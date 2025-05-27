# models.py
from sqlalchemy import Column, Integer, String, Float
from pydantic import BaseModel
from typing import Optional
from database import Base

class Movie(Base):
    __tablename__ = "movies"
    title = Column(String(255), primary_key=True)
    year = Column(Integer, nullable=False)
    rating = Column(Float, nullable=True)
    genre = Column(String(50), nullable=True)

class MovieSchema(BaseModel):
    title: str
    year: Optional[int] = None
    rating: Optional[float] = None
    genre: Optional[str] = None

    class Config:
        orm_mode = True
