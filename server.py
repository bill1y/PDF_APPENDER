from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
import psutil
#import win32gui
#import win32process
#import win32api
import os
import tempfile
from typing import Optional, List
from pydantic import BaseModel
from PyPDF2 import PdfReader, PdfWriter
import io

app = FastAPI(title="PDF Document Server", version="1.0.0")

class DocumentPath(BaseModel):
    path: str
    process_id: int
    window_title: str

class AppendRequest(BaseModel):
    target_document_path: str

def get_window_text(hwnd):
    """Get window title text"""
    try:
        return win32gui.GetWindowText(hwnd)
    except:
        return ""

def get_process_path(pid):
    """Get the executable path of a process"""
    try:
        process = psutil.Process(pid)
        return process.exe()
    except:
        return None

def find_adobe_acrobat_documents():
    """Find all Adobe Acrobat windows and extract document paths"""
    documents = []
    
    def enum_windows_callback(hwnd, results):
        if win32gui.IsWindowVisible(hwnd):
            window_title = get_window_text(hwnd)
            
            # Check if it's an Adobe Acrobat window
            if ("Adobe Acrobat" in window_title or 
                "Acrobat Reader" in window_title or
                window_title.endswith(".pdf - Adobe Acrobat") or
                window_title.endswith(".pdf - Adobe Acrobat Reader")):
                
                try:
                    # Get process ID
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    
                    # Get process path
                    process_path = get_process_path(pid)
                    
                    if process_path and ("acrobat" in process_path.lower() or "reader" in process_path.lower()):
                        # Extract document path from window title
                        document_path = extract_document_path_from_title(window_title)
                        
                        if document_path:
                            documents.append({
                                "path": document_path,
                                "process_id": pid,
                                "window_title": window_title,
                                "process_path": process_path
                            })
                except Exception as e:
                    print(f"Error processing window {hwnd}: {e}")
    
    win32gui.EnumWindows(enum_windows_callback, [])
    return documents

def extract_document_path_from_title(title):
    """Extract document path from Adobe Acrobat window title"""
    try:
        # Common patterns for Adobe Acrobat window titles:
        # "document.pdf - Adobe Acrobat"
        # "document.pdf - Adobe Acrobat Reader DC"
        # "C:\path\to\document.pdf - Adobe Acrobat"
        
        if " - Adobe" in title:
            potential_path = title.split(" - Adobe")[0].strip()
            
            # Check if it's a full path
            if os.path.exists(potential_path):
                return potential_path
            
            # If it's just a filename, we need to find the full path
            # This is more complex and might require additional Windows API calls
            # For now, we'll try to get it from the process command line
            return find_full_document_path(potential_path)
        
        return None
    except Exception as e:
        print(f"Error extracting document path from title '{title}': {e}")
        return None

def find_full_document_path(filename):
    """Try to find the full path of a document given just the filename"""
    try:
        # Get all Adobe processes
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and ('acrobat' in proc.info['name'].lower() or 'reader' in proc.info['name'].lower()):
                    cmdline = proc.info['cmdline']
                    if cmdline:
                        # Look for PDF files in command line arguments
                        for arg in cmdline:
                            if arg.endswith('.pdf') and os.path.exists(arg):
                                if os.path.basename(arg) == filename:
                                    return arg
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # If not found in command line, return the filename as-is
        return filename
    except Exception as e:
        print(f"Error finding full document path: {e}")
        return filename

@app.get("/get_document")
async def get_document():
    """Get the path of currently opened PDF document in Adobe Acrobat"""
    try:
        documents = find_adobe_acrobat_documents()
        
        if not documents:
            raise HTTPException(
                status_code=404, 
                detail="No Adobe Acrobat document found. Please make sure Adobe Acrobat is running with a PDF document open."
            )
        
        # Return the first document found (you can modify this logic as needed)
        main_document = documents[0]
        
        return JSONResponse(content={
            "status": "success",
            "document": {
                "path": main_document["path"],
                "process_id": main_document["process_id"],
                "window_title": main_document["window_title"]
            },
            "total_documents_found": len(documents),
            "all_documents": documents
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving document information: {str(e)}")

@app.post("/append_to_document")
async def append_to_document(
    file: UploadFile = File(..., description="PDF file to append"),
    target_path: str = None
):
    """Append content from uploaded PDF to the currently open Adobe Acrobat document"""
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # If no target path provided, try to get the currently open document
        if not target_path:
            documents = find_adobe_acrobat_documents()
            if not documents:
                raise HTTPException(
                    status_code=404,
                    detail="No target document specified and no Adobe Acrobat document found"
                )
            target_path = documents[0]["path"]
        
        # Verify target document exists
        if not os.path.exists(target_path):
            raise HTTPException(status_code=404, detail=f"Target document not found: {target_path}")
        
        # Read the uploaded file
        uploaded_content = await file.read()
        uploaded_pdf = PdfReader(io.BytesIO(uploaded_content))
        
        # Read the target document
        with open(target_path, 'rb') as target_file:
            target_pdf = PdfReader(target_file)
            
            # Create a new PDF writer
            pdf_writer = PdfWriter()
            
            # Add all pages from target document
            for page in target_pdf.pages:
                pdf_writer.add_page(page)
            
            # Add all pages from uploaded document
            for page in uploaded_pdf.pages:
                pdf_writer.add_page(page)
            
            # Create a temporary file for the merged PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                pdf_writer.write(temp_file)
                temp_path = temp_file.name
            
            # Replace the original file with the merged version
            # Note: This might require closing the document in Adobe Acrobat first
            import shutil
            
            # Create a backup
            backup_path = target_path + '.backup'
            shutil.copy2(target_path, backup_path)
            
            try:
                # Replace the original file
                shutil.move(temp_path, target_path)
                
                return JSONResponse(content={
                    "status": "success",
                    "message": f"Successfully appended {len(uploaded_pdf.pages)} pages to {target_path}",
                    "target_document": target_path,
                    "pages_added": len(uploaded_pdf.pages),
                    "total_pages": len(target_pdf.pages) + len(uploaded_pdf.pages),
                    "backup_created": backup_path
                })
                
            except Exception as e:
                # Restore from backup if something went wrong
                if os.path.exists(backup_path):
                    shutil.move(backup_path, target_path)
                raise HTTPException(
                    status_code=500, 
                    detail=f"Error replacing target document (restored from backup): {str(e)}"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error appending document: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "PDF Document Server",
        "version": "1.0.0",
        "endpoints": {
            "GET /get_document": "Get currently opened PDF document path in Adobe Acrobat",
            "POST /append_to_document": "Append PDF content to target document",
            "GET /docs": "API documentation"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)