from starlette.middleware.cors import CORSMiddleware
from fastapi import Depends, FastAPI
from db.data_access import Base, engine

from routes.folders import router as folders_router
from routes.images import router as images_router
from routes.annotation import router as annotation_router

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

@app.get("/")
async def hello():
    return {"msg": "Hello, Structured Handwritten Data Extraction API is live!"}