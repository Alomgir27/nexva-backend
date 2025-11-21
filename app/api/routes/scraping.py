from datetime import datetime
from app import database

def run_domain_scraping(job_id: int, domain_id: int, start_url: str):
    print(f"🚀 Starting scraping background task: job_id={job_id}, domain_id={domain_id}, url={start_url}")
    from app.services.scraper import WebScraper
    db = database.SessionLocal()
    try:
        job = db.query(database.ScrapeJob).filter(database.ScrapeJob.id == job_id).first()
        domain = db.query(database.Domain).filter(database.Domain.id == domain_id).first()
        
        if not job or not domain:
            print(f"❌ Job or domain not found: job_id={job_id}, domain_id={domain_id}")
            return
        
        print(f"📋 Starting scraping for: {start_url}")
        job.status = "running"
        domain.status = "scraping"
        db.commit()
        
        web_scraper = WebScraper()
        pages = web_scraper.scrape_domain(start_url, domain_id, db)
        
        db.refresh(domain)
        
        job.status = "completed"
        job.pages_scraped = len(pages)
        job.total_pages = len(pages)
        job.completed_at = datetime.utcnow()
        
        domain.status = "completed"
        domain.pages_scraped = len(pages)
        domain.last_scraped_at = datetime.utcnow()
        
        db.commit()
        print(f"✅ Scraping completed: {len(pages)} pages scraped from {start_url}")
    except Exception as e:
        print(f"Scraping error for domain {domain_id}: {e}")
        if job:
            job.status = "failed"
            job.error = str(e)
        if domain:
            domain.status = "failed"
        db.commit()
    finally:
        db.close()

