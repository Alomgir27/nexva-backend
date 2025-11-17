from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from app import database
from app.services import auth

router = APIRouter()

def _get_document_with_auth(document_id: int, current_user: database.User, db: Session):
    document = db.query(database.Document).filter(database.Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    chatbot = db.query(database.Chatbot).filter(
        database.Chatbot.id == document.chatbot_id,
        database.Chatbot.user_id == current_user.id
    ).first()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Not authorized")
    
    return document

@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    document = _get_document_with_auth(document_id, current_user, db)
    if not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        document.file_path,
        media_type=document.mime_type or "application/octet-stream",
        filename=document.file_name
    )

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    document = _get_document_with_auth(document_id, current_user, db)
    
    if os.path.exists(document.file_path):
        try:
            os.remove(document.file_path)
        except OSError:
            pass
    
    db.delete(document)
    db.commit()
    return {"message": "Document deleted successfully"}

