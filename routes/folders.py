from fastapi import APIRouter, status, Depends, HTTPException
from db.data_access import get_db
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
import blueprints.folders, blueprints.images
from routes.common.image_utils import delete_images_for_folder

router = APIRouter()

# this is required in the sqlalchemy 2.0 version
# we can directly return the output of query when using sqlalchemy 1.4
class FolderResponse(BaseModel):
    id: int
    name: str
    description: str
    color: str
    num_images: int

    class Config:
        orm_mode = True


@router.get("/folders")
def read_folders(db: Session = Depends(get_db)):
    # get all folders and count images for each folder
    folders = (
        db.query(
            blueprints.folders.Folder.id,
            blueprints.folders.Folder.name,
            blueprints.folders.Folder.description,
            blueprints.folders.Folder.color,
            func.count(blueprints.images.Image.id).label("num_images"),
        )
        .join(
            blueprints.images.Image,
            blueprints.images.Image.folder_id == blueprints.folders.Folder.id,
            isouter=True,
        )
        .group_by(blueprints.folders.Folder.id)
    ).all()

    return [FolderResponse(**folder._asdict()) for folder in folders]

@router.get("/folders/{folder_id}")
def read_folder(folder_id: int, db: Session = Depends(get_db)):
    # Query for the folder
    folder = (
        db.query(blueprints.folders.Folder)
        .filter(blueprints.folders.Folder.id == folder_id)
        .first()  # .first() returns the first result or None
    )
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Folder not found",
        )
    
    # Query for images related to the folder
    result = (
        db.query(blueprints.images.Image)
        .join(blueprints.folders.Folder, blueprints.images.Image.folder_id == blueprints.folders.Folder.id)
        .filter(blueprints.folders.Folder.id == folder_id)
        .all()  # .all() returns the list of results
    )

    return {"folder": folder, "images": result, "labels": ["testing label"]}


class CreateFolder(BaseModel):
    name: str
    description: str
    color: str

    class Config:
        orm_mode = True


@router.post("/folders")
def create_folder(folder: CreateFolder, db: Session = Depends(get_db)):
    folder = blueprints.folders.Folder(
        name=folder.name, description=folder.description, color=folder.color
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


@router.put("/folders/{folder_id}")
def update_folder(
    folder: CreateFolder,
    folder_id: int,
    db: Session = Depends(get_db),
):
    db_folder = (
        db.query(blueprints.folders.Folder)
        .filter(blueprints.folders.Folder.id == folder_id)
        .first()
    )
    if db_folder:
        db_folder.name = folder.name
        db_folder.description = folder.description
        db_folder.color = folder.color
        db.commit()
        db.refresh(db_folder)
        return db_folder
    else:
        return f"No folder with id = {folder_id}"


@router.delete("/folders/{folder_id}")
def delete_folder(
    folder_id: int, db: Session = Depends(get_db)
):
    db_folder = (
        db.query(blueprints.folders.Folder)
        .filter(blueprints.folders.Folder.id == folder_id)
        .first()
    )
    if db_folder:
        try:
            # delete_images_for_folder(db, folder_id, user=user)
            db.delete(db_folder)
            db.commit()
            return f"Successfully deleted folder with id {folder_id}"
        except Exception as e:
            return f"Error deleting images for folder maybe image file to delete does not exist {folder_id}"

    return f"No folder with id = {folder_id}"
