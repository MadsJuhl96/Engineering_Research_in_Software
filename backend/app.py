from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import Column, Integer, String, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
from cachetools import TTLCache
from typing import Dict, Any
import json
import time
import numpy as np
from PIL import Image, ImageFilter
import io
from operator import itemgetter

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

# In-memory TTL cache (max 100 items, 60 seconds TTL)
movie_cache = TTLCache(maxsize=100, ttl=10)
derived_cache = TTLCache(maxsize=10, ttl=10)

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


def simulate_image_processing(num_images: int = 20, image_size=(5000, 5000)):
    for _ in range(num_images):
        # Create a fake image (random noise)
        array = np.random.randint(0, 256, image_size + (3,), dtype=np.uint8)
        img = Image.fromarray(array)

        # Simulate CPU work: apply filters, resize, convert
        img = img.filter(ImageFilter.GaussianBlur(2))
        img = img.resize((256, 256))
        buf = io.BytesIO()
        img.save(buf, format='JPEG')  # Simulate encoding

@app.get("/")
def index():
    return {"message": "Welcome to the FastAPI backend"}



@app.get("/movies")
def get_movies(db: Session = Depends(get_db)):
    start_time = time.perf_counter()

    if "all_movies" in movie_cache:
        duration = time.perf_counter() - start_time
        return {
            "source": "memory_cache",
            "duration_seconds": round(duration, 3),
            "movies": movie_cache["all_movies"]
        }

    movies = db.query(Movie).all()
    movies_data = jsonable_encoder(movies)

    # Simulate image processing
    simulate_image_processing(num_images=5)

    movie_cache["all_movies"] = movies_data
    duration = time.perf_counter() - start_time
    return {
        "source": "database",
        "duration_seconds": round(duration, 3),
        "movies": movies_data
    }


@app.get("/movies/top10")
def get_top_10_movies(db: Session = Depends(get_db)):
    if "top_10" in derived_cache:
        return {"source": "derived_cache", "movies": derived_cache["top_10"]}

    # Use existing full movie cache if available
    if "all_movies" in movie_cache:
        all_movies = movie_cache["all_movies"]
    else:
        all_movies = db.query(Movie).all()
        all_movies = jsonable_encoder(all_movies)
        movie_cache["all_movies"] = all_movies

    # Derive data
    top_10 = sorted(
    [m for m in all_movies if m["rating"] is not None],
    key=itemgetter("rating"),
    reverse=True
)[:10]
    derived_cache["top_10"] = top_10

    return {"source": "computed", "movies": top_10}

@app.get("/movies/{title}")
def get_movie(title: str, db: Session = Depends(get_db)):
    cache_key = f"movie:{title}"

    if cache_key in movie_cache:
        return {"source": "memory_cache", "movie": movie_cache[cache_key]}

    movie = db.query(Movie).filter(Movie.title == title).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    movie_data = {
        "title": movie.title,
        "year": movie.year,
        "rating": movie.rating,
        "genre": movie.genre
    }

    movie_cache[cache_key] = movie_data
    return {"source": "database", "movie": movie_data}

@app.post("/movies", status_code=201)
def add_movie(movie: MovieSchema, db: Session = Depends(get_db)):
    new_movie = Movie(**movie.model_dump())
    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)

    # Invalidate cache
    movie_cache.pop("all_movies", None)

    return {"message": "Movie added!", "movie": new_movie}

@app.put("/movies/{title}")
def update_movie(title: str, updated_movie: MovieSchema, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.title == title).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    for key, value in updated_movie.model_dump(exclude_unset=True).items():
        setattr(movie, key, value)

    db.commit()

    # Invalidate relevant caches
    movie_cache.pop("all_movies", None)
    movie_cache.pop(f"movie:{title}", None)

    return {"message": "Movie updated!", "movie": movie}

@app.delete("/movies/{title}")
def delete_movie(title: str, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.title == title).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    db.delete(movie)
    db.commit()

    # Invalidate relevant caches
    movie_cache.pop("all_movies", None)
    movie_cache.pop(f"movie:{title}", None)

    return {"message": "Movie deleted!"}

# Create tables
Base.metadata.create_all(engine)
