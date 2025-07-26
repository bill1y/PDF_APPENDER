import base64
import json
import os
import tempfile
import uuid
from io import BytesIO
from typing import List

from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import psutil


def get_opened_pdf_process() -> str | None:
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        name = proc.info['name']
        args = proc.info['cmdline']
        if name and 'sumatrapdf' in name.lower():
            for arg in reversed(args):
                if arg.lower().endswith('.pdf'):
                    return arg
    return None


def add_images_to_pdf(text: str | None, pdf_path: str, images_base64: List[str], output_path: str):
    """Add images to existing PDF as new pages"""
    # Read existing PDF file
    reader = PdfReader(pdf_path)
    # Create PDF writer object for output
    writer = PdfWriter()
    # process images
    images_base64 = [preprocess_base64_image(image) for image in images_base64 if image]

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


def preprocess_base64_image(data_url: str) -> base64:
    # Убираем префикс до запятой
    if data_url.startswith("data:image"):
        header, base64_data = data_url.split(",", 1)
    else:
        base64_data = data_url
    # Добавляем padding, если его не хватает
    missing_padding = len(base64_data) % 4
    if missing_padding:
        base64_data += '=' * (4 - missing_padding)
    return base64_data
