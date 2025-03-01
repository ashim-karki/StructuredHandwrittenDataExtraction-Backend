from blueprints import Task, Status
import logging
from db.data_access import get_db
from fastapi import BackgroundTasks
from db.data_access import get_db
from blueprints import OCR
from routes.common.folder2image import get_images_from_folder
from routes.common.temp_ocr import apply_ocr

def background_ocr_task(db, folder_id):
    """Modified to accept a db session and folder_id instead of images"""
    # Get images with the active session
    images = get_images_from_folder(db, folder_id)
    total_images = len(images)
    
    print(total_images)

    if total_images == 0:
        yield 100  # Nothing to process
        return
    
    ocred_words = []
    for i, image in enumerate(images):
        # Explicitly query for words instead of using lazy loading
        words = db.query(OCR).filter(OCR.image_id == image.id).all()
        if words:  # Using words directly instead of len(image.words)
            yield (i + 1) / total_images * 100
        else:
            bboxes = apply_ocr(
                image.path,
                "",
                write_to_file=False,
                normalize_bbox=True,
            )
            for item in bboxes:
                if item["value"] == "":
                    continue
                ocred_words.append(
                    OCR(
                        text=item["value"],
                        posx_0=item["bbox"][0],
                        posy_0=item["bbox"][1],
                        posx_1=item["bbox"][2],
                        posy_1=item["bbox"][3],
                        image_id=image.id,
                    )
                )
            
            if ocred_words:  # Only commit if there are words to add
                db.add_all(ocred_words)
                db.commit()
                ocred_words = []  # Reset for next batch
                
            yield (i + 1) / total_images * 100

def periodic_task_updater(db_factory, task_id, task_func):
    """
    Use a factory function to create new db sessions for the background task.
    Track task by ID instead of object reference.
    """
    # Create a new session for this background process
    db = db_factory()  # Call the factory to get a session
    try:
        # Retrieve the task by ID using the new session
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            logging.error(f"Task with ID {task_id} not found")
            return
            
        for percentage_complete in task_func(db):  # Pass db session to task_func
            task.percentage_complete = percentage_complete
            if task.percentage_complete == 100:
                task.status = Status.completed
            db.commit()
    except Exception as e:
        logging.error(f"Background task failed: {e}")
        # Only set status to failed if task was found
        if 'task' in locals():
            task.status = Status.failed
            db.commit()
        raise e
    finally:
        # Always close the db session when done
        db.close()

def create_task(
    db,
    name,
    description,
    task_func,
    background_tasks: BackgroundTasks,
    type,
    folder_id,
):
    task = Task(
        name=name,
        description=description,
        percentage_complete=0,
        status=Status.running,
        type=type,
        folder_id=folder_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # Pass the get_db function directly as the factory
    background_tasks.add_task(
        periodic_task_updater, 
        db_factory=get_db,  # Function that returns a new DB session when called
        task_id=task.id,
        task_func=lambda db: background_ocr_task(db, folder_id)
    )