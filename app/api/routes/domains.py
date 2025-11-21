from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime
from uuid import uuid4
import os

from app import database, schemas
from app.services import auth
from app.core.config import settings

router = APIRouter()

DOCUMENT_STORAGE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads", "documents")
)
os.makedirs(DOCUMENT_STORAGE_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain"
}

def _get_domain_with_auth(domain_id: int, current_user: database.User, db: Session):
    domain = db.query(database.Domain).filter(database.Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    chatbot = db.query(database.Chatbot).filter(
        database.Chatbot.id == domain.chatbot_id,
        database.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Not authorized")
    
    return domain, chatbot

@router.post("", response_model=schemas.DomainResponse)
async def create_domain(
    domain_data: schemas.DomainCreate,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    chatbot = db.query(database.Chatbot).filter(
        database.Chatbot.id == domain_data.chatbot_id,
        database.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    
    domain = database.Domain(chatbot_id=domain_data.chatbot_id, url=domain_data.url, status="scraping")
    db.add(domain)
    db.commit()
    db.refresh(domain)
    
    job = database.ScrapeJob(domain_id=domain.id, status="pending")
    db.add(job)
    db.commit()
    db.refresh(job)
    
    print(f"🔍 Created scrape job {job.id} for domain {domain.id} ({domain_data.url})")
    
    # Run scraping in a separate thread to avoid blocking the main event loop
    import threading
    from app.api.routes.scraping import run_domain_scraping
    
    thread = threading.Thread(
        target=run_domain_scraping,
        args=(job.id, domain.id, domain_data.url),
        daemon=True
    )
    thread.start()
    print(f"✅ Scraping thread started for job {job.id}")
    
    return domain

@router.get("/{chatbot_id}", response_model=List[schemas.DomainResponse])
def list_domains(
    chatbot_id: int,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    chatbot = db.query(database.Chatbot).filter(
        database.Chatbot.id == chatbot_id,
        database.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    
    domains = db.query(database.Domain).filter(database.Domain.chatbot_id == chatbot_id).all()
    return domains

@router.get("/{domain_id}/pages", response_model=Dict)
def list_scraped_pages(
    domain_id: int,
    page: int = 1,
    per_page: int = 10,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    domain = db.query(database.Domain).filter(database.Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    chatbot = db.query(database.Chatbot).filter(
        database.Chatbot.id == domain.chatbot_id,
        database.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Not authorized")
    
    offset = (page - 1) * per_page
    pages = db.query(database.ScrapedPage).filter(
        database.ScrapedPage.domain_id == domain_id
    ).offset(offset).limit(per_page).all()
    
    total = db.query(database.ScrapedPage).filter(database.ScrapedPage.domain_id == domain_id).count()
    
    pages_data = [{
        "id": p.id,
        "url": p.url,
        "title": p.title,
        "content": p.content,
        "content_preview": p.content_preview,
        "word_count": p.word_count,
        "tags": p.tags if p.tags else [],
        "last_updated": p.last_updated.isoformat() if p.last_updated else None,
        "created_at": p.created_at.isoformat() if p.created_at else None
    } for p in pages]
    
    return {
        "pages": pages_data,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }

@router.get("/{domain_id}/documents", response_model=List[schemas.DocumentResponse])
def list_documents(
    domain_id: int,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    domain, chatbot = _get_domain_with_auth(domain_id, current_user, db)
    documents = db.query(database.Document).filter(
        database.Document.domain_id == domain.id
    ).order_by(database.Document.created_at.desc()).all()
    return documents

@router.post("/{domain_id}/documents", response_model=schemas.DocumentResponse)
async def upload_document(
    domain_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    domain, chatbot = _get_domain_with_auth(domain_id, current_user, db)
    
    original_filename = file.filename or "document"
    extension = os.path.splitext(original_filename)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported content type")
    
    unique_name = f"{uuid4().hex}{extension}"
    
    if settings.USE_R2_STORAGE:
        try:
            from app.services.r2_storage import get_r2_client
            r2_client = get_r2_client()
            
            object_key = f"documents/{chatbot.id}/{domain.id}/{unique_name}"
            file_url = r2_client.upload_file(file.file, object_key, file.content_type)
            
            size = 0
            file.file.seek(0)
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
            
            document = database.Document(
                chatbot_id=chatbot.id,
                domain_id=domain.id,
                file_name=original_filename,
                file_path=file_url,
                mime_type=file.content_type,
                file_size=size,
                status="uploaded"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"R2 upload failed: {str(e)}")
    else:
        domain_dir = os.path.join(DOCUMENT_STORAGE_DIR, str(chatbot.id), str(domain.id))
        os.makedirs(domain_dir, exist_ok=True)
        file_path = os.path.join(domain_dir, unique_name)
        
        size = 0
        with open(file_path, "wb") as buffer:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                buffer.write(chunk)
        
        document = database.Document(
            chatbot_id=chatbot.id,
            domain_id=domain.id,
            file_name=original_filename,
            file_path=file_path,
            mime_type=file.content_type,
            file_size=size,
            status="uploaded"
        )
    
    await file.close()
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    background_tasks.add_task(process_and_index_document, document.id, chatbot.id, domain.id, original_filename, db)
    
    return document

def process_and_index_document(document_id: int, chatbot_id: int, domain_id: int, original_filename: str, db: Session):
    # Re-query to get fresh object in new thread context if needed, or pass IDs
    # For simplicity in this context, we'll use a new session if this was a real async worker, 
    # but here we're just moving it out of the request handler.
    # Ideally, we should use a new DB session here.
    
    new_db = database.SessionLocal()
    try:
        document = new_db.query(database.Document).filter(database.Document.id == document_id).first()
        if not document:
            return

        from app.services.document_processor import process_document, chunk_text
        from app.services import search
        
        print(f"📄 Processing document: {original_filename}")
        
        # Extract text from document
        content_data = process_document(document.file_path, document.mime_type)
        
        if content_data['content']:
            # Chunk the content
            chunks = chunk_text(content_data['content'])
            print(f"📝 Extracted {len(content_data['content'])} chars in {len(chunks)} chunks")
            
            # Generate tags
            tags = search.generate_content_tags(content_data['title'], content_data['content'])
            
            # Index each chunk
            for idx, chunk in enumerate(chunks):
                doc = {
                    'url': f"document://{document.id}",
                    'title': content_data['title'],
                    'content': chunk,
                    'chunk_index': idx,
                    'chatbot_id': chatbot_id,
                    'domain_id': domain_id,
                    'document_id': document.id,
                    'tags': tags
                }
                search.index_chatbot_content(chatbot_id, doc)
            
            # Update document status
            document.status = "indexed"
            new_db.commit()
            print(f"✅ Document indexed: {original_filename}")
        else:
            document.status = "failed"
            new_db.commit()
            print(f"⚠️  No content extracted from: {original_filename}")
            
    except Exception as e:
        print(f"❌ Error indexing document {original_filename}: {e}")
        if document:
            document.status = "failed"
            new_db.commit()
    finally:
        new_db.close()

@router.delete("/{domain_id}")
def delete_domain(
    domain_id: int,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    domain = db.query(database.Domain).filter(database.Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    chatbot = db.query(database.Chatbot).filter(
        database.Chatbot.id == domain.chatbot_id,
        database.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Not authorized")
    
    db.query(database.ScrapedPage).filter(database.ScrapedPage.domain_id == domain_id).delete()
    db.query(database.ScrapeJob).filter(database.ScrapeJob.domain_id == domain_id).delete()
    db.query(database.Document).filter(database.Document.domain_id == domain_id).delete()
    
    db.delete(domain)
    db.commit()
    return {"message": "Domain deleted successfully"}

