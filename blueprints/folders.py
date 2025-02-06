from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from db.data_access import Base
from sqlalchemy.orm import relationship


class Folder(Base):
    __tablename__ = "folders" # it is common practice to use a lowercase and plural form for the table name

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    user = Column(String)
    description = Column(String)
    color = Column(String)

    # delete all image if tag is deleted
    images = relationship("Image", back_populates="folder", cascade="all, delete-orphan")
    # image_sets = relationship("ImageSet", back_populates="tags")

    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"Tag(id={self.id}, name={self.name}, color={self.color})"
