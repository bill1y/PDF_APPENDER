import base64
import json
import os
import tempfile
import uuid
from io import BytesIO
from typing import Optional, List, Dict

from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from src.common.consts import REDIS_FILE_METADATA_KEY
from src.common.redis_client import redis_client
from reportlab.lib.units import cm


def generate_uid() -> str:
    """Generate unique identifier"""
    return str(uuid.uuid4())


def decode_base64_file(base64_string: str) -> bytes:
    """Decode base64 string to bytes"""
    return base64.b64decode(base64_string)


def save_file_to_disk(file_data: bytes, uid: str, files_dir: str = "files") -> str:
    """Save file to disk with UID as filename"""
    if not os.path.exists(files_dir):
        os.makedirs(files_dir)

    file_path = os.path.join(files_dir, f"{uid}.pdf")
    with open(file_path, "wb") as f:
        f.write(file_data)

    return file_path


async def save_file_metadata( uid: str, filename: str, location: str):
    """Save file metadata to Redis"""
    metadata = {
        "filename": filename,
        "location": location
    }
    await redis_client.set(REDIS_FILE_METADATA_KEY.format(uid=uid), metadata)


async def get_file_metadata(uid: str) -> Optional[Dict]:
    """Get file metadata from Redis"""
    return await redis_client.get(REDIS_FILE_METADATA_KEY.format(uid=uid))


async def get_all_files_metadata() -> List[Dict]:
    """Get all files metadata from Redis"""
    files = []
    keys = await redis_client.keys(REDIS_FILE_METADATA_KEY.format(uid="*"))
    for key in keys:
        key = key.split(":")[1]
        metadata = await get_file_metadata(key)
        if metadata:
            files.append({"uid": key, **metadata})
    return files


async def delete_file_metadata(redis_client, uid: str):
    """Delete file metadata from Redis"""
    await redis_client.delete(REDIS_FILE_METADATA_KEY.format(uid=uid))


def delete_file_from_disk(file_path: str):
    """Delete file from disk"""
    if os.path.exists(file_path):
        os.remove(file_path)


def add_images_to_pdf(text: str | None, pdf_path: str, images_base64: List[str], output_path: str):
    """Add images to existing PDF as new pages"""
    # Read existing PDF file
    reader = PdfReader(pdf_path)
    # Create PDF writer object for output
    writer = PdfWriter()

    # Copy all existing pages from original PDF
    for page in reader.pages:
        writer.add_page(page)

    # Create temporary PDF file for image processing
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
        temp_pdf_path = temp_pdf.name

    try:
        # Create new PDF canvas with A4 page size
        c = canvas.Canvas(temp_pdf_path, pagesize=A4)
        page_width, page_height = A4

        # Process each base64 encoded image
        for img_base64 in images_base64:
            # Decode base64 string to binary image data
            img_data = base64.b64decode(img_base64)
            # Open image from binary data
            img = Image.open(BytesIO(img_data))

            # Get original image dimensions
            img_width, img_height = img.size
            # Calculate aspect ratio to maintain proportions
            aspect_ratio = img_width / img_height

            # Scale image to fit page while maintaining aspect ratio
            if aspect_ratio > (page_width / page_height):
                # Image is wider - fit to page width
                new_width = page_width
                new_height = page_width / aspect_ratio
            else:
                # Image is taller - fit to page height
                new_height = page_height
                new_width = page_height * aspect_ratio

            # Calculate position to center image on page
            x = (page_width - new_width) / 2
            y = (page_height - new_height) / 2

            # Add text to the top of the page if provided
            if text and text.strip():
                # Set font for text
                c.setFont("Helvetica", 12)
                # Split text into lines for multiline support
                lines = text.split('\n')
                # Start text position 2cm from top
                y_text = page_height - 2 * cm
                # Line height between text lines
                line_height = 14

                # Draw each line of text
                for line in lines:
                    c.drawString(2 * cm, y_text, line)
                    y_text -= line_height

            # Save image to temporary PNG file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_img:
                img.save(temp_img.name, 'PNG')
                temp_img_path = temp_img.name

            try:
                # Draw image on PDF page at calculated position and size
                c.drawImage(temp_img_path, x, y, width=new_width, height=new_height)
                # Finish current page and start new one
                c.showPage()
            finally:
                # Clean up temporary image file
                os.unlink(temp_img_path)

        # Save the canvas to PDF file
        c.save()

        # Read the temporary PDF containing images
        temp_reader = PdfReader(temp_pdf_path)

        # Add all image pages to the main PDF writer
        for page in temp_reader.pages:
            writer.add_page(page)

        # Write final PDF to output file
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)

    finally:
        # Clean up temporary PDF file
        if os.path.exists(temp_pdf_path):
            os.unlink(temp_pdf_path)
