from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import boto3
from botocore.exceptions import ClientError
import uuid
import logging
import os
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BUCKET_NAME = "jackle-image-gallery"
CLOUDFRONT_DOMAIN = "https://d3fy0jl7xndosi.cloudfront.net"

def get_extension(file_path: str) -> str:
    return "." + file_path.split(".")[-1]


@app.post("/upload")
# the ... in File(...) means that it is required in the request body
async def upload_files(originalFile: UploadFile = File(...), thumbnailFile: UploadFile = File(...), gallery: str = Form(...)): 
    unique_id = str(uuid.uuid4())
    original_unique_name = unique_id + get_extension(originalFile.filename)
    thumbnail_unique_name = unique_id + get_extension(thumbnailFile.filename)
    original_s3_key = f"uploads/original/{gallery}/{original_unique_name}"
    thumbnail_s3_key = f"uploads/thumbnail/{gallery}/{thumbnail_unique_name}"
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
    original_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{original_s3_key}"
    thumbnail_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{thumbnail_s3_key}"
    return JSONResponse({"original_url": original_url, "thumbnail_url": thumbnail_url})


@app.get("/show")
# gallery here is in the param, not in the request body
async def show_files(gallery: str): 
    prefix = f"uploads/thumbnail/{gallery}/"
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION")
    )
    response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)
    if "Contents" not in response:
        return []
    urls = [
        f"{CLOUDFRONT_DOMAIN}/{obj['Key']}"
        for obj in response["Contents"]
    ]
    return urls


@app.delete("/delete")
async def show_files(fileName: str = Form(...), galleryName: str = Form(...)): 
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION")
    )
    paginator = s3_client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=BUCKET_NAME)
    search_expression = (
        f"Contents[?"
        f"starts_with(Key, `uploads/original/{galleryName}/{fileName}.`) || "
        f"starts_with(Key, `uploads/thumbnail/{galleryName}/{fileName}.`)"
        f"][]"
    )
    matching_files = page_iterator.search(search_expression)
    deleted_keys = []
    for obj in matching_files:
        key = obj["Key"]
        s3_client.delete_object(Bucket=BUCKET_NAME, Key=key)
        deleted_keys.append(key)
    return {
        "deleted_files": deleted_keys,
        "count": len(deleted_keys)
    }
    