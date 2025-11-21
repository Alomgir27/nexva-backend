import PyPDF2
from docx import Document as DocxDocument
from typing import Dict
import os

def process_document(file_path: str, mime_type: str) -> Dict[str, str]:
    """Extract text content from uploaded documents"""
    try:
        if mime_type == "application/pdf" or file_path.endswith('.pdf'):
            return _process_pdf(file_path)
        elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or file_path.endswith('.docx'):
            return _process_docx(file_path)
        elif mime_type == "text/plain" or file_path.endswith('.txt'):
            return _process_txt(file_path)
        else:
            return {"title": os.path.basename(file_path), "content": ""}
    except Exception as e:
        print(f"❌ Error processing document {file_path}: {e}")
        return {"title": os.path.basename(file_path), "content": ""}

def _process_pdf(file_path: str) -> Dict[str, str]:
    """Extract text from PDF"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            # Use filename as title, clean it up
            title = os.path.splitext(os.path.basename(file_path))[0]
            title = title.replace('_', ' ').replace('-', ' ').title()
            
            return {"title": title, "content": text.strip()}
    except Exception as e:
        print(f"❌ PDF processing error: {e}")
        return {"title": os.path.basename(file_path), "content": ""}

def _process_docx(file_path: str) -> Dict[str, str]:
    """Extract text from DOCX"""
    try:
        doc = DocxDocument(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()])
        
        # Use filename as title, clean it up
        title = os.path.splitext(os.path.basename(file_path))[0]
        title = title.replace('_', ' ').replace('-', ' ').title()
        
        return {"title": title, "content": text.strip()}
    except Exception as e:
        print(f"❌ DOCX processing error: {e}")
        return {"title": os.path.basename(file_path), "content": ""}

def _process_txt(file_path: str) -> Dict[str, str]:
    """Extract text from TXT file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
            
            # Use first line as title or filename
            lines = text.split('\n')
            title = lines[0].strip() if lines else os.path.basename(file_path)
            if len(title) > 100:
                title = os.path.splitext(os.path.basename(file_path))[0]
                title = title.replace('_', ' ').replace('-', ' ').title()
            
            return {"title": title, "content": text.strip()}
    except Exception as e:
        print(f"❌ TXT processing error: {e}")
        return {"title": os.path.basename(file_path), "content": ""}

def chunk_text(text: str, chunk_size: int = 512) -> list:
    """Split text into smaller chunks for indexing"""
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
