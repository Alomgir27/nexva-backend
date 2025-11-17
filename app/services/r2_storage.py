import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from typing import BinaryIO
from app.core.config import settings

class R2Storage:
    def __init__(self):
        if not all([
            settings.R2_ACCOUNT_ID,
            settings.R2_ACCESS_KEY_ID,
            settings.R2_SECRET_ACCESS_KEY,
            settings.R2_BUCKET_NAME
        ]):
            raise ValueError("R2 credentials incomplete in config")
        
        self.client = boto3.client(
            's3',
            endpoint_url=f'https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            config=Config(signature_version='s3v4'),
            region_name='auto'
        )
        self.bucket = settings.R2_BUCKET_NAME
        self.public_url = settings.R2_PUBLIC_URL
    
    def upload_file(self, file_obj: BinaryIO, object_key: str, content_type: str = None) -> str:
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            self.client.upload_fileobj(file_obj, self.bucket, object_key, ExtraArgs=extra_args)
            return f"{self.public_url}/{object_key}"
        except ClientError as e:
            raise Exception(f"R2 upload failed: {e}")
    
    def delete_file(self, object_key: str):
        try:
            self.client.delete_object(Bucket=self.bucket, Key=object_key)
        except ClientError as e:
            raise Exception(f"R2 delete failed: {e}")
    
    def get_file_url(self, object_key: str) -> str:
        return f"{self.public_url}/{object_key}"

def get_r2_client() -> R2Storage:
    if not settings.USE_R2_STORAGE:
        raise ValueError("R2 storage not enabled")
    return R2Storage()

