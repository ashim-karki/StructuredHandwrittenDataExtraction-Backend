# labels referes to the fields that we would want to extract from the reciepts
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, ForeignKey
from db.data_access import Base
from sqlalchemy.orm import relationship


class Label(Base):
    __tablename__ = "labels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)

    # imageset_id = Column(Integer, ForeignKey("ImageSet.id", ondelete="CASCADE"))
    # model_id = Column(Integer, ForeignKey("Model.id", ondelete="CASCADE"))
    # image_set = relationship("ImageSet", back_populates="labels")
    # model = relationship("Model", back_populates="labels")

    # top left and bottom right position for bounding box
    posx_0 = Column(Integer)
    posy_0 = Column(Integer)
    posx_1 = Column(Integer)
    posy_1 = Column(Integer)

    image_id = Column(Integer, ForeignKey("images.id", ondelete="CASCADE"))

    created_at = Column(DateTime, server_default=func.now())
    annotated_words = relationship("AnnotatedWord", back_populates="label")
    
    # key_information = relationship("KeyInformation", back_populates="label")

    def __repr__(self):
        return f"Label(id={self.id}, name={self.name}, annotated words={self.annotated_words}\n)"
