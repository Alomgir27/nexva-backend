import boto3
import os
import logging
import uuid
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL")
R2_REGION = "us-east-1"

if not all([R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME, R2_ENDPOINT_URL, R2_PUBLIC_URL]):
    raise ValueError("Missing R2 configuration. Please check your .env file.")

class R2Service:
    def __init__(self):
        self._client = None
        self.bucket_name = R2_BUCKET_NAME
        logger.info(f"R2Service configured - bucket: {self.bucket_name}")
    
    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client(
                's3',
                endpoint_url=R2_ENDPOINT_URL,
                aws_access_key_id=R2_ACCESS_KEY_ID,
                aws_secret_access_key=R2_SECRET_ACCESS_KEY,
                region_name=R2_REGION,
                config=boto3.session.Config(
                    retries={'max_attempts': 2},
                    read_timeout=10,
                    connect_timeout=5
                )
            )
            logger.info("R2 client initialized")
        return self._client
    
    def upload_file(self, local_path: str, r2_key: str, content_type: str = "application/octet-stream") -> Dict[str, Any]:
        try:
            if not os.path.exists(local_path):
                return {"success": False, "error": f"File not found: {local_path}"}
            
            with open(local_path, 'rb') as file:
                self.client.upload_fileobj(
                    file,
                    self.bucket_name,
                    r2_key,
                    ExtraArgs={'ContentType': content_type}
                )
            
            public_url = f"{R2_PUBLIC_URL}/{r2_key}"
            file_size = os.path.getsize(local_path)
            
            logger.info(f"Uploaded: {r2_key} ({file_size} bytes)")
            
            return {
                "success": True,
                "r2_key": r2_key,
                "url": public_url,
                "size": file_size
            }
        except Exception as e:
            logger.error(f"Upload failed: {r2_key} → {e}")
            return {"success": False, "error": str(e)}
    
    def delete_file(self, r2_key: str) -> Dict[str, Any]:
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=r2_key)
            logger.info(f"Deleted: {r2_key}")
            return {"success": True}
        except Exception as e:
            logger.error(f"Delete failed: {r2_key} → {e}")
            return {"success": False, "error": str(e)}
    
    def generate_file_path(self, domain_id: int, filename: str) -> str:
        sanitized = self._sanitize_filename(filename)
        return f"documents/{domain_id}/{uuid.uuid4().hex[:8]}_{sanitized}"
    
    def _sanitize_filename(self, filename: str) -> str:
        import re
        name_parts = filename.rsplit('.', 1)
        name = name_parts[0]
        ext = f".{name_parts[1]}" if len(name_parts) > 1 else ""
        name = name.replace(' ', '-')
        name = re.sub(r'[^a-zA-Z0-9\-_.]', '-', name)
        name = re.sub(r'-+', '-', name)
        name = name.strip('-')
        if not name:
            name = f"file_{uuid.uuid4().hex[:8]}"
        return f"{name}{ext}"
    
    def _get_content_type(self, filename: str) -> str:
        ext = filename.lower().split('.')[-1]
        types = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'txt': 'text/plain'
        }
        return types.get(ext, 'application/octet-stream')

r2_service = R2Service()

