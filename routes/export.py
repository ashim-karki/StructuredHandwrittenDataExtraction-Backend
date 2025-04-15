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
import re

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

# Utility function to parse table data from text content
def parse_table_data(text_content):
    """
    Parse table text content into rows and columns.
    Assumes that rows are separated by newlines and columns by commas or tabs.
    """
    if not text_content:
        return []
    
    # Check if the text already contains CSV-like data
    if ',' in text_content:
        # Split by newlines to get rows
        rows = text_content.strip().split('\n')
        # For each row, split by comma to get columns
        table_data = [row.split(',') for row in rows]
    else:
        # If no commas, try splitting by whitespace/tabs
        rows = text_content.strip().split('\n')
        # For each row, split by whitespace
        table_data = [re.split(r'\s+', row.strip()) for row in rows]
    
    return table_data


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
        
        # Initialize data structures for different label types
        text_data = []  # For "Text" label - export as JSON
        table_data_by_image = {}  # For "Table" label - will collect table data by image
        
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
                        "text": ocr.text,
                    })
            
            # Sort annotations by label type
            text_annotations = []
            table_annotations = []
            
            for annotated_word in annotated_words:
                # Access the related word object safely
                word_text = ""
                if hasattr(annotated_word, 'word') and annotated_word.word is not None:
                    word_text = str(annotated_word.word.text)  # Ensure it's a string
                
                # Access the related label safely
                label_name = None
                if hasattr(annotated_word, 'label') and annotated_word.label is not None:
                    label_name = str(annotated_word.label.name)
                
                annotation_data = {
                    # "word_id": annotated_word.id,
                    "Text": word_text,
                    # "label": label_name
                }
                
                # Sort by label type
                if label_name == "Text":
                    text_annotations.append(annotation_data)
                elif label_name == "Table":
                    table_annotations.append(annotation_data)
            
            # Get image metadata - ensure all values are JSON serializable
            image_data = {
                # "image_id": image.id,
                "filename": str(image.name),
                # "ocr_data": ocr_data if options.includeOcr else []
            }
            
            # Add to text data collection if we have text annotations
            if text_annotations:
                text_image_data = {**image_data}
                text_image_data["annotations"] = text_annotations
                text_data.append(text_image_data)
            
            # Process table annotations for this image
            if table_annotations:
                # Combine all table content from this image
                table_content = "\n".join([annotation["Text"] for annotation in table_annotations])
                if table_content:
                    # Store the table data with image info
                    table_data_by_image[image.name] = parse_table_data(table_content)
        
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
- text_data.json: JSON format of all text annotations
- [image_name]_table.csv: CSV format of table data for each image with table annotations
"""
        
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
        
        # Write JSON file for text annotations
        json_data = {
            "task_name": str(task.name),
            "folder_name": str(folder.name),
            "export_date": datetime.now().isoformat(),
            "extracted_data": text_data
        }
        
        json_file = os.path.join(export_path, "text_data.json")
        with open(json_file, 'w') as f:
            json.dump(json_data, f, indent=2, cls=CustomJSONEncoder)
        
        # Create separate CSV files for each image's table data
        table_csv_files = []
        for image_name, table_rows in table_data_by_image.items():
            if table_rows:
                # Create a valid filename from image name
                safe_name = "".join([c if c.isalnum() else "_" for c in image_name])
                csv_filename = f"{safe_name}_table.csv"
                csv_file_path = os.path.join(export_path, csv_filename)
                
                # Write the table data directly to CSV without adding metadata headers
                with open(csv_file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    # Write all rows directly
                    writer.writerows(table_rows)
                
                table_csv_files.append((csv_file_path, csv_filename))
        print(table_csv_files)
        
        # Now create the ZIP file with all the generated files
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            # Add the README file to the ZIP
            zipf.write(readme_file, os.path.basename(readme_file))
            
            # Add JSON file for text annotations
            zipf.write(json_file, os.path.basename(json_file))
            
            # Add CSV files for table annotations
            for csv_path, csv_name in table_csv_files:
                zipf.write(csv_path, csv_name)
        
        # Update status to completed with download URL
        download_url = f"/static/exports/{zip_filename}"
        print("download", download_url)
        update_export_status(export_id, {
            "status": "completed",
            "progress": 100.0,
            "download_url": download_url
        })
        
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