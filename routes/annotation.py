from fastapi import APIRouter, Depends, HTTPException
from db.data_access import get_db
from sqlalchemy.orm import Session

from routes.common.temp_keyvalue_extraction import extract_keyvalue

from blueprints import AnnotatedWord, Folder, Image, Label, OCR

from typing import List

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
    return response_data


@router.post("/annotate/{image_id}/{folder_id}")
def post_image_annotation(
    image_id: int,
    folder_id: int,
    annotations: List[dict],  # Expecting a list of annotation objects from frontend
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
    
    for annotation in annotations:
        word_id = annotation.get("word_id")
        updated_text = annotation.get("word")  # Extract only the "word" field
        
        # Check if OCR record exists and update
        word = db.query(OCR).filter(OCR.word_id == word_id, OCR.image_id == image.id).first()
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
        annotation_record = db.query(AnnotatedWord).filter(
            AnnotatedWord.word_id == word.word_id,
            AnnotatedWord.image_id == image.id
        ).first()
        if not annotation_record:
            annotation_record = AnnotatedWord(
                word_id=word.word_id,
                image_id=image.id,
                label_id=None  # Adjust as needed
            )
            db.add(annotation_record)
        db.commit()
        db.refresh(annotation_record)
    
    return {"message": "Annotations successfully added or updated"}
