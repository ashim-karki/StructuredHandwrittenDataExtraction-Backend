from fastapi import APIRouter, Depends
from db.data_access import get_db
from sqlalchemy.orm import Session

from routes.common.keyvalue_extraction import extract_keyvalue

from blueprints import AnnotatedWord, Folder, Image, Label, OCR

router = APIRouter()

@router.get("/annotation/{image_id}")
def get_annotation(image_id: int, db: Session = Depends(get_db)):
    annotated_words = db.query(AnnotatedWord).filter_by(image_id=image_id).all()

    # Convert ORM objects to dictionaries with correct data types
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

@router.post("/annotation/{image_id}")
def post_annotation(
    image_id: int,
    db: Session = Depends(get_db),
):
    image = db.query(Image).filter_by(id=image_id).first()
    # ocred_words = []
    # ocred_labels = []
    # ocred_annotations = []
    file_path = "uploaded_images/" + image.path
    # background_tasks.add_task(apply_ocr, file_path, "", write_to_file=False)
    key_value = extract_keyvalue()

    for item in key_value:
        word = OCR(
            text=item["value"],
            posx_0=item["value_bbox"][0],
            posy_0=item["value_bbox"][1],
            posx_1=item["value_bbox"][2],
            posy_1=item["value_bbox"][3],
            image_id=image_id,
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
            image_id=image_id,
        )
        db.add(label)
        db.commit()
        label_id = label.id

        annotation = AnnotatedWord(
            word_id=word_id,
            image_id=image_id,
            label_id=label_id,
        )
        db.add(annotation)
        db.commit()

    return {
            "OCR": db.query(OCR).filter_by(image_id=image_id).all(),
            "Labels": db.query(Label).filter_by(image_id=image_id).all(),
            "Annotations": db.query(AnnotatedWord).filter_by(image_id=image_id).all()
            }

    
