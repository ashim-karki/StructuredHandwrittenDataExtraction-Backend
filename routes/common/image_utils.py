import cv2
# from blueprints import Tag, Image
from blueprints.images import Image
import os


# def un_normalize(points: list, width: int, height: int) -> list:
#     x0, y0, x2, y2 = [int(p) for p in points]

#     x0 = int(width * (x0 / 1000))
#     x2 = int(width * (x2 / 1000))
#     y0 = int(height * (y0 / 1000))
#     y2 = int(height * (y2 / 1000))

#     return [x0, y0, x2, y2]


# def draw_rectange(image_path, bboxes):
#     image = cv2.imread(image_path)
#     for bbox in bboxes.values():
#         height, width, channels = image.shape
#         for box in bbox:
#             x, y, w, h = un_normalize(box, width, height)
#             start_point = (x, y)
#             end_point = (w, h)
#             color = (0, 0, 255)
#             thickness = 1
#             image = cv2.rectangle(image, start_point, end_point, color, thickness)
#     return image


def delete_images_for_folder(db, tag_id):
    images_for_tag = (
        db.query(Image).filter(Image.tag_id == tag_id)
    )
    image_paths = [image.path for image in images_for_tag.all()]
    IMAGE_BASE_PATH = "uploaded_images/"
    for file_path in image_paths:
        if os.path.exists(IMAGE_BASE_PATH + file_path):
            os.remove(IMAGE_BASE_PATH + file_path)
        else:
            raise Exception(f"Error: {file_path} does not exist")
