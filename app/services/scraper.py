from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import random
import threading
try:
    import undetected_chromedriver as uc
except ImportError:
    uc = None
# uc = None # Force standard selenium for speed
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import time
from typing import List, Dict, Optional
from datetime import datetime
from app.services import search
from app import database
import tempfile
import os
import re
from pydub import AudioSegment
from app.services.transcription_service import transcribe_audio_file
import yt_dlp

class WebScraper:
    def __init__(self, max_pages: int = 1000):
        self.max_pages = max_pages
        self.visited = set()
        self.failed_attempts = {}
        self.max_retries = 3
        
    # Global lock for driver initialization to prevent parallel patching/downloads
    _driver_lock = threading.Lock()

    def _get_driver(self):
        user_agent = random.choice([
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        ])

        content_block_prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.stylesheets": 2,
            "profile.managed_default_content_settings.fonts": 2,
            "profile.managed_default_content_settings.plugins": 2,
            "profile.managed_default_content_settings.popups": 2,
            "profile.managed_default_content_settings.media_stream": 2,
            "profile.managed_default_content_settings.media_stream_mic": 2,
            "profile.managed_default_content_settings.media_stream_camera": 2,
            "profile.managed_default_content_settings.geolocation": 2,
            "profile.managed_default_content_settings.notifications": 2,
        }

        blocked_resource_patterns = [
            "*.css", "*.jpg", "*.jpeg", "*.png", "*.gif", "*.svg",
            "*.woff", "*.woff2", "*.ttf", "*.otf", "*.ico",
            "*.mp4", "*.webm", "*.mp3", "*.wav"
        ]

        def apply_shared_options(opts):
            opts.add_argument('--headless=new')
            opts.add_argument('--no-sandbox')
            opts.add_argument('--disable-dev-shm-usage')
            opts.add_argument('--disable-gpu')
            opts.add_argument('--disable-blink-features=AutomationControlled')
            opts.add_argument('--disable-extensions')
            opts.add_argument('--disable-infobars')
            opts.add_argument('--disable-web-security')
            opts.add_argument('--allow-running-insecure-content')
            opts.add_argument('--blink-settings=imagesEnabled=false')
            opts.add_argument(f'--user-agent={user_agent}')
            opts.page_load_strategy = 'normal'
            opts.add_experimental_option("prefs", content_block_prefs)

        # Use lock to ensure sequential initialization
        with self._driver_lock:
            driver = None
            
            if uc:
                print("   - Using undetected_chromedriver")
                options = uc.ChromeOptions()
                apply_shared_options(options)
                
                # Try to find Chrome binary in common locations
                chrome_paths = [
                    '/usr/bin/google-chrome',
                    '/usr/bin/google-chrome-stable',
                    '/usr/bin/chromium-browser',
                    '/usr/bin/chromium'
                ]
                chrome_binary = None
                for path in chrome_paths:
                    if os.path.exists(path):
                        chrome_binary = path
                        break
                
                if chrome_binary:
                    options.binary_location = chrome_binary
                    print(f"   - Chrome binary: {chrome_binary}")
                
                import time
                start_time = time.time()
                print(f"   - 🕒 Starting uc.Chrome at {start_time}")
                
                try:
                    driver = uc.Chrome(options=options, use_subprocess=True)
                    print(f"   - ✅ uc.Chrome started in {time.time() - start_time:.2f}s")
                except Exception as e:
                    print(f"   - ❌ uc.Chrome failed: {e}")
                    print("   - 🔄 Falling back to standard selenium...")
                    driver = None  # Ensure we fall through to standard selenium
            
            # Fallback to standard selenium if uc failed or not available
            if driver is None:
                print("   - Using standard selenium webdriver")
                options = Options()
                apply_shared_options(options)
                
                print("   - Checking/Installing Chrome driver...")
                driver_path = ChromeDriverManager().install()
                print(f"   - Driver path: {driver_path}")
                
                service = Service(driver_path)
                driver = webdriver.Chrome(service=service, options=options)

        driver.set_script_timeout(60)
        driver.implicitly_wait(10)

        try:
            driver.execute_cdp_cmd('Network.enable', {})
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": user_agent})
            driver.execute_cdp_cmd('Network.setBlockedURLs', {"urls": blocked_resource_patterns})
        except Exception:
            pass

        try:
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception:
            pass

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
    
    def _chunk_text(self, text: str, chunk_size: int = 1000) -> List[str]:
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
    
    def scrape_domain(self, start_url: str, domain_id: int, db) -> List[database.ScrapedPage]:
        # Initialize variables
        to_visit = [start_url]
        scraped_pages = []
        base_domain = urlparse(start_url).netloc
        driver = None  # Initialize driver to None
        
        domain = db.query(database.Domain).filter(database.Domain.id == domain_id).first()
        chatbot_id = domain.chatbot_id
        
        max_iterations = self.max_pages * 3
        iteration_count = 0
        consecutive_failures = 0
        max_consecutive_failures = 10

        try:
            print("🚗 Initializing Chrome driver...")
            driver = self._get_driver()
            print("✅ Driver initialized")
            
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
                    print(f"🌐 Navigating to: {url}")
                    driver.get(url)
                    print(f"⏳ Waiting for page load: {url}")
                    time.sleep(2)
                    print(f"📄 Page loaded: {driver.title}")
                    
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
                    
                    if content_data['content']:
                        word_count = len(content_data['content'].split())
                        content_preview = content_data['content'][:200] + "..." if len(content_data['content']) > 200 else content_data['content']
                        
                        tags = search.generate_content_tags(content_data['title'], content_data['content'])
                        
                        scraped_page = database.ScrapedPage(
                            domain_id=domain_id,
                            url=normalized_url,
                            title=content_data['title'],
                            content=content_data['content'],
                            content_preview=content_preview,
                            word_count=word_count,
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
        
        except Exception as e:
            print(f"❌ Driver initialization failed: {e}")
        
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
        
        return scraped_pages


