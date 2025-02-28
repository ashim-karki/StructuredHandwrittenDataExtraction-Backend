from fastapi import APIRouter, Depends, HTTPException
from db.data_access import get_db
from sqlalchemy.orm import Session

from routes.common.keyvalue_extraction import extract_keyvalue

from blueprints import AnnotatedWord, Folder, Image, Label, OCR

router = APIRouter()

@router.get("/annotation/{folder_id}")
def get_annotations(
    folder_id: int, db: Session = Depends(get_db)
):
    folder = db.query(Folder).filter(Folder.id == folder_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    images = db.query(Image).filter(Image.folder_id == folder_id).all()
    if not images:
        raise HTTPException(status_code=404, detail="No images found in the folder")

    image_ids = [image.id for image in images]

    annotated_words = db.query(AnnotatedWord).filter(AnnotatedWord.image_id.in_(image_ids)).all()

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

    return response_data


@router.post("/annotation/{folder_id}")
def post_annotation(
    folder_id: int,
    db: Session = Depends(get_db),
):
    folder = db.query(Folder).filter(Folder.id == folder_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    images = db.query(Image).filter(Image.folder_id == folder_id).all()
    if not images:
        raise HTTPException(status_code=404, detail="No images found in the folder")

    for image in images:

        file_path = "uploaded_images/" + image.name
        key_value = extract_keyvalue(file_path, image.id)

        for item in key_value:
            word = OCR(
                text=item["value"],
                posx_0=item["value_bbox"][0],
                posy_0=item["value_bbox"][1],
                posx_1=item["value_bbox"][2],
                posy_1=item["value_bbox"][3],
                image_id=image.id,
            )
            db.add(word)
            db.commit()  # Ensures the ID is generated
            word_id = word.word_id  # Fetch the newly assigned ID

            label = Label(
                name=item["key"],
                posx_0=item["key_bbox"][0],
                posy_0=item["key_bbox"][1],
                posx_1=item["key_bbox"][2],
                posy_1=item["key_bbox"][3],
                image_id=image.id,
            )
            db.add(label)
            db.commit()
            label_id = label.id

            annotation = AnnotatedWord(
                word_id=word_id,
                image_id=image.id,
                label_id=label_id,
            )
            db.add(annotation)
            db.commit()

    # Return results for all images in the folder
    ocr_results = db.query(OCR).filter(OCR.image_id.in_([image.id for image in images])).all()
    label_results = db.query(Label).filter(Label.image_id.in_([image.id for image in images])).all()
    annotation_results = db.query(AnnotatedWord).filter(AnnotatedWord.image_id.in_([image.id for image in images])).all()

    return {
        "OCR": ocr_results,
        "Labels": label_results,
        "Annotations": annotation_results
    }

    
