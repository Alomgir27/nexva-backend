from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import time
from typing import List, Dict, Optional
from datetime import datetime
import search
import models
import tempfile
import os
import re
from pydub import AudioSegment
from transcription_service import transcribe_audio_file
import yt_dlp

class WebScraper:
    def __init__(self, max_pages: int = 1000):
        self.max_pages = max_pages
        self.visited = set()
        self.failed_attempts = {}
        self.max_retries = 3
        
    def _get_driver(self):
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        options.page_load_strategy = 'normal'
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(30)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    
    def _normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip('/')
    
    def _is_same_domain(self, url: str, base_domain: str) -> bool:
        return urlparse(url).netloc == urlparse(base_domain).netloc
    
    def _extract_content(self, soup: BeautifulSoup) -> Dict[str, str]:
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()
        
        title = soup.find('title')
        title_text = title.get_text(strip=True) if title else ""
        
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        text = main_content.get_text(separator=' ', strip=True) if main_content else ""
        
        return {
            'title': title_text,
            'content': text[:50000]
        }
    
    def _chunk_text(self, text: str, chunk_size: int = 512) -> List[str]:
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            current_size += len(word) + 1
            if current_size > chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_size = len(word)
            else:
                current_chunk.append(word)
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _extract_youtube_url(self, url: str) -> Optional[str]:
        """Extract YouTube video ID and return full URL"""
        youtube_patterns = [
            r'(?:youtube(?:-nocookie)?\.com\/watch\?v=|youtu\.be\/|youtube(?:-nocookie)?\.com\/embed\/)([^&\n?#]+)',
            r'youtube(?:-nocookie)?\.com\/.*[?&]v=([^&\n?#]+)'
        ]
        
        for pattern in youtube_patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                return f"https://www.youtube.com/watch?v={video_id}"
        
        return None
    
    def _extract_vimeo_url(self, url: str) -> Optional[str]:
        """Extract Vimeo video ID and return full URL"""
        vimeo_pattern = r'vimeo\.com\/(?:video\/)?(\d+)'
        match = re.search(vimeo_pattern, url)
        if match:
            video_id = match.group(1)
            return f"https://vimeo.com/{video_id}"
        return None
    
    def _extract_media_urls(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract audio and video URLs from page including YouTube/Vimeo"""
        media_files = []
        seen_urls = set()
        supported_formats = ['.mp3', '.mp4', '.webm', '.wav', '.ogg', '.m4a', '.avi', '.mov', '.flv']
        
        # Find audio tags
        for audio in soup.find_all('audio'):
            src = audio.get('src')
            if src:
                full_url = urljoin(base_url, src)
                if any(full_url.lower().endswith(fmt) for fmt in supported_formats) and full_url not in seen_urls:
                    media_files.append({'type': 'audio', 'url': full_url})
                    seen_urls.add(full_url)
            
            for source in audio.find_all('source'):
                src = source.get('src')
                if src:
                    full_url = urljoin(base_url, src)
                    if any(full_url.lower().endswith(fmt) for fmt in supported_formats) and full_url not in seen_urls:
                        media_files.append({'type': 'audio', 'url': full_url})
                        seen_urls.add(full_url)
        
        # Find video tags
        for video in soup.find_all('video'):
            src = video.get('src')
            if src:
                full_url = urljoin(base_url, src)
                if any(full_url.lower().endswith(fmt) for fmt in supported_formats) and full_url not in seen_urls:
                    media_files.append({'type': 'video', 'url': full_url})
                    seen_urls.add(full_url)
            
            for source in video.find_all('source'):
                src = source.get('src')
                if src:
                    full_url = urljoin(base_url, src)
                    if any(full_url.lower().endswith(fmt) for fmt in supported_formats) and full_url not in seen_urls:
                        media_files.append({'type': 'video', 'url': full_url})
                        seen_urls.add(full_url)
        
        # Find YouTube/Vimeo embeds in iframes
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src') or iframe.get('data-src')
            if src:
                youtube_url = self._extract_youtube_url(src)
                if youtube_url and youtube_url not in seen_urls:
                    media_files.append({'type': 'youtube', 'url': youtube_url})
                    seen_urls.add(youtube_url)
                    continue
                
                vimeo_url = self._extract_vimeo_url(src)
                if vimeo_url and vimeo_url not in seen_urls:
                    media_files.append({'type': 'vimeo', 'url': vimeo_url})
                    seen_urls.add(vimeo_url)
        
        # Find direct video/audio links in data attributes
        for elem in soup.find_all(attrs={'data-src': True}):
            src = elem.get('data-src')
            if src and any(src.lower().endswith(fmt) for fmt in supported_formats):
                full_url = urljoin(base_url, src)
                if full_url not in seen_urls:
                    media_type = 'audio' if any(src.lower().endswith(fmt) for fmt in ['.mp3', '.wav', '.ogg', '.m4a']) else 'video'
                    media_files.append({'type': media_type, 'url': full_url})
                    seen_urls.add(full_url)
        
        # Limit to 3 media files per page
        return media_files[:3]
    
    def _process_media_file(self, media_url: str, media_type: str) -> Optional[Dict]:
        """Download media using yt-dlp, extract audio, and transcribe"""
        temp_audio = None
        
        try:
            print(f"🎵 Processing {media_type}: {media_url}")
            
            # Use yt-dlp for all media downloads (supports YouTube, Vimeo, and direct files)
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(tempfile.gettempdir(), '%(id)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
                'postprocessor_args': [
                    '-ar', '16000',  # 16kHz sample rate
                    '-ac', '1',      # Mono
                ],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(media_url, download=True)
                
                # Get the output filename
                if 'id' in info:
                    video_id = info['id']
                else:
                    video_id = os.path.splitext(os.path.basename(urlparse(media_url).path))[0]
                
                temp_audio = os.path.join(tempfile.gettempdir(), f"{video_id}.wav")
                
                # Check if wav was created, otherwise find the downloaded file
                if not os.path.exists(temp_audio):
                    # Try to find any file with the video_id
                    temp_dir = tempfile.gettempdir()
                    for file in os.listdir(temp_dir):
                        if file.startswith(video_id):
                            temp_file = os.path.join(temp_dir, file)
                            # Convert to wav if needed
                            if not file.endswith('.wav'):
                                audio = AudioSegment.from_file(temp_file)
                                audio = audio.set_channels(1).set_frame_rate(16000)
                                temp_audio = os.path.join(temp_dir, f"{video_id}_converted.wav")
                                audio.export(temp_audio, format="wav")
                                os.unlink(temp_file)
                            else:
                                temp_audio = temp_file
                            break
                
                if not os.path.exists(temp_audio):
                    print(f"⚠️ Could not find audio file for {media_url}")
                    return None
                
                # Transcribe the audio
                transcription = transcribe_audio_file(temp_audio, language=None)
                
                if transcription:
                    return {
                        'url': media_url,
                        'type': media_type,
                        'transcription': transcription,
                        'title': info.get('title', os.path.basename(media_url)),
                        'duration': info.get('duration', 0)
                    }
                
                return None
        
        except Exception as e:
            print(f"❌ Media processing error for {media_url}: {e}")
            return None
        
        finally:
            # Clean up temporary files
            if temp_audio and os.path.exists(temp_audio):
                try:
                    os.unlink(temp_audio)
                except:
                    pass
            
            # Clean up any remaining temp files for this media
            try:
                temp_dir = tempfile.gettempdir()
                parsed = urlparse(media_url)
                basename = os.path.splitext(os.path.basename(parsed.path))[0]
                for file in os.listdir(temp_dir):
                    if basename and basename in file:
                        try:
                            os.unlink(os.path.join(temp_dir, file))
                        except:
                            pass
            except:
                pass
    
    def scrape_domain(self, start_url: str, domain_id: int, db) -> List[models.ScrapedPage]:
        driver = self._get_driver()
        to_visit = [start_url]
        scraped_pages = []
        base_domain = urlparse(start_url).netloc
        
        domain = db.query(models.Domain).filter(models.Domain.id == domain_id).first()
        chatbot_id = domain.chatbot_id
        
        max_iterations = self.max_pages * 3
        iteration_count = 0
        consecutive_failures = 0
        max_consecutive_failures = 10
        
        try:
            while to_visit and len(scraped_pages) < self.max_pages and iteration_count < max_iterations:
                iteration_count += 1
                
                if consecutive_failures >= max_consecutive_failures:
                    print(f"Too many consecutive failures ({consecutive_failures}), stopping scraping")
                    break
                
                if len(to_visit) > 1000:
                    print(f"Too many URLs in queue ({len(to_visit)}), limiting to 1000")
                    to_visit = to_visit[:1000]
                
                url = to_visit.pop(0)
                normalized_url = self._normalize_url(url)
                
                if normalized_url in self.visited:
                    continue
                
                if self.failed_attempts.get(normalized_url, 0) >= self.max_retries:
                    continue
                
                self.visited.add(normalized_url)
                
                try:
                    driver.get(url)
                    time.sleep(2)
                    
                    # Check if blocked by anti-bot (more specific detection)
                    page_title = driver.title.lower()
                    page_source_sample = driver.page_source.lower()[:2000]
                    
                    # Only flag as blocked if we see clear blocking indicators
                    blocking_patterns = [
                        ('access denied', 'forbidden'),
                        ('cloudflare', 'checking your browser'),
                        ('please complete the security check', 'captcha'),
                        ('blocked', 'firewall'),
                        ('attention required', 'cloudflare'),
                    ]
                    
                    is_blocked = any(
                        all(keyword in page_source_sample for keyword in pattern)
                        for pattern in blocking_patterns
                    )
                    
                    if is_blocked:
                        print(f"⚠️ Site blocking detected at {url} - skipping")
                        consecutive_failures += 1
                        self.failed_attempts[normalized_url] = self.max_retries
                        continue
                    
                    soup = BeautifulSoup(driver.page_source, 'lxml')
                    content_data = self._extract_content(soup)
                    
                    # Extract media URLs
                    media_files = self._extract_media_urls(soup, url)
                    media_urls = [m['url'] for m in media_files]
                    media_transcriptions = []
                    
                    # Process media files and transcribe
                    for media in media_files:
                        result = self._process_media_file(media['url'], media['type'])
                        if result:
                            media_transcriptions.append(result)
                            # Append transcription to content
                            content_data['content'] += f"\n\n[{media['type'].upper()} TRANSCRIPTION from {result['url']}]: {result['transcription']}"
                    
                    if content_data['content']:
                        word_count = len(content_data['content'].split())
                        content_preview = content_data['content'][:200] + "..." if len(content_data['content']) > 200 else content_data['content']
                        
                        tags = search.generate_content_tags(content_data['title'], content_data['content'])
                        
                        scraped_page = models.ScrapedPage(
                            domain_id=domain_id,
                            url=normalized_url,
                            title=content_data['title'],
                            content=content_data['content'],
                            content_preview=content_preview,
                            word_count=word_count,
                            media_urls=media_urls,
                            media_transcriptions=media_transcriptions,
                            tags=tags,
                            last_updated=datetime.utcnow()
                        )
                        db.add(scraped_page)
                        db.commit()
                        scraped_pages.append(scraped_page)
                        
                        # Update domain pages count in real-time
                        domain.pages_scraped = len(scraped_pages)
                        db.commit()
                        
                        consecutive_failures = 0
                        print(f"✅ Scraped: {normalized_url} ({len(scraped_pages)}/{self.max_pages})")
                        
                        chunks = self._chunk_text(content_data['content'])
                        tags = search.generate_content_tags(content_data['title'], content_data['content'])
                        
                        for idx, chunk in enumerate(chunks):
                            doc = {
                                'url': normalized_url,
                                'title': content_data['title'],
                                'content': chunk,
                                'chunk_index': idx,
                                'chatbot_id': chatbot_id,
                                'domain_id': domain_id,
                                'tags': tags
                            }
                            search.index_chatbot_content(chatbot_id, doc)
                        
                        # Index media transcriptions separately with metadata
                        for media_trans in media_transcriptions:
                            media_tags = search.generate_content_tags(
                                f"{content_data['title']} - {media_trans['type']}", 
                                media_trans['transcription']
                            )
                            media_doc = {
                                'url': normalized_url,
                                'title': f"{content_data['title']} - {media_trans['type'].upper()}",
                                'content': media_trans['transcription'],
                                'chunk_index': 0,
                                'chatbot_id': chatbot_id,
                                'domain_id': domain_id,
                                'media_type': media_trans['type'],
                                'media_url': media_trans['url'],
                                'tags': media_tags
                            }
                            search.index_chatbot_content(chatbot_id, media_doc)
                    
                    links = soup.find_all('a', href=True)
                    unique_links = set()
                    
                    for link in links[:100]:
                        href = link['href']
                        full_url = urljoin(url, href)
                        
                        if self._is_same_domain(full_url, start_url):
                            normalized_link = self._normalize_url(full_url)
                            if (normalized_link not in self.visited and 
                                normalized_link not in unique_links and
                                normalized_link not in to_visit):
                                unique_links.add(normalized_link)
                    
                    to_visit.extend(list(unique_links)[:50])
                
                except Exception as e:
                    error_msg = str(e).lower()
                    print(f"❌ Error scraping {url}: {e}")
                    
                    # Check if it's a blocking/timeout error
                    if any(keyword in error_msg for keyword in ['timeout', 'refused', 'unreachable', '403', '429']):
                        print(f"⚠️ Site appears to be blocking requests")
                        consecutive_failures += 1
                    
                    self.failed_attempts[normalized_url] = self.failed_attempts.get(normalized_url, 0) + 1
                    consecutive_failures += 1
                    continue
        
        finally:
            driver.quit()
        
        return scraped_pages

