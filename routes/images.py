from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
import blueprints.folders
from db.data_access import get_db
from sqlalchemy.orm import Session
from pydantic import BaseModel
from starlette.responses import FileResponse
import shutil
from typing import List
from fastapi_pagination import add_pagination
import blueprints.images
from PIL import Image as PILImage
import os

router = APIRouter()

@router.post("/upload")
# def read_tags(db: Session = Depends(get_db), user=Depends(get_user_token)):
def upload_images_with_folder(
    folder_id: str = Form(...), # ... means required
    files: List[UploadFile] = File(...),
    db=Depends(get_db),
):

    folder = db.query(blueprints.folders.Folder).filter_by(id=int(folder_id)).first()

    if folder is None:
        raise HTTPException(status_code=400, detail="Folder not found!")

    try:
        for file in files:
            filename = file.filename
            # id = uuid.uuid4().hex
            folder_path = "uploaded_images/"
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            path = folder_path + filename # replaced id with filename so that image will be saved with its original name
            with open(path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            # TODO: optimize, need to find way to get image size without opening it
            img = PILImage.open(path)
            image = blueprints.images.Image(
                name=filename,
                path=folder_path + filename, # replaced id with filename so that image will be saved with its original name
                folder=folder,
                size_x=img.size[0],
                size_y=img.size[1],
            )
            db.add(image)
            db.flush()
        db.commit()
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Images upload failed! because of " + str(e)
        )

    return {"message": "Images uploaded successfully!"}

@router.get("/image/{filename}")
def read_file(filename: str):
    return FileResponse(f"uploaded_images/{filename}")

class Image(BaseModel):
    id: int
    name: str
    path: str

# discard image
from fastapi import HTTPException

# TODO: add delete image