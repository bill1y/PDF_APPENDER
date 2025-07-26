import base64
import sys
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

if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

dotenv_path = os.path.join(base_path, ".env")
load_dotenv(dotenv_path)

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

