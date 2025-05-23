from sqlalchemy import Column, Integer, String, Float
from pydantic import BaseModel
from database import Base

class Movie(Base):
    __tablename__ = "movies"
    title = Column(String(255), primary_key=True)
    year = Column(Integer, nullable=False)
    rating = Column(Float)
    genre = Column(String(50))

class MovieSchema(BaseModel):
    title: str
    year: int
    rating: float | None = None
    genre: str | None = None

    class Config:
        orm_mode = True
