from typing import List

from pydantic import BaseModel, Field


class AddImages(BaseModel):
    """Schema for adding images to an existing PDF."""
    text: str = Field(None, description="Text to append to the PDF")
    images: List[str] = Field(..., description="List of base64 encoded images to append to the PDF")
