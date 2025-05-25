from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from typing import List, Optional
import time
import random
import numpy as np
from PIL import Image, ImageFilter
import io

from database import SessionLocal
from cache import movie_cache, derived_cache
from models import Movie, MovieSchema


router = APIRouter()

# DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Simulate heavy processing
def simulate_image_processing(num_images: int = 5, image_size=(5000, 5000)):
    for _ in range(num_images):
        array = np.random.randint(0, 256, image_size + (3,), dtype=np.uint8)
        img = Image.fromarray(array)
        img = img.filter(ImageFilter.GaussianBlur(2))
        img = img.resize((256, 256))
        buf = io.BytesIO()
        img.save(buf, format='JPEG')

@router.get("/")
def index():
    return {"message": "Welcome to the FastAPI backend"}

@router.get("/movies")
def get_movies(db: Session = Depends(get_db)):
    start_time = time.perf_counter()
    cached = movie_cache.get("all_movies")
    if cached:
        duration = time.perf_counter() - start_time
        return {"source": "memory_cache", "duration_seconds": round(duration, 3), "movies": cached}
    movies = db.query(Movie).all()
    movies_data = jsonable_encoder(movies)
    simulate_image_processing()
    movie_cache.set("all_movies", movies_data, compute_cost=1.5)
    duration = time.perf_counter() - start_time
    return {"source": "database", "duration_seconds": round(duration, 3), "movies": movies_data}

@router.get("/movies/derived/top10")
def get_top10_cached():
    cached_top10 = derived_cache.get("top_10")
    if cached_top10:
        return {"source": "derived_cache", "movies": cached_top10}

    all_movies = [movie_cache.get(k) for k in movie_cache.cache.keys() if k.startswith("movie:")]
    all_movies = [m for m in all_movies if isinstance(m, dict) and m.get("rating") is not None]


    top_10 = sorted(all_movies, key=lambda m: m["rating"], reverse=True)[:10]
    derived_cache.set("top_10", top_10, compute_cost=2.0, size=1.0)
    return {"source": "computed", "movies": top_10}

@router.get("/movies/{title}")
def get_movie(title: str, db: Session = Depends(get_db)):
    key = f"movie:{title}"
    cached = movie_cache.get(key)
    if cached:
        return {"source": "memory_cache", "movie": cached}
    movie = db.query(Movie).filter(Movie.title == title).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    movie_data = jsonable_encoder(movie)
    movie_cache.set(key, movie_data)
    return {"source": "database", "movie": movie_data}

@router.get("/cache/stats")
def cache_stats():
    return JSONResponse(content={
        "movie_cache": movie_cache.stats(),
        "derived_cache": derived_cache.stats(),
    })



