import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from fastapi import HTTPException
import logging
from typing import BinaryIO
from uuid import uuid4
from config import settings

class S3Service:
    def __init__(self):
        self.client = self._create_client()
        self.bucket = settings.S3_BUCKET
    
    def _create_client(self):
        try:
            return boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY,
                aws_secret_access_key=settings.AWS_SECRET_KEY,
                region_name=settings.S3_REGION
            )

        except Exception as e:
            logging.error(f"Failed to create S3 client: {e}")
            raise
        
    # Generate S3_key
    def generate_s3_key(self, filename: str):
        return f"video/uploads/{uuid4()}_{filename}"
    
    # Uploads file to S3 as video object
    def upload_file(self, file_obj: BinaryIO , key: str, content_type: str = None):
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
                
            self.client.upload_fileobj(file_obj, self.bucket, key, ExtraArgs=extra_args)
            return f"s3://{self.bucket}/{key}"
            
        except NoCredentialsError:
            raise HTTPException(status_code=500, detail="AWS credentials not configured")
        except ClientError as e:
            logging.error(f"S3 upload error: {e}")
            raise HTTPException(status_code=500, detail="File upload failed")
    
    # Downloads video object from S3
    def download_file(self, key: str, video_path: str):
        try:
            with open(video_path, "wb") as f:
                self.client.download_fileobj(self.bucket, key, f)
        except NoCredentialsError:
            raise HTTPException(status_code=500, detail="AWS credentials not configured")
        except ClientError as e:
            logging.error(f"S3 download error: {e}")
            raise HTTPException(status_code=500, detail="File download failed")
    
    # Delete the current object in S3
    def delete_file(self, key: str):
        try:
            self.client.delete_object(self.bucket, key)
        except NoCredentialsError:
            raise HTTPException(status_code=500, detail="AWS credentials not configured")
        except ClientError as e:
            logging.error(f"S3 delete error: {e}")
            raise HTTPException(status_code=500, detail="File delete failed")

# Initialize service
s3_service = S3Service()

