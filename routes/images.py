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
 
# @router.delete("/image/{filename}")
# def delete_image(
#     filename: str, db: Session = Depends(get_db)
# ):
#     image = db.query(blueprints.images.Image).filter_by(name=filename).first()

#     if image is None:
#         raise HTTPException(status_code=404, detail="Image not found")

#     db.delete(image)
#     db.commit()
#     return {"message": "Image deleted successfully!"}

# add_pagination(router)

# @router.get("/allimages", response_model=Page[Image])
# def get_all_images(db: Session = Depends(get_db), user=Depends(get_user_token)):
#     user_images = db.query(blueprints.images.Image).filter(
#         blueprints.images.Image.user == user["uid"]
#     )
#     return paginate(
#         [Image(id=image.id, name=image.name, path=image.path) for image in user_images]
#     )

# @router.post("/direct_upload")
# # def read_tags(db: Session = Depends(get_db), user=Depends(get_user_token)):
# def upload_images_and_create_new_tag(
#     tag_name: str = Form(...),
#     files: List[UploadFile] = File(...),
#     user=Depends(get_user_token),
#     db=Depends(get_db),
# ):
#     # tag = db.query(blueprints.tags.Tag).filter_by(id=int(tag_id[0])).first()

#     color = random.choice(
#         [
#             "#ff6900",
#             "#fcb900",
#             "#7bdcb5",
#             "#00d084",
#             "#8ed1fc",
#             "#0693e3",
#             "#abb8c3",
#             "#eb144c",
#             "#f78da7",
#             "#9900ef",
#             "#00ff00",
#         ]
#     )
#     tag = blueprints.tags.Tag(
#         name=tag_name,
#         user=user["uid"],
#         description="This is tag description",
#         color=color,
#     )
#     db.add(tag)
#     db.flush()
#     try:
#         for file in files:
#             filename = file.filename
#             id = uuid.uuid4().hex
#             folder_path = "uploaded_images/"
#             if not os.path.exists(folder_path):
#                 os.makedirs(folder_path)
#             path = folder_path + id + file.content_type.replace("image/", ".")
#             with open(path, "wb") as buffer:
#                 shutil.copyfileobj(file.file, buffer)
#             # TODO: optimize, need to find way to get image size without opening it
#             img = PILImage.open(path)
#             image = blueprints.images.Image(
#                 name=filename,
#                 user=user["uid"],
#                 path=id + file.content_type.replace("image/", "."),
#                 tag=tag,
#                 size_x=img.size[0],
#                 size_y=img.size[1],
#             )
#             db.add(image)
#             db.flush()
#         db.commit()
#     except Exception as e:
#         raise HTTPException(
#             status_code=400, detail="Images upload failed! because of " + str(e)
#         )

#     return {"message": "Images uploaded successfully!"}