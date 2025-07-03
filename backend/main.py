from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import boto3
from botocore.exceptions import ClientError
import uuid
import logging
import os
from datetime import datetime, timedelta, timezone
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
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../static"))
app.mount("/staticfiles", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(frontend_path, "index.html"))

REGION_NAME = os.getenv("AWS_REGION")
BUCKET_NAME = "jackle-image-gallery"
CLOUDFRONT_DOMAIN = "https://d3fy0jl7xndosi.cloudfront.net"
s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=REGION_NAME
)

def get_extension(file_path: str) -> str:
    return "." + file_path.split(".")[-1]


@app.post("/upload")
# the ... in File(...) means that it is required in the request body
async def upload_file(originalFile: UploadFile = File(...), thumbnailFile: UploadFile = File(...), gallery: str = Form(...), expiringDay: int = Form(...)): 
    unique_id = str(uuid.uuid4())
    original_unique_name = unique_id + get_extension(originalFile.filename)
    thumbnail_unique_name = unique_id + get_extension(thumbnailFile.filename)
    original_s3_key = f"uploads/original/{gallery}/{original_unique_name}"
    thumbnail_s3_key = f"uploads/thumbnail/{gallery}/{thumbnail_unique_name}"
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

    # new stuff
    expiration_time = (datetime.now(timezone.utc) - timedelta(days=expiringDay)).isoformat() # this is current setting as minus time to make sure the tasks is always expiring already
    upload_time = datetime.now(timezone.utc).isoformat()
    dynamodb_client = boto3.client('dynamodb', region_name=REGION_NAME)
    dynamodb_client.put_item(
        TableName='image-gallery-db',
        Item={
            "uuid": {"S": unique_id}, 
            "gallery": {"S": gallery},
            "original_s3_key": {"S": original_s3_key},
            "thumbnail_s3_key": {"S": thumbnail_s3_key},
            "original_url": {"S": original_url},
            "thumbnail_url": {"S": thumbnail_url},
            "expiration_date": {"S": expiration_time},
            "uploaded_at": {"S": upload_time}
        }
    )
    
    return JSONResponse({"original_url": original_url, "thumbnail_url": thumbnail_url})


@app.get("/show")
# gallery here is in the param, not in the request body
async def show_files(gallery: str): 
    prefix = f"uploads/thumbnail/{gallery}/"
    response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)
    if "Contents" not in response:
        return []
    urls = [
        f"{CLOUDFRONT_DOMAIN}/{obj['Key']}"
        for obj in response["Contents"]
    ]
    return urls


@app.delete("/delete")
async def delete_file(fileName: str = Form(...), galleryName: str = Form(...)): 
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
        print("key here:",key)
        s3_client.delete_object(Bucket=BUCKET_NAME, Key=key)
        deleted_keys.append(key)
    return {
        "deleted_files": deleted_keys,
        "count": len(deleted_keys)
    }


def delete_s3_prefix(bucket_name, prefix):
    paginator = s3_client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
    deleted_keys = []
    for page in page_iterator:
        if "Contents" in page:
            objects = [{"Key": obj["Key"]} for obj in page["Contents"]]
            s3_client.delete_objects(Bucket=bucket_name, Delete={"Objects": objects})
            deleted_keys.extend([obj["Key"] for obj in page["Contents"]])
    return {
        "deleted_files": deleted_keys,
        "count": len(deleted_keys)
    }


@app.delete("/delete-gallery")
async def delete_gallery(galleryName: str = Form(...)): 
    original = delete_s3_prefix(BUCKET_NAME, f"uploads/original/{galleryName}/")
    thumbnail = delete_s3_prefix(BUCKET_NAME, f"uploads/thumbnail/{galleryName}/")
    total_deleted = original["deleted_files"] + thumbnail["deleted_files"]
    return {
        "message": f"Gallery '{galleryName}' deleted.",
        "deleted_files": total_deleted,
        "count": len(total_deleted)
    }

    