import base64
import traceback

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from typing import List
import os
from contextlib import asynccontextmanager
from src.common.utils import (
    generate_uid,
    decode_base64_file,
    save_file_to_disk,
    save_file_metadata,
    get_file_metadata,
    get_all_files_metadata,
    delete_file_metadata,
    delete_file_from_disk,
    add_images_to_pdf,
)
from src.common.redis_client import redis_client
from src.fastapi_app.schemas import FileUpload, AddImages, FileResponse, FileMetadata, FileUidResponse
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await redis_client.connect()
    yield
    # Shutdown
    await redis_client.disconnect()


app = FastAPI(title="PDF Manager API", version="1.0.0", lifespan=lifespan, debug=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить все источники
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все методы (GET, POST, PUT, DELETE и т.д.)
    allow_headers=["*"],  # Разрешить все заголовки
)


@app.post("/upload", response_model=FileUidResponse)
async def upload_file(file_upload: FileUpload):
    """
    Upload PDF file in base64 format
    """
    try:
        uid = generate_uid()

        # Decode base64 file
        file_data = decode_base64_file(file_upload.file_data)

        # Save file to disk
        file_path = save_file_to_disk(file_data, uid)

        # Save metadata to Redis
        await save_file_metadata(uid, file_upload.filename, file_path)

        return FileUidResponse(uid=uid)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@app.get("/download/{uid}")
async def download_file(uid: str):
    """
    Download file by UID
    """
    try:
        # Get file metadata from Redis
        metadata = await get_file_metadata(uid)

        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")

        file_path = metadata["location"]
        filename = metadata["filename"]

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")

        return FileResponse(
            filename=filename,
            file_data=base64.b64encode(open(file_path, "rb").read()).decode("utf-8"),
            uid=uid
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")


@app.post("/add-images")
async def add_images_to_file(add_images: AddImages):
    """
    Add images to existing PDF file
    """
    try:
        # Get file metadata from Redis
        metadata = await get_file_metadata(add_images.uid)

        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")

        file_path = metadata["location"]

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")

        # Add images to PDF
        add_images_to_pdf(
            add_images.text,
            file_path,
            add_images.images,
            file_path
        )

        return {"message": "Images added successfully"}
    except Exception as e:
        print(f'Error adding images: {e} {traceback.format_exc()}')
        raise HTTPException(status_code=500, detail=f"Error adding images: {str(e)}")


@app.get("/files", response_model=List[FileMetadata])
async def get_all_files():
    """
    Get list of all files
    """
    try:
        files = await get_all_files_metadata()
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting files: {str(e)}")


@app.get("/files/{uid}", response_model=FileMetadata)
async def get_file_info(uid: str):
    """
    Get file information by UID
    """
    try:
        metadata = await get_file_metadata(uid)

        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")

        return FileMetadata(
            uid=uid, filename=metadata["filename"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting file info: {str(e)}"
        )


@app.delete("/files/{uid}")
async def delete_file(uid: str):
    """
    Delete file by UID
    """
    try:
        # Get file metadata from Redis
        metadata = await get_file_metadata(uid)

        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")

        file_path = metadata["location"]

        # Delete file from disk
        delete_file_from_disk(file_path)

        # Delete metadata from Redis
        await delete_file_metadata(uid)

        return {"message": "File deleted successfully"}
    except Exception as e:
        print(f'Error deleting file: {e} {traceback.format_exc()}')
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")


@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {"message": "PDF Manager API is running"}


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    try:
        # Check Redis connection
        await redis_client.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
