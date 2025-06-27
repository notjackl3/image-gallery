from fastapi import UploadFile, File
import uuid
import boto3
from botocore.exceptions import ClientError
import logging

import os
from dotenv import load_dotenv
load_dotenv()

BUCKET_NAME = "jackle-image-gallery"

def get_extension(file_path: str) -> str:
    return "." + file_path.split(".")[-1]


def upload_to_s3(originalFile: UploadFile, thumbnailFile: UploadFile, gallery_name: str) -> str:
    unique_id = str(uuid.uuid4())
    original_unique_name = unique_id + get_extension(originalFile.filename)
    thumbnail_unique_name = unique_id + get_extension(thumbnailFile.filename)
    original_s3_key = f"uploads/original/{gallery_name}/{original_unique_name}"
    thumbnail_s3_key = f"uploads/thumbnail/{gallery_name}/{thumbnail_unique_name}"
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION")
    )

    for file, key in zip([originalFile, thumbnailFile], [original_s3_key, thumbnail_s3_key]):
        try:
            s3_client.upload_fileobj(
                file.file,
                BUCKET_NAME,
                key,
                ExtraArgs={
                    # "ACL": "public-read",
                    "ContentType": file.content_type
                }
            )
        except ClientError as e:
            logging.error(e)
            raise e
        finally:
            file.file.close()

    return f"https://{BUCKET_NAME}.s3.amazonaws.com/{original_s3_key}", f"https://{BUCKET_NAME}.s3.amazonaws.com/{thumbnail_s3_key}"

