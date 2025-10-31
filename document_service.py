from typing import List, Dict
import PyPDF2
from docx import Document
import os
import search
import models

def chunk_text(text: str, chunk_size: int = 512) -> List[str]:
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

def extract_text_from_pdf(file_path: str) -> Dict[str, any]:
    text = ""
    title = ""
    
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        
        if reader.metadata and reader.metadata.title:
            title = reader.metadata.title
        
        for page in reader.pages:
            text += page.extract_text() + " "
    
    return {
        'title': title or os.path.basename(file_path),
        'content': text.strip(),
        'word_count': len(text.split())
    }

def extract_text_from_docx(file_path: str) -> Dict[str, any]:
    doc = Document(file_path)
    
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    text = ' '.join(paragraphs)
    
    title = doc.core_properties.title or os.path.basename(file_path)
    
    return {
        'title': title,
        'content': text,
        'word_count': len(text.split())
    }

def extract_text_from_txt(file_path: str) -> Dict[str, any]:
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        text = file.read()
    
    return {
        'title': os.path.basename(file_path),
        'content': text,
        'word_count': len(text.split())
    }

def process_document(document_id: int, file_path: str, file_type: str, chatbot_id: int, domain_id: int, db) -> bool:
    try:
        if file_type == 'application/pdf' or file_path.endswith('.pdf'):
            extracted = extract_text_from_pdf(file_path)
        elif file_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/docx'] or file_path.endswith('.docx'):
            extracted = extract_text_from_docx(file_path)
        elif file_type == 'text/plain' or file_path.endswith('.txt'):
            extracted = extract_text_from_txt(file_path)
        else:
            return False
        
        document = db.query(models.DomainDocument).filter(models.DomainDocument.id == document_id).first()
        if not document:
            return False
        
        document.title = extracted['title']
        document.content_preview = extracted['content'][:500]
        document.word_count = extracted['word_count']
        document.status = 'completed'
        db.commit()
        
        chunks = chunk_text(extracted['content'])
        tags = search.generate_content_tags(extracted['title'], extracted['content'])
        
        for idx, chunk in enumerate(chunks):
            doc_data = {
                'url': f"document://{document.filename}",
                'title': extracted['title'],
                'content': chunk,
                'chunk_index': idx,
                'chatbot_id': chatbot_id,
                'domain_id': domain_id,
                'document_id': document_id,
                'source_type': 'document',
                'tags': tags
            }
            search.index_chatbot_content(chatbot_id, doc_data)
        
        return True
    except Exception as e:
        print(f"Error processing document: {e}")
        document = db.query(models.DomainDocument).filter(models.DomainDocument.id == document_id).first()
        if document:
            document.status = 'failed'
            db.commit()
        return False

def delete_document_from_index(chatbot_id: int, document_id: int):
    try:
        from search import es, get_chatbot_index
        index_name = get_chatbot_index(chatbot_id)
        
        query = {
            "query": {
                "term": {"document_id": document_id}
            }
        }
        
        es.delete_by_query(index=index_name, body=query)
        return True
    except Exception as e:
        print(f"Error deleting document from index: {e}")
        return False

