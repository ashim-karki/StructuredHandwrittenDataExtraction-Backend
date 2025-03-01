from fastapi import BackgroundTasks
from blueprints import Task, Status
from sqlalchemy.orm import Session
import logging
from db.data_access import get_db

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

# from fastapi import BackgroundTasks
# from blueprints import Task, Status

# def periodic_task_updater(db, task, task_func):
#     try:
#         for percentage_complete in task_func():
#             task.percentage_complete = percentage_complete
#             if task.percentage_complete == 100:
#                 task.status = Status.completed
#             db.commit()
#             db.refresh(task)
#     except Exception as e:
#         print("Background task failed", e)
#         task.status = Status.failed
#         db.commit()
#         db.refresh(task)
#         raise e


# def create_task(
#     db,
#     name,
#     description,
#     task_func,
#     background_tasks: BackgroundTasks,
#     type,
#     folder_id,
#     # model_id=None,
# ):
#     task = Task(
#         name=name,
#         description=description,
#         percentage_complete=0,
#         status=Status.running,
#         type=type,
#         folder_id=folder_id,
#         # model_id=model_id,
#     )
#     db.add(task)
#     db.commit()
#     db.refresh(task)
#     background_tasks.add_task(periodic_task_updater, db, task, task_func)
