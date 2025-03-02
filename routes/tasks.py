from fastapi import APIRouter, Depends, BackgroundTasks
from db.data_access import get_db
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from blueprints.tasks import Task, Type
from routes.common.tasks import create_task
from routes.common.tasks import background_ocr_task

router = APIRouter()

@router.get("/tasks")
def read_tasks(db: Session = Depends(get_db)):
    # get all tasks and sort by creation date
    tasks = (
        db.query(
            Task.id,
            Task.name,
            Task.description,
            Task.percentage_complete,
            Task.status,
            Task.type,
            Task.folder_id,
            # Task.imageset_id,
            # Task.model_id,
        )
        .order_by(Task.created_at.desc())
    ).all()

    # Convert list of tuples to list of dictionaries
    task_list = [
        {
            "id": t[0],
            "name": t[1],
            "description": t[2],
            "percentage_complete": t[3],
            "status": t[4],
            "type": t[5],
            "folder_id": t[6],
        }
        for t in tasks
    ]

    return task_list

class FormData(BaseModel):
    folder_id: str
    name: str
    description: str

    class Config:
        orm_mode = True

@router.post("/start_task")
def start_task(
    formdata: FormData,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    folder_id = formdata.folder_id
    name = formdata.name
    description = formdata.description
    print("here 1", folder_id)
    
    create_task(
        db,
        name,
        description,
        lambda db, folder_id: background_ocr_task(db, folder_id),
        background_tasks,
        type=Type.ocr,  # Make sure this enum exists and is imported
        folder_id=folder_id,
    )
    return {"message": "OCR task started successfully"}
    # text_extraction("/Users/ashim_karki/Desktop/MajorProject/9)MajorBackend/uploaded_images/handwritten_form.png")



@router.delete("/tasks/{task_id}")
def delete_task(
    task_id: int, db: Session = Depends(get_db)
):

    db_task = (
        db.query(Task)
        .filter(Task.id == task_id)
        .first()
    )

    if db_task:
        db.delete(db_task)
        db.commit()
        return "Task deleted"
    return f"No task with id = {task_id}"