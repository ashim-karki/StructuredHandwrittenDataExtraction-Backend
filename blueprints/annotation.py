from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, ForeignKey
from db.data_access import Base
from sqlalchemy.orm import relationship

class AnnotatedWord(Base):
    __tablename__ = "annotatedword"

    id = Column(Integer, primary_key=True, index=True)
    word_id = Column(Integer, ForeignKey("ocr.word_id", ondelete="CASCADE"))
    word = relationship("OCR", back_populates="annotation")

    # imageset_id = Column(Integer, ForeignKey("ImageSet.id", ondelete="CASCADE"))
    
    image_id = Column(Integer, ForeignKey("images.id", ondelete="CASCADE"))
    label_id = Column(Integer, ForeignKey("labels.id", ondelete="CASCADE"))
    label = relationship("Label", back_populates="annotated_words")
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"AnnotationedWords(id={self.id}, word={self.word}, label_id={self.label_id}, label={self.label})"
