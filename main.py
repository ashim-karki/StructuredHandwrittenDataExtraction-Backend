from starlette.middleware.cors import CORSMiddleware
from fastapi import Depends, FastAPI
from db.data_access import Base, engine

from routes.folders import router as folders_router
from routes.images import router as images_router
from routes.annotation import router as annotation_router
from routes.tasks import router as tasks_router
from routes.key_extraction import router as key_extraction_router
from routes.export import router as export_router

from fastapi.staticfiles import StaticFiles

import tempfile
import os

# Create exports directory if it doesn't exist
EXPORT_DIR = os.path.join(tempfile.gettempdir(), "data_exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

app = FastAPI()

# If this is your first time running the app, the tables may not have been created in your database.
# You can create them by running the following command:
Base.metadata.create_all(bind=engine)

allow_all = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_all,
    allow_credentials=True,
    allow_methods=allow_all,
    allow_headers=allow_all,
)

# app.middleware("http")(logging_middleware)

app.include_router(folders_router, prefix="/api", tags=["folders"])
app.include_router(images_router, prefix="/api", tags=["images"])
app.include_router(annotation_router, prefix="/api", tags=["annotation"])
app.include_router(tasks_router, prefix="/api", tags=["tasks"])
app.include_router(key_extraction_router, prefix="/api", tags=["extraction"])
app.include_router(export_router, prefix="/api", tags=["export"])

app.mount("/static/exports", StaticFiles(directory=EXPORT_DIR), name="exports")


@app.get("/")
async def hello():
    return {"msg": "Hello, Structured Handwritten Data Extraction API is live!"}