# How to run

```bash
docker compose up -d
```

# Docs
```bash
http://localhost:8000/docs
```

# Lovable prompt:
```
When the user first visits the page, they should be presented with two main options: either select a file from the sidebar on the left, or upload a new file via a drag-and-drop area.

On the left panel, there should be a collapsible container displaying the last five files the user has worked with. By default, this container shows only those five files. The user can click a button to uncollapse the container and expand the full list of all files they’ve used. When expanded, a collapse button should also appear, allowing them to revert back to the five recent files view for a cleaner interface.

Each file entry in the list should have a small delete button (a cross icon) beside it, so the user can remove unwanted files from the list.

The user can select a file from the list, or upload a new file using a drag-and-drop area (which replaces the default drawing field when no file is selected). Upon uploading or selecting a file:

The file is sent to a file upload endpoint, and the system receives a UID for that file.

The current working file’s UID is stored in memory.

If a file is selected or uploaded (i.e., the UID is not empty), the page should display the Tldraw drawing canvas, allowing the user to freely draw.

There should also be a "Download PDF" button. When clicked, the app must send a request to the image-to-PDF endpoint, including the UID and the drawn image in Base64 format.

Additionally:

Use the provided endpoint to retrieve the full list of available files.

All endpoints are described in the OpenAPI specification below.

If there are any form fields (e.g. text inputs) on the left panel, and they are filled out by the user, those values should also be sent along together with the file when uploading.


{"openapi":"3.1.0","info":{"title":"PDF Manager API","version":"1.0.0"},"paths":{"/upload":{"post":{"summary":"Upload File","description":"Upload PDF file in base64 format","operationId":"upload_file_upload_post","requestBody":{"content":{"application/json":{"schema":{"$ref":"#/components/schemas/FileUpload"}}},"required":true},"responses":{"200":{"description":"Successful Response","content":{"application/json":{"schema":{"$ref":"#/components/schemas/FileUidResponse"}}}},"422":{"description":"Validation Error","content":{"application/json":{"schema":{"$ref":"#/components/schemas/HTTPValidationError"}}}}}}},"/download/{uid}":{"get":{"summary":"Download File","description":"Download file by UID","operationId":"download_file_download__uid__get","parameters":[{"name":"uid","in":"path","required":true,"schema":{"type":"string","title":"Uid"}}],"responses":{"200":{"description":"Successful Response","content":{"application/json":{"schema":{}}}},"422":{"description":"Validation Error","content":{"application/json":{"schema":{"$ref":"#/components/schemas/HTTPValidationError"}}}}}}},"/add-images":{"post":{"summary":"Add Images To File","description":"Add images to existing PDF file","operationId":"add_images_to_file_add_images_post","requestBody":{"content":{"application/json":{"schema":{"$ref":"#/components/schemas/AddImages"}}},"required":true},"responses":{"200":{"description":"Successful Response","content":{"application/json":{"schema":{}}}},"422":{"description":"Validation Error","content":{"application/json":{"schema":{"$ref":"#/components/schemas/HTTPValidationError"}}}}}}},"/files":{"get":{"summary":"Get All Files","description":"Get list of all files","operationId":"get_all_files_files_get","responses":{"200":{"description":"Successful Response","content":{"application/json":{"schema":{"items":{"$ref":"#/components/schemas/FileMetadata"},"type":"array","title":"Response Get All Files Files Get"}}}}}}},"/files/{uid}":{"get":{"summary":"Get File Info","description":"Get file information by UID","operationId":"get_file_info_files__uid__get","parameters":[{"name":"uid","in":"path","required":true,"schema":{"type":"string","title":"Uid"}}],"responses":{"200":{"description":"Successful Response","content":{"application/json":{"schema":{"$ref":"#/components/schemas/FileMetadata"}}}},"422":{"description":"Validation Error","content":{"application/json":{"schema":{"$ref":"#/components/schemas/HTTPValidationError"}}}}}},"delete":{"summary":"Delete File","description":"Delete file by UID","operationId":"delete_file_files__uid__delete","parameters":[{"name":"uid","in":"path","required":true,"schema":{"type":"string","title":"Uid"}}],"responses":{"200":{"description":"Successful Response","content":{"application/json":{"schema":{}}}},"422":{"description":"Validation Error","content":{"application/json":{"schema":{"$ref":"#/components/schemas/HTTPValidationError"}}}}}}},"/":{"get":{"summary":"Root","description":"Root endpoint","operationId":"root__get","responses":{"200":{"description":"Successful Response","content":{"application/json":{"schema":{}}}}}}},"/health":{"get":{"summary":"Health Check","description":"Health check endpoint","operationId":"health_check_health_get","responses":{"200":{"description":"Successful Response","content":{"application/json":{"schema":{}}}}}}}},"components":{"schemas":{"AddImages":{"properties":{"text":{"type":"string","title":"Text","description":"Text to append to the PDF"},"uid":{"type":"string","title":"Uid","description":"Unique identifier of the PDF file"},"images":{"items":{"type":"string"},"type":"array","title":"Images","description":"List of base64 encoded images to append to the PDF"}},"type":"object","required":["uid","images"],"title":"AddImages","description":"Schema for adding images to an existing PDF."},"FileMetadata":{"properties":{"uid":{"type":"string","title":"Uid","description":"Unique identifier of the file"},"filename":{"type":"string","title":"Filename","description":"Original name of the file"}},"type":"object","required":["uid","filename"],"title":"FileMetadata","description":"Schema containing metadata about a processed file."},"FileUidResponse":{"properties":{"uid":{"type":"string","title":"Uid","description":"Unique identifier of the processed file"}},"type":"object","required":["uid"],"title":"FileUidResponse","description":"Response schema containing the unique identifier of the processed file."},"FileUpload":{"properties":{"file_data":{"type":"string","title":"File Data","description":"Base64 encoded file content"},"filename":{"type":"string","title":"Filename","description":"Original name of the file being uploaded"}},"type":"object","required":["file_data","filename"],"title":"FileUpload","description":"Schema for file upload request."},"HTTPValidationError":{"properties":{"detail":{"items":{"$ref":"#/components/schemas/ValidationError"},"type":"array","title":"Detail"}},"type":"object","title":"HTTPValidationError"},"ValidationError":{"properties":{"loc":{"items":{"anyOf":[{"type":"string"},{"type":"integer"}]},"type":"array","title":"Location"},"msg":{"type":"string","title":"Message"},"type":{"type":"string","title":"Error Type"}},"type":"object","required":["loc","msg","type"],"title":"ValidationError"}}}}
```

123
