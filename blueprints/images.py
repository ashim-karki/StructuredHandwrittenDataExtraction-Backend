from sqlalchemy import Column, Integer, String, Enum, DateTime, func, ForeignKey
from db.data_access import Base, SessionLocal
from sqlalchemy.orm import relationship
from sqlalchemy import event
import os


class Image(Base):
    __tablename__ = "images" # it is common practice to use a lowercase and plural form for the table name

    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(String)
    path = Column(String)
    name = Column(String)
    size_x = Column(Integer)
    size_y = Column(Integer)

    folder_id = Column(Integer, ForeignKey("folders.id"))
    folder = relationship("Folder", back_populates="images")

    # words = relationship("OCR", back_populates="image")

    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"Image(id={self.id},  path={self.path})"


def delete_image_on_db_record_delete(target):
    if target.path and os.path.exists("uploaded_images/" + target.path):
        os.remove("uploaded_images/" + target.path)


def before_flush(session, flush_context, instances):
    for instance in session.deleted:
        if isinstance(instance, Image):
            delete_image_on_db_record_delete(instance)


event.listen(SessionLocal, "before_flush", before_flush)
