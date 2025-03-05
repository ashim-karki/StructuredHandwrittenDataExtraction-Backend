from blueprints import Folder
from sqlalchemy.orm import Session

def get_images_from_folder(db, folder_id):
    image_folder = db.query(Folder).filter_by(id=folder_id).first()
    images = list(image_folder.images)
    return images
