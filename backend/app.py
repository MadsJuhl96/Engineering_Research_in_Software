from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import Column, Integer, String, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
import json
import time

# Database Configuration
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "1234"
POSTGRES_DB = "TestMovie"
POSTGRES_HOST = "localhost"
POSTGRES_PORT = "5432"

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# FastAPI instance
app = FastAPI()

# SQLAlchemy Movie Model
class Movie(Base):
    __tablename__ = "movies"
    title = Column(String(255), primary_key=True)
    year = Column(Integer, nullable=False)
    rating = Column(Float)
    genre = Column(String(50))

# Pydantic Schema
class MovieSchema(BaseModel):
    title: str
    year: int
    rating: float | None = None
    genre: str | None = None

# DB session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Simple in-memory cache ---
cache_movies = {}
cache_single_movie = {}
CACHE_TTL = 3600  # 1 hour

def is_cache_valid(cache_item):
    return cache_item and (time.time() - cache_item["timestamp"] < CACHE_TTL)

@app.get("/")
def index():
    return {"message": "Welcome to the FastAPI backend"}

@app.get("/movies")
def get_movies(db: Session = Depends(get_db)):
    if is_cache_valid(cache_movies.get("all_movies")):
        return {"source": "memory", "movies": cache_movies["all_movies"]["data"]}

    movies = db.query(Movie).all()
    movies_data = jsonable_encoder(movies)

    # Cache the result
    cache_movies["all_movies"] = {
        "timestamp": time.time(),
        "data": movies_data
    }

    return {"source": "database", "movies": movies_data}

@app.get("/movies/{title}")
def get_movie(title: str, db: Session = Depends(get_db)):
    if is_cache_valid(cache_single_movie.get(title)):
        return {"source": "memory", "movie": cache_single_movie[title]["data"]}

    movie = db.query(Movie).filter(Movie.title == title).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    movie_data = {
        "title": movie.title,
        "year": movie.year,
        "rating": movie.rating,
        "genre": movie.genre
    }

    cache_single_movie[title] = {
        "timestamp": time.time(),
        "data": movie_data
    }

    return {"source": "database", "movie": movie_data}

@app.post("/movies", status_code=201)
def add_movie(movie: MovieSchema, db: Session = Depends(get_db)):
    new_movie = Movie(**movie.model_dump())
    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)

    # Invalidate caches
    cache_movies.pop("all_movies", None)
    cache_single_movie.pop(new_movie.title, None)

    return {"message": "Movie added!", "movie": new_movie}

@app.put("/movies/{title}")
def update_movie(title: str, updated_movie: MovieSchema, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.title == title).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    for key, value in updated_movie.model_dump(exclude_unset=True).items():
        setattr(movie, key, value)

    db.commit()

    # Invalidate caches
    cache_movies.pop("all_movies", None)
    cache_single_movie.pop(title, None)

    return {"message": "Movie updated!", "movie": movie}

@app.delete("/movies/{title}")
def delete_movie(title: str, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.title == title).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    db.delete(movie)
    db.commit()

    # Invalidate caches
    cache_movies.pop("all_movies", None)
    cache_single_movie.pop(title, None)

    return {"message": "Movie deleted!"}

# Create tables
Base.metadata.create_all(engine)
