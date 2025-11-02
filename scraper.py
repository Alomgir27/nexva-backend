from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from typing import List, Dict, Optional
from datetime import datetime
import search
import models
import tempfile
import os
import re
import gc
from threading import Lock
from pydub import AudioSegment
from transcription_service import transcribe_audio_file
import yt_dlp
import socket

_DRIVER_PATH = os.environ.get("CHROMEDRIVER_PATH")
_DRIVER_PATH_LOCK = Lock()
_PORT_LOCK = Lock()
_USED_PORTS = set()


class WebScraper:
    def __init__(self, max_pages: int = 1000, process_media: Optional[bool] = None):
        self.max_pages = max_pages
        self.visited = set()
        self.failed_attempts = {}
        self.max_retries = 3
        self.driver = None
        self._driver_options = None
        if process_media is None:
            self.process_media = os.getenv("ENABLE_MEDIA_SCRAPE", "false").lower() == "true"
        else:
            self.process_media = process_media
        
    def _get_free_port(self):
        """Get a free port for Chrome remote debugging"""
        with _PORT_LOCK:
            for port in range(9222, 9322):
                if port not in _USED_PORTS:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    try:
                        sock.bind(('127.0.0.1', port))
                        sock.close()
                        _USED_PORTS.add(port)
                        return port
                    except OSError:
                        continue
            return None
    
    def _release_port(self, port):
        """Release port when driver closes"""
        with _PORT_LOCK:
            _USED_PORTS.discard(port)
    
    def _get_driver(self):
        if self.driver:
            return self.driver
        
        print(f"🔧 Initializing Chrome WebDriver...")
        try:
            if not self._driver_options:
                port = self._get_free_port()
                if not port:
                    raise Exception("No free ports available for Chrome")
                
                self._remote_debugging_port = port
                options = Options()
                options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_argument('--disable-extensions')
                options.add_argument('--disable-logging')
                options.add_argument('--log-level=3')
                options.add_argument('--disable-software-rasterizer')
                options.add_argument('--disable-images')
                options.add_argument('--blink-settings=imagesEnabled=false')
                options.add_argument(f'--remote-debugging-port={port}')
                options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                options.page_load_strategy = 'normal'
                self._driver_options = options

            global _DRIVER_PATH
            if not _DRIVER_PATH:
                with _DRIVER_PATH_LOCK:
                    if not _DRIVER_PATH:
                        print("📦 Installing ChromeDriver...")
                        _DRIVER_PATH = ChromeDriverManager().install()

            if not os.path.exists(_DRIVER_PATH):
                raise FileNotFoundError(f"ChromeDriver not found at {_DRIVER_PATH}")

            service = Service(_DRIVER_PATH)

            print(f"🚀 Starting Chrome browser on port {self._remote_debugging_port}...")
            self.driver = webdriver.Chrome(service=service, options=self._driver_options)
            self.driver.set_page_load_timeout(15)
            self.driver.set_script_timeout(10)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print(f"✅ Chrome WebDriver ready on port {self._remote_debugging_port}")
            return self.driver
        except Exception as e:
            if hasattr(self, '_remote_debugging_port'):
                self._release_port(self._remote_debugging_port)
            print(f"❌ Failed to initialize Chrome WebDriver: {e}")
            raise
    
    def _cleanup_driver(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            finally:
                self.driver = None
                if hasattr(self, '_remote_debugging_port'):
                    self._release_port(self._remote_debugging_port)
        
        try:
            import subprocess
            subprocess.run(['pkill', '-9', '-f', 'chrome.*--headless'], capture_output=True, timeout=3)
            time.sleep(1)
        except:
            pass

    def _restart_driver(self):
        self._cleanup_driver()
        return self._get_driver()
    
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
        """Extract video URLs including YouTube/Vimeo and custom players"""
        media_files = []
        seen_urls = set()
        video_formats = ['.mp4', '.webm', '.avi', '.mov', '.flv', '.m3u8']
        
        # Find standard video tags
        for video in soup.find_all('video'):
            for attr in ['src', 'data-src', 'data-video-src', 'data-url']:
                src = video.get(attr)
                if src:
                    full_url = urljoin(base_url, src)
                    if any(full_url.lower().endswith(fmt) for fmt in video_formats) and full_url not in seen_urls:
                        media_files.append({'type': 'video', 'url': full_url})
                        seen_urls.add(full_url)
            
            for source in video.find_all('source'):
                for attr in ['src', 'data-src']:
                    src = source.get(attr)
                    if src:
                        full_url = urljoin(base_url, src)
                        if any(full_url.lower().endswith(fmt) for fmt in video_formats) and full_url not in seen_urls:
                            media_files.append({'type': 'video', 'url': full_url})
                            seen_urls.add(full_url)
        
        # Find YouTube/Vimeo embeds in iframes
        for iframe in soup.find_all('iframe'):
            for attr in ['src', 'data-src', 'data-lazy-src']:
                src = iframe.get(attr)
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
        
        # Find videos in data attributes and custom players
        for attr_name in ['data-src', 'data-video-url', 'data-video-src', 'data-background-video']:
            for elem in soup.find_all(attrs={attr_name: True}):
                src = elem.get(attr_name)
                if src and any(src.lower().endswith(fmt) for fmt in video_formats):
                    full_url = urljoin(base_url, src)
                    if full_url not in seen_urls:
                        media_files.append({'type': 'video', 'url': full_url})
                        seen_urls.add(full_url)
        
        # Check for video URLs in script tags (JSON data)
        for script in soup.find_all('script', type='application/json'):
            script_content = script.string
            if script_content:
                for fmt in video_formats:
                    pattern = rf'(https?://[^\s"\'<>]+{fmt})'
                    matches = re.findall(pattern, script_content, re.IGNORECASE)
                    for match in matches:
                        if match not in seen_urls:
                            media_files.append({'type': 'video', 'url': match})
                            seen_urls.add(match)
        
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
                
                # Get audio duration
                audio = AudioSegment.from_file(temp_audio)
                duration_seconds = len(audio) / 1000.0
                
                # Transcribe in chunks if longer than 3 minutes
                chunk_duration = 180000  # 3 minutes in milliseconds
                transcriptions = []
                
                if duration_seconds > 180:  # Longer than 3 minutes
                    print(f"📊 Audio is {duration_seconds:.1f}s, splitting into chunks...")
                    num_chunks = int(duration_seconds / 180) + 1
                    
                    for i in range(num_chunks):
                        start_ms = i * chunk_duration
                        end_ms = min((i + 1) * chunk_duration, len(audio))
                        
                        chunk = audio[start_ms:end_ms]
                        chunk_file = os.path.join(tempfile.gettempdir(), f"{video_id}_chunk_{i}.wav")
                        
                        try:
                            chunk.export(chunk_file, format="wav")
                            chunk_text = transcribe_audio_file(chunk_file, language=None)
                            if chunk_text:
                                transcriptions.append(chunk_text)
                                print(f"✅ Chunk {i+1}/{num_chunks} transcribed")
                        except Exception as chunk_error:
                            print(f"⚠️ Chunk {i+1} failed: {chunk_error}")
                        finally:
                            if os.path.exists(chunk_file):
                                os.unlink(chunk_file)
                    
                    transcription = " ".join(transcriptions)
                else:
                    # Short audio, transcribe directly
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
        pages_batch = []
        base_domain = urlparse(start_url).netloc
        pages_since_driver_refresh = 0
        
        domain = db.query(models.Domain).filter(models.Domain.id == domain_id).first()
        chatbot_id = domain.chatbot_id
        
        max_iterations = self.max_pages * 3
        iteration_count = 0
        consecutive_failures = 0
        max_consecutive_failures = 10
        landing_page_url = self._normalize_url(start_url)
        
        try:
            while to_visit and len(scraped_pages) < self.max_pages and iteration_count < max_iterations:
                iteration_count += 1
                
                if consecutive_failures >= max_consecutive_failures:
                    print(f"Too many consecutive failures ({consecutive_failures}), stopping scraping")
                    break
                
                if len(to_visit) > 1000:
                    to_visit = to_visit[:1000]
                
                url = to_visit.pop(0)
                normalized_url = self._normalize_url(url)
                
                if normalized_url in self.visited:
                    continue
                
                if self.failed_attempts.get(normalized_url, 0) >= self.max_retries:
                    continue
                
                self.visited.add(normalized_url)
                
                try:
                    try:
                        driver.get(url)
                        time.sleep(0.5)
                    except Exception as load_error:
                        error_str = str(load_error).lower()
                        if any(keyword in error_str for keyword in ['invalid session', 'disconnected', 'renderer', 'devtools']):
                            print(f"⚠️ Driver crashed on {url}, restarting...")
                            try:
                                self._cleanup_driver()
                                driver = self._get_driver()
                                pages_since_driver_refresh = 0
                                driver.get(url)
                                time.sleep(0.5)
                            except:
                                print(f"⚠️ Driver restart failed for {url}, skipping...")
                                consecutive_failures += 1
                                continue
                        elif 'timeout' in error_str:
                            print(f"⏱️ Timeout on {url}, skipping...")
                            consecutive_failures += 1
                            continue
                        else:
                            raise
                    
                    try:
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                        time.sleep(0.3)
                        driver.execute_script("window.scrollTo(0, 0);")
                        time.sleep(0.5)  # Wait for lazy-loaded videos
                    except:
                        pass
                    
                    page_source = driver.page_source
                    page_title = driver.title.lower()
                    page_source_sample = page_source.lower()[:2000]
                    
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
                    
                    soup = BeautifulSoup(page_source, 'lxml')
                    content_data = self._extract_content(soup)
                    
                    media_urls = []
                    media_transcriptions = []

                    if self.process_media and normalized_url == landing_page_url:
                        media_files = self._extract_media_urls(soup, url)
                        if media_files:
                            print(f"🎬 Found {len(media_files)} media file(s) on landing page: {url}")
                        media_urls = [m['url'] for m in media_files]

                        for idx, media in enumerate(media_files, 1):
                            print(f"📥 Processing media {idx}/{len(media_files)}: {media['type']}")
                            result = self._process_media_file(media['url'], media['type'])
                            if result:
                                media_transcriptions.append(result)
                                content_data['content'] += f"\n\n[{media['type'].upper()} TRANSCRIPTION from {result['url']}]: {result['transcription']}"
                            print(f"✅ Media {idx}/{len(media_files)} done, cleaned up")
                            gc.collect()
                    
                    links = soup.find_all('a', href=True)[:100]
                    
                    del soup, page_source
                    gc.collect()
                    
                    if content_data['content']:
                        word_count = len(content_data['content'].split())
                        content_preview = content_data['content'][:200] + "..." if len(content_data['content']) > 200 else content_data['content']
                        
                        scraped_page = models.ScrapedPage(
                            domain_id=domain_id,
                            url=normalized_url,
                            title=content_data['title'],
                            content=content_data['content'],
                            content_preview=content_preview,
                            word_count=word_count,
                            media_urls=media_urls,
                            media_transcriptions=media_transcriptions,
                            tags=[],
                            last_updated=datetime.utcnow()
                        )
                        db.add(scraped_page)
                        scraped_pages.append(scraped_page)
                        pages_batch.append((scraped_page, content_data, media_transcriptions))
                        
                        if len(scraped_pages) % 5 == 0:
                            domain.pages_scraped = len(scraped_pages)
                            db.commit()
                        
                        consecutive_failures = 0
                        pages_since_driver_refresh += 1
                        print(f"✅ Scraped: {normalized_url} ({len(scraped_pages)}/{self.max_pages})")
                        
                        if len(pages_batch) >= 5:
                            self._batch_index_pages(pages_batch, chatbot_id, domain_id)
                            pages_batch.clear()
                            gc.collect()
                        
                        unique_links = set()
                        
                        for link in links:
                            href = link.get('href', '')
                            if not href:
                                continue
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
                    
                    if any(keyword in error_msg for keyword in ['invalid session', 'disconnected', 'devtools', 'renderer']):
                        print(f"🔄 Driver crashed, attempting restart...")
                        consecutive_failures += 1
                        
                        if consecutive_failures < max_consecutive_failures:
                            try:
                                self._cleanup_driver()
                                time.sleep(3)
                                driver = self._get_driver()
                                pages_since_driver_refresh = 0
                                time.sleep(1)
                                to_visit.insert(0, url)
                                self.visited.discard(normalized_url)
                                consecutive_failures = 0
                                continue
                            except Exception as restart_error:
                                print(f"❌ Failed to restart driver: {restart_error}")
                                consecutive_failures += 1
                    else:
                        consecutive_failures += 1
                    
                    self.failed_attempts[normalized_url] = self.failed_attempts.get(normalized_url, 0) + 1
                    continue
        
        finally:
            if pages_batch:
                self._batch_index_pages(pages_batch, chatbot_id, domain_id)
            
            if scraped_pages:
                domain.pages_scraped = len(scraped_pages)
                db.commit()
            
            self._cleanup_driver()
            gc.collect()
        
        return scraped_pages
    
    def _batch_index_pages(self, pages_batch: List, chatbot_id: int, domain_id: int):
        """Batch process and index multiple pages together"""
        try:
            for scraped_page, content_data, media_transcriptions in pages_batch:
                tags = search.generate_content_tags(content_data['title'], content_data['content'])
                scraped_page.tags = tags
                
                chunks = self._chunk_text(content_data['content'])
                
                for idx, chunk in enumerate(chunks):
                    doc = {
                        'url': scraped_page.url,
                        'title': content_data['title'],
                        'content': chunk,
                        'chunk_index': idx,
                        'chatbot_id': chatbot_id,
                        'domain_id': domain_id,
                        'tags': tags
                    }
                    search.index_chatbot_content(chatbot_id, doc)
                
                for media_trans in media_transcriptions:
                    media_tags = search.generate_content_tags(
                        f"{content_data['title']} - {media_trans['type']}", 
                        media_trans['transcription']
                    )
                    media_doc = {
                        'url': scraped_page.url,
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
        except Exception as e:
            print(f"⚠️ Batch indexing error: {e}")

