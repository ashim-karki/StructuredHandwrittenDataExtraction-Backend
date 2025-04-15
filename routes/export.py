import os
import zipfile
import json
import csv
import io
import tempfile
import uuid
import shutil
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import and_

from db.data_access import get_db
from blueprints import AnnotatedWord, Folder, Image, Label, OCR, Task

router = APIRouter()

# Models for request and response
class ExportOptions(BaseModel):
    includeOcr: bool = True
    includeTables: bool = True
    format: str = "json"  # "json", "csv", "excel"

class ExportRequest(BaseModel):
    task_id: int
    folder_id: int
    options: ExportOptions

class ExportStatusResponse(BaseModel):
    export_id: str
    status: str  # "pending", "in_progress", "completed", "failed"
    progress: float = 0.0
    download_url: Optional[str] = None
    error: Optional[str] = None

# In-memory store for export status (in production, use a database)
export_status = {}

# Directory to store exports
EXPORT_DIR = os.path.join(tempfile.gettempdir(), "data_exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

# Utility function to get export status
def get_export_status(export_id: str) -> ExportStatusResponse:
    if export_id not in export_status:
        raise HTTPException(status_code=404, detail="Export not found")
    return export_status[export_id]

# Utility function to update export status
def update_export_status(export_id: str, data: Dict):
    if export_id not in export_status:
        export_status[export_id] = ExportStatusResponse(
            export_id=export_id,
            status="pending"
        )
    export_status[export_id] = ExportStatusResponse(
        **{**export_status[export_id].dict(), **data}
    )

# Background task to generate export
# async def generate_export(export_id: str, task_id: int, folder_id: int, options: ExportOptions, db: Session):
#     try:
#         # Update status to in_progress
#         update_export_status(export_id, {"status": "in_progress", "progress": 0.0})
        
#         # Verify the task and folder exist
#         task = db.query(Task).filter(Task.id == task_id).first()
#         folder = db.query(Folder).filter(Folder.id == folder_id).first()
        
#         if not task or not folder:
#             update_export_status(export_id, {
#                 "status": "failed", 
#                 "error": "Task or folder not found"
#             })
#             return
        
#         # Get all images for the folder
#         images = db.query(Image).filter(Image.folder_id == folder_id).all()
        
#         if not images:
#             update_export_status(export_id, {
#                 "status": "failed", 
#                 "error": "No images found in the folder"
#             })
#             return
        
#         # Create temporary directory for export files
#         export_path = os.path.join(EXPORT_DIR, export_id)
#         os.makedirs(export_path, exist_ok=True)
        
#         # Export data
#         all_data = []
        
#         for i, image in enumerate(images):
#             # Update progress
#             progress = (i / len(images)) * 100
#             update_export_status(export_id, {"progress": progress})
            
#             # Get annotations for image
#             annotated_words = db.query(AnnotatedWord).filter(AnnotatedWord.image_id == image.id).all()
            
#             # Get OCR data if requested
#             ocr_data = []
#             if options.includeOcr:
#                 ocr_records = db.query(OCR).filter(OCR.image_id == image.id).all()
                
#                 # Convert OCR objects to dictionaries
#                 ocr_data = []
#                 for ocr in ocr_records:
#                     ocr_data.append({
#                         "word_id": ocr.word_id,
#                         "text": ocr.text,
#                         "position": {
#                             "x0": float(ocr.posx_0) if ocr.posx_0 is not None else 0,
#                             "y0": float(ocr.posy_0) if ocr.posy_0 is not None else 0,
#                             "x1": float(ocr.posx_1) if ocr.posx_1 is not None else 0,
#                             "y1": float(ocr.posy_1) if ocr.posy_1 is not None else 0
#                         }
#                     })
#                 # print("OCR data:", ocr_data)
#             # Format annotations - ensure we're converting from SQLAlchemy objects to dictionaries
#             annotations = []
#             for annotated_word in annotated_words:
#                 # Access the related word object safely
#                 word_text = ""
#                 if hasattr(annotated_word, 'word') and annotated_word.word is not None:
#                     word_text = annotated_word.word.text
                
#                 # Access the related label safely
#                 label_name = None
#                 if hasattr(annotated_word, 'label') and annotated_word.label is not None:
#                     label_name = annotated_word.label
                
#                 annotations.append({
#                     "id": annotated_word.id,
#                     "image_id": annotated_word.image_id,
#                     "word_id": annotated_word.word_id,
#                     "word": word_text,
#                     "label_id": annotated_word.label_id,
#                     "label": label_name
#                 })
            
#             # Get image metadata
#             image_data = {
#                 "image_id": image.id,
#                 "filename": image.name,
#                 "path": image.path,
#                 "annotations": annotations,
#                 "ocr_data": ocr_data if options.includeOcr else []
#             }
            
#             all_data.append(image_data)

#             # print("all_data:", all_data)
        
#         # Create export files based on format
#         zip_filename = f"export_{task.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
#         zip_path = os.path.join(EXPORT_DIR, zip_filename)
        
#         with zipfile.ZipFile(zip_path, 'w') as zipf:
#             # Export JSON
#             if options.format == "json" or options.format == "all":
#                 json_data = {
#                     "task_name": task.name,
#                     "folder_name": folder.name,
#                     "export_date": datetime.now().isoformat(),
#                     "images": all_data
#                 }

#                 print("Json data:\n\n\n", json_data)
                
#                 json_file = os.path.join(export_path, "export_data.json")
#                 with open(json_file, 'w') as f:
#                     json.dump(json_data, f, indent=2)
                
#                 zipf.write(json_file, os.path.basename(json_file))
#                 print("Export data saved to temp directory")
            
#             # Export CSV
#             if options.format == "csv" or options.format == "all":
#                 csv_file = os.path.join(export_path, "export_data.csv")
                
#                 with open(csv_file, 'w', newline='') as f:
#                     writer = csv.writer(f)
                    
#                     # Write header
#                     header = ["image_id", "image_name", "word_id", "text", "label"]
#                     writer.writerow(header)
                    
#                     # Write data
#                     for image_data in all_data:
#                         for annotation in image_data["annotations"]:
#                             row = [
#                                 image_data["image_id"],
#                                 image_data["filename"],
#                                 annotation["word_id"],
#                                 annotation["word"],
#                                 annotation["label"] or ""
#                             ]
#                             writer.writerow(row)
                
#                 zipf.write(csv_file, os.path.basename(csv_file))
            
#             # Export Excel (if requested and available)
#             if options.format == "excel" or options.format == "all":
#                 try:
#                     import pandas as pd
                    
#                     # Convert data to DataFrame
#                     rows = []
#                     for image_data in all_data:
#                         for annotation in image_data["annotations"]:
#                             row = {
#                                 "image_id": image_data["image_id"],
#                                 "image_name": image_data["filename"],
#                                 "word_id": annotation["word_id"],
#                                 "text": annotation["word"],
#                                 "label": annotation["label"] or ""
#                             }
#                             rows.append(row)
                    
#                     df = pd.DataFrame(rows)
                    
#                     # Export to Excel
#                     excel_file = os.path.join(export_path, "export_data.xlsx")
#                     df.to_excel(excel_file, index=False)
                    
#                     zipf.write(excel_file, os.path.basename(excel_file))
#                 except ImportError:
#                     # If pandas is not available, log an error but continue
#                     pass
        
#         # Create a README file
#         readme_content = f"""
# Export Information
# -----------------
# Task: {task.name}
# Folder: {folder.name}
# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Included OCR Data: {"Yes" if options.includeOcr else "No"}
# Included Table Data: {"Yes" if options.includeTables else "No"}
# Format: {options.format}

# Files Included:
# """
        
#         if options.format == "json" or options.format == "all":
#             readme_content += "- export_data.json: JSON format of all annotations and data\n"
        
#         if options.format == "csv" or options.format == "all":
#             readme_content += "- export_data.csv: CSV format of annotations\n"
        
#         if options.format == "excel" or options.format == "all":
#             readme_content += "- export_data.xlsx: Excel format of annotations\n"
        
#         readme_file = os.path.join(export_path, "README.txt")
#         with open(readme_file, 'w') as f:
#             f.write(readme_content)
        
#         zipf.write(readme_file, os.path.basename(readme_file))
            
#         # Update status to completed with download URL
#         download_url = f"/static/exports/{zip_filename}"
#         update_export_status(export_id, {
#             "status": "completed",
#             "progress": 100.0,
#             "download_url": download_url
#         })
        
#         # Schedule cleanup after some time (e.g., 1 hour)
#         # In a real app, use a task scheduler
        
#     except Exception as e:
#         # Handle any exceptions
#         update_export_status(export_id, {
#             "status": "failed",
#             "error": str(e)
#         })
        
#         # Log the error
#         print(f"Export error: {str(e)}")
#     finally:
#         # Clean up temporary directory
#         if os.path.exists(export_path):
#             shutil.rmtree(export_path)


async def generate_export(export_id: str, task_id: int, folder_id: int, options: ExportOptions, db: Session):
    try:
        # Update status to in_progress
        update_export_status(export_id, {"status": "in_progress", "progress": 0.0})
        
        # Verify the task and folder exist
        task = db.query(Task).filter(Task.id == task_id).first()
        folder = db.query(Folder).filter(Folder.id == folder_id).first()
        
        if not task or not folder:
            update_export_status(export_id, {
                "status": "failed", 
                "error": "Task or folder not found"
            })
            return
        
        # Get all images for the folder
        images = db.query(Image).filter(Image.folder_id == folder_id).all()
        
        if not images:
            update_export_status(export_id, {
                "status": "failed", 
                "error": "No images found in the folder"
            })
            return
        
        # Create temporary directory for export files
        export_path = os.path.join(EXPORT_DIR, export_id)
        os.makedirs(export_path, exist_ok=True)
        
        # Export data
        all_data = []
        
        for i, image in enumerate(images):
            # Update progress
            progress = (i / len(images)) * 100
            update_export_status(export_id, {"progress": progress})
            
            # Get annotations for image
            annotated_words = db.query(AnnotatedWord).filter(AnnotatedWord.image_id == image.id).all()
            
            # Get OCR data if requested
            ocr_data = []
            if options.includeOcr:
                ocr_records = db.query(OCR).filter(OCR.image_id == image.id).all()
                
                # Convert OCR objects to dictionaries
                for ocr in ocr_records:
                    ocr_data.append({
                        "word_id": ocr.word_id,
                        "text": ocr.text,
                        "position": {
                            "x0": float(ocr.posx_0) if ocr.posx_0 is not None else 0,
                            "y0": float(ocr.posy_0) if ocr.posy_0 is not None else 0,
                            "x1": float(ocr.posx_1) if ocr.posx_1 is not None else 0,
                            "y1": float(ocr.posy_1) if ocr.posy_1 is not None else 0
                        }
                    })
            
            # Format annotations - ensure we're converting from SQLAlchemy objects to dictionaries
            annotations = []
            for annotated_word in annotated_words:
                # Access the related word object safely
                word_text = ""
                if hasattr(annotated_word, 'word') and annotated_word.word is not None:
                    word_text = str(annotated_word.word)  # Ensure it's a string
                
                # Access the related label safely
                label_name = None
                if hasattr(annotated_word, 'label') and annotated_word.label is not None:
                    label_name = str(annotated_word.label)  # Ensure it's a string
                
                annotations.append({
                    "id": annotated_word.id,
                    "image_id": annotated_word.image_id,
                    "word_id": annotated_word.word_id,
                    "word": word_text,
                    "label_id": annotated_word.label_id,
                    "label": label_name
                })
            
            # Get image metadata - ensure all values are JSON serializable
            image_data = {
                "image_id": image.id,
                "filename": str(image.name),
                "path": str(image.path),
                "annotations": annotations,
                "ocr_data": ocr_data if options.includeOcr else []
            }
            
            all_data.append(image_data)
        
        # Create export files based on format
        zip_filename = f"export_{task.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        zip_path = os.path.join(EXPORT_DIR, zip_filename)
        
        # Create a README file
        readme_content = f"""
Export Information
-----------------
Task: {task.name}
Folder: {folder.name}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Included OCR Data: {"Yes" if options.includeOcr else "No"}
Included Table Data: {"Yes" if options.includeTables else "No"}
Format: {options.format}

Files Included:
"""
        
        if options.format == "json" or options.format == "all":
            readme_content += "- export_data.json: JSON format of all annotations and data\n"
        
        if options.format == "csv" or options.format == "all":
            readme_content += "- export_data.csv: CSV format of annotations\n"
        
        if options.format == "excel" or options.format == "all":
            readme_content += "- export_data.xlsx: Excel format of annotations\n"
        
        readme_file = os.path.join(export_path, "README.txt")
        with open(readme_file, 'w') as f:
            f.write(readme_content)
        
        # Custom JSON encoder for handling non-serializable objects
        class CustomJSONEncoder(json.JSONEncoder):
            def default(self, obj):
                try:
                    return super().default(obj)
                except TypeError:
                    return str(obj)  # Convert non-serializable objects to strings
        
        # Write all export files first, then add them to the ZIP
        if options.format == "json" or options.format == "all":
            json_data = {
                "task_name": str(task.name),
                "folder_name": str(folder.name),
                "export_date": datetime.now().isoformat(),
                "images": all_data
            }
            
            json_file = os.path.join(export_path, "export_data.json")
            with open(json_file, 'w') as f:
                json.dump(json_data, f, indent=2, cls=CustomJSONEncoder)
        
        # Export CSV
        if options.format == "csv" or options.format == "all":
            csv_file = os.path.join(export_path, "export_data.csv")
            
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write header
                header = ["image_id", "image_name", "word_id", "text", "label"]
                writer.writerow(header)
                
                # Write data
                for image_data in all_data:
                    for annotation in image_data["annotations"]:
                        row = [
                            image_data["image_id"],
                            image_data["filename"],
                            annotation["word_id"],
                            annotation["word"],
                            annotation["label"] or ""
                        ]
                        writer.writerow(row)
        
        # Export Excel (if requested and available)
        excel_file = None
        if options.format == "excel" or options.format == "all":
            try:
                import pandas as pd
                
                # Convert data to DataFrame
                rows = []
                for image_data in all_data:
                    for annotation in image_data["annotations"]:
                        row = {
                            "image_id": image_data["image_id"],
                            "image_name": image_data["filename"],
                            "word_id": annotation["word_id"],
                            "text": annotation["word"],
                            "label": annotation["label"] or ""
                        }
                        rows.append(row)
                
                df = pd.DataFrame(rows)
                
                # Export to Excel
                excel_file = os.path.join(export_path, "export_data.xlsx")
                df.to_excel(excel_file, index=False)
            except ImportError:
                # If pandas is not available, log an error but continue
                print("Warning: pandas not installed, Excel export not available")
        
        # Now create the ZIP file with all the generated files
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            # Add the README file to the ZIP
            zipf.write(readme_file, os.path.basename(readme_file))
            
            # Add JSON file if created
            if options.format == "json" or options.format == "all":
                json_file = os.path.join(export_path, "export_data.json")
                zipf.write(json_file, os.path.basename(json_file))
            
            # Add CSV file if created
            if options.format == "csv" or options.format == "all":
                csv_file = os.path.join(export_path, "export_data.csv")
                zipf.write(csv_file, os.path.basename(csv_file))
            
            # Add Excel file if created
            if excel_file and os.path.exists(excel_file):
                zipf.write(excel_file, os.path.basename(excel_file))
        
        # Update status to completed with download URL
        download_url = f"/static/exports/{zip_filename}"
        print("download",download_url)
        update_export_status(export_id, {
            "status": "completed",
            "progress": 100.0,
            "download_url": download_url
        })
        
        # Schedule cleanup after some time (e.g., 1 hour)
        # In a real app, use a task scheduler
        
    except Exception as e:
        # Handle any exceptions
        update_export_status(export_id, {
            "status": "failed",
            "error": str(e)
        })
        
        # Log the error
        print(f"Export error: {str(e)}")
        # For debugging, print the traceback
        import traceback
        traceback.print_exc()
    finally:
        # Clean up temporary directory
        if os.path.exists(export_path):
            shutil.rmtree(export_path)


@router.post("/export", response_model=Dict)
async def create_export(
    export_request: ExportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start an export process for a task's annotations.
    """
    # Generate export ID
    export_id = str(uuid.uuid4())
    
    # Initialize status
    export_status[export_id] = ExportStatusResponse(
        export_id=export_id,
        status="pending",
        progress=0.0
    )
    
    # Start background task
    background_tasks.add_task(
        generate_export,
        export_id,
        export_request.task_id,
        export_request.folder_id,
        export_request.options,
        db
    )
    
    return {"export_id": export_id}

@router.get("/export/status/{export_id}", response_model=ExportStatusResponse)
async def check_export_status(export_id: str):
    """
    Check the status of an export process.
    """
    return get_export_status(export_id)

@router.get("/export/download/{filename}")
async def download_export(filename: str):
    """
    Download an exported file.
    """
    file_path = os.path.join(EXPORT_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Export file not found")
    
    # Return the URL path for the static file server
    return {
        "file_url": f"/static/exports/{filename}"
    }

@router.get("/export/tasks")
async def get_exportable_tasks(db: Session = Depends(get_db)):
    """
    Get a list of tasks that can be exported (completed tasks).
    """
    completed_tasks = db.query(Task).filter(Task.status == 2).all()
    
    return [{
        "id": task.id,
        "name": task.name,
        "description": task.description,
        "type": task.type,
        "folder_id": task.folder_id,
        "percentage_complete": task.percentage_complete,
        "status": task.status
    } for task in completed_tasks]