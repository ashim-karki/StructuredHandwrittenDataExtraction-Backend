from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, ForeignKey
from db.data_access import Base
from sqlalchemy.orm import relationship

class OCR(Base):
    __tablename__ = "ocr"

    word_id = Column(Integer, primary_key=True, index=True)
    text = Column(String)

    # top left and bottom right position for bounding box
    posx_0 = Column(Integer)
    posy_0 = Column(Integer)
    posx_1 = Column(Integer)
    posy_1 = Column(Integer)

    image_id = Column(Integer, ForeignKey("images.id", ondelete="CASCADE"))
    # image = relationship("Image", back_populates="words")
    annotation = relationship("AnnotatedWord", back_populates="word")
    created_at = Column(DateTime, server_default=func.now())

    # representation when we want to print the database output
    # otherwise the output will be of form <blueprints.ocr.OCR object at 0xffff5b3a16c0>
    def __repr__(self):
        return (
            f"<OCR(word_id={self.word_id}, text='{self.text}', "
            f"pos=({self.posx_0}, {self.posy_0}, {self.posx_1}, {self.posy_1}), "
            f"image_id={self.image_id})>"
        )