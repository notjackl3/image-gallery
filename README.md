# Image Gallery 📸
This is a full-stack cloud-based image management app that allows users to upload, browse, and download images seamlessly. Built with performance, scalability, and ease-of-use in mind, the system compresses images before upload, caches them globally using a CDN, and periodically cleans up expired files — all powered by AWS. 

*(I often struggle with organizing and sharing large sets of images while keeping things fast and lightweight. So, I built this app to solve my own problem! I understand that Apple users have airdrop which makes this easier, but I am not using iPhone...)*

## Features

- Upload and display images in different user-defined galleries.
- Display optimized thumbnails while storing full-resolution originals.
- Users can delete images or view them by gallery.
- Expiration system: images auto-delete after a set time
- Global caching and faster delivery.

## How It's Made:

**Tech used:** FastAPI, JavaScript, HTML, CSS, AWS S3, Lambda, DynamoDB, CloudFront, EC2, Nginx.

The backend is powered by `fastapi`, exposing a set of `restful api` endpoints that handle uploading, retrieving, and deleting images. Uploaded files are first compressed in the browser using the `canvas api`, then sent to `s3` via the backend. Each image has two versions: a high-res original and a lightweight thumbnail.

To enhance performance and reduce latency, `aws cloudfront` is used to cache and deliver the images globally. Expiration metadata is stored in `dynamodb`, and an `aws lambda` function, scheduled with `eventbridge`, runs daily to automatically delete expired images.

The frontend is built with vanilla `html/css/js`, communicating directly with the backend and rendering galleries dynamically. Hosting is done on an `ec2 ubuntu` instance, using `nginx` as the web server and reverse proxy.

## What I Learned Through This Project:

- How to structure and expose a RESTful API with FastAPI.
- Client-side image processing with the Canvas API and Blob objects.
- S3 file management and CloudFront integration for high-performance delivery.
- Using DynamoDB for storing metadata and EventBridge + Lambda for scheduled automation.
- Deploying full-stack apps with EC2 + Nginx.
- Mnaging IAM roles and permissions for secure AWS resource access.


