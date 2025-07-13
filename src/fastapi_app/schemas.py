from typing import List

from pydantic import BaseModel, Field


class FileUpload(BaseModel):
    """Schema for file upload request."""
    file_data: str = Field(..., description="Base64 encoded file content")
    filename: str = Field(..., description="Original name of the file being uploaded")


class AddImages(BaseModel):
    """Schema for adding images to an existing PDF."""
    text: str = Field(None, description="Text to append to the PDF")
    uid: str = Field(..., description="Unique identifier of the PDF file")
    images: List[str] = Field(..., description="List of base64 encoded images to append to the PDF")


class FileResponse(BaseModel):
    """Response schema containing the unique identifier of the processed file."""
    uid: str = Field(..., description="Unique identifier of the processed file")
    file_data: str = Field(..., description="Base64 encoded file data")
    filename: str = Field(..., description="Name of the processed file")


class FileUidResponse(BaseModel):
    """Response schema containing the unique identifier of the processed file."""
    uid: str = Field(..., description="Unique identifier of the processed file")


class FileMetadata(BaseModel):
    """Schema containing metadata about a processed file."""
    uid: str = Field(..., description="Unique identifier of the file")
    filename: str = Field(..., description="Original name of the file")
