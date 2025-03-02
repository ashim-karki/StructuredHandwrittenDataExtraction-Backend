from fastapi import APIRouter, Depends, HTTPException
from db.data_access import get_db
from sqlalchemy.orm import Session

from routes.common.keyvalue_extraction import extract_keyvalue

from blueprints import AnnotatedWord, Folder, Image, Label, OCR

router = APIRouter()

@router.get("/annotations/{image_id}/{folder_id}")
def get_image_annotations(
    image_id: int,
    folder_id: int,
    db: Session = Depends(get_db)
):
    # Verify the folder exists
    folder = db.query(Folder).filter(Folder.id == folder_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Verify the image exists and belongs to the specified folder
    image = db.query(Image).filter(
        Image.id == image_id,
        Image.folder_id == folder_id
    ).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found in the specified folder")

    # Get all annotations for the specific image
    annotated_words = db.query(AnnotatedWord).filter(AnnotatedWord.image_id == image_id).all()
    
    # Format the response data
    response_data = [
        {
            "id": annotated_word.id,
            "image_id": annotated_word.image_id,
            "word_id": annotated_word.word_id,
            "word": annotated_word.word.text,
            "label_id": annotated_word.label_id,
            "label": annotated_word.label.name
        }
        for annotated_word in annotated_words
    ]
    print(response_data[0]["word"])
    print(type(response_data[0]["word"]))
    return response_data


@router.post("/annotate/{image_id}/{folder_id}")
def post_image_annotation(
    image_id: int,
    folder_id: int,
    updated_text: str,  # Ensure this is the correct field name
    db: Session = Depends(get_db),
):
    # Verify the folder exists
    folder = db.query(Folder).filter(Folder.id == folder_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Verify the image exists and belongs to the specified folder
    image = db.query(Image).filter(
        Image.id == image_id,
        Image.folder_id == folder_id
    ).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found in the specified folder")
    
    # Check if OCR record exists and update, otherwise create new
    word = db.query(OCR).filter(OCR.image_id == image.id).first()
    if word:
        word.text = updated_text
    else:
        word = OCR(
            text=updated_text,
            posx_0=0,
            posy_0=0,
            posx_1=0,
            posy_1=0,
            image_id=image.id,
        )
        db.add(word)
    db.commit()
    db.refresh(word)
    
    # Check if Annotation record exists and update, otherwise create new
    annotation = db.query(AnnotatedWord).filter(AnnotatedWord.image_id == image.id).first()
    if annotation:
        annotation.word_id = word.word_id
    else:
        annotation = AnnotatedWord(
            word_id=word.word_id,
            image_id=image.id,
            label_id=None  # Adjust as needed
        )
        db.add(annotation)
    db.commit()
    db.refresh(annotation)
    
    return {"message": "Annotation successfully added or updated", "annotation_id": annotation.id}

# @router.post("/annotations/{image_id}/{folder_id}")
# def post_image_annotation(
#     image_id: int,
#     folder_id: int,
#     db: Session = Depends(get_db),
# ):
#     # Verify the folder exists
#     folder = db.query(Folder).filter(Folder.id == folder_id).first()
#     if not folder:
#         raise HTTPException(status_code=404, detail="Folder not found")
    
#     # Verify the image exists and belongs to the specified folder
#     image = db.query(Image).filter(
#         Image.id == image_id,
#         Image.folder_id == folder_id
#     ).first()
#     if not image:
#         raise HTTPException(status_code=404, detail="Image not found in the specified folder")

#     # Process the specific image
#     file_path = "uploaded_images/" + image.name
#     key_value = extract_keyvalue(file_path, image_id)
    
#     added_annotations = []
    
#     for item in key_value:
#         # Create OCR record
#         word = OCR(
#             text=item["value"],
#             posx_0=item["value_bbox"][0],
#             posy_0=item["value_bbox"][1],
#             posx_1=item["value_bbox"][2],
#             posy_1=item["value_bbox"][3],
#             image_id=image_id,
#         )
#         db.add(word)
#         db.commit()  # Ensures the ID is generated
        
#         # Create Label record
#         label = Label(
#             name=item["key"],
#             posx_0=item["key_bbox"][0],
#             posy_0=item["key_bbox"][1],
#             posx_1=item["key_bbox"][2],
#             posy_1=item["key_bbox"][3],
#             image_id=image_id,
#         )
#         db.add(label)
#         db.commit()
        
#         # Create Annotation record
#         annotation = AnnotatedWord(
#             word_id=word.word_id,
#             image_id=image_id,
#             label_id=label.id,
#         )
#         db.add(annotation)
#         db.commit()
        
#         added_annotations.append({
#             "annotation_id": annotation.id,
#             "word_id": word.word_id,
#             "word_text": word.text,
#             "label_id": label.id,
#             "label_name": label.name
#         })

#     # Return results for this specific image
#     return {
#         "image_id": image_id,
#         "folder_id": folder_id,
#         "annotations_added": len(added_annotations),
#         "annotations": added_annotations
#     }

# @router.get("/annotation/{folder_id}")
# def get_annotations(
#     folder_id: int, db: Session = Depends(get_db)
# ):
#     folder = db.query(Folder).filter(Folder.id == folder_id).first()
#     if not folder:
#         raise HTTPException(status_code=404, detail="Folder not found")
    
#     images = db.query(Image).filter(Image.folder_id == folder_id).all()
#     if not images:
#         raise HTTPException(status_code=404, detail="No images found in the folder")

#     image_ids = [image.id for image in images]

#     annotated_words = db.query(AnnotatedWord).filter(AnnotatedWord.image_id.in_(image_ids)).all()

#     response_data = [
#         {
#             "id": annotated_word.id,
#             "image_id": annotated_word.image_id,
#             "word_id": annotated_word.word_id,
#             "word": annotated_word.word.text,
#             "label_id": annotated_word.label_id,
#             "label": annotated_word.label.name
#         }
#         for annotated_word in annotated_words
#     ]

#     return response_data


# @router.post("/annotation/{folder_id}")
# def post_annotation(
#     folder_id: int,
#     db: Session = Depends(get_db),
# ):
#     folder = db.query(Folder).filter(Folder.id == folder_id).first()
#     if not folder:
#         raise HTTPException(status_code=404, detail="Folder not found")
    
#     images = db.query(Image).filter(Image.folder_id == folder_id).all()
#     if not images:
#         raise HTTPException(status_code=404, detail="No images found in the folder")

#     for image in images:

#         file_path = "uploaded_images/" + image.name
#         key_value = extract_keyvalue(file_path, image.id)

#         for item in key_value:
#             word = OCR(
#                 text=item["value"],
#                 posx_0=item["value_bbox"][0],
#                 posy_0=item["value_bbox"][1],
#                 posx_1=item["value_bbox"][2],
#                 posy_1=item["value_bbox"][3],
#                 image_id=image.id,
#             )
#             db.add(word)
#             db.commit()  # Ensures the ID is generated
#             word_id = word.word_id  # Fetch the newly assigned ID

#             label = Label(
#                 name=item["key"],
#                 posx_0=item["key_bbox"][0],
#                 posy_0=item["key_bbox"][1],
#                 posx_1=item["key_bbox"][2],
#                 posy_1=item["key_bbox"][3],
#                 image_id=image.id,
#             )
#             db.add(label)
#             db.commit()
#             label_id = label.id

#             annotation = AnnotatedWord(
#                 word_id=word_id,
#                 image_id=image.id,
#                 label_id=label_id,
#             )
#             db.add(annotation)
#             db.commit()

#     # Return results for all images in the folder
#     ocr_results = db.query(OCR).filter(OCR.image_id.in_([image.id for image in images])).all()
#     label_results = db.query(Label).filter(Label.image_id.in_([image.id for image in images])).all()
#     annotation_results = db.query(AnnotatedWord).filter(AnnotatedWord.image_id.in_([image.id for image in images])).all()

#     return {
#         "OCR": ocr_results,
#         "Labels": label_results,
#         "Annotations": annotation_results
#     }

    
