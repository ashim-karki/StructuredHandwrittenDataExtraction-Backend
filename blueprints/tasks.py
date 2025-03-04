from sqlalchemy import Column, Integer, String, Enum, DateTime, func, ForeignKey
from sqlalchemy.schema import ForeignKeyConstraint
from db.data_access import Base
import enum


class Status(enum.Enum):
    running = 1
    completed = 2
    failed = 3


class Type(enum.Enum):
    ocr = 1
    table = 2 
    table_and_ocr = 3


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    description = Column(String)
    type = Column(Enum(Type))
    # model_id = Column(Integer, ForeignKey("Model.id", ondelete="SET NULL"))
    folder_id = Column(Integer, ForeignKey("folders.id", ondelete="SET NULL"))
    # imageset_id = Column(Integer, ForeignKey("ImageSet.id", ondelete="SET NULL"))
    status = Column(Enum(Status))
    percentage_complete = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
