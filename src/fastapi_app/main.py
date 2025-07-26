import base64
import traceback

from fastapi import FastAPI, HTTPException
from typing import List
import os
from contextlib import asynccontextmanager
from src.common.utils import (
    get_opened_pdf_process,
    add_images_to_pdf,
)
from src.fastapi_app.schemas import AddImages
from fastapi.middleware.cors import CORSMiddleware
from pyngrok import ngrok
from dotenv import load_dotenv
import subprocess

load_dotenv()  # take environment variables



@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="PDF Manager API", version="1.0.0", lifespan=lifespan, debug=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить все источники
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все методы (GET, POST, PUT, DELETE и т.д.)
    allow_headers=["*"],  # Разрешить все заголовки
)

@app.post("/add-images")
async def add_images_to_file(add_images: AddImages):
    """
    Add images to existing PDF file
    """
    file_path = get_opened_pdf_process()
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    try:
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
    

@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {"message": "PDF Manager API is running"}



if __name__ == "__main__":
    import uvicorn
    from pyngrok import ngrok

    port = int(os.getenv('SERVER_PORT', 8080))
    ngrok_domain=os.getenv('NGROK_DOMAIN')
    ngrok_token=os.getenv('NGROK_TOKEN')
    ngrok.set_auth_token(ngrok_token)
    public_url = ngrok.connect(port, domain=ngrok_domain)
    print(f"------------- NGROK tunnel is opened: {public_url} -------------")

    uvicorn.run(app, host="0.0.0.0", port=port)
