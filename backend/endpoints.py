# endpoints.py
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Movie, MovieSchema
from cache import movie_cache
from generate_data import generate_derived_movies

router = APIRouter()

@router.get("/movies")
def list_movies():
    db = SessionLocal()
    try:
        movies = db.query(Movie).all()
        movies_schema = [MovieSchema.from_orm(m) for m in movies]
        return {"movies": movies_schema, "source": "db"}
    finally:
        db.close()

@router.get("/derived")
def get_derived(n: int = Query(..., gt=0, le=100)):
    key = f"derived:{n}"
    cached_result = movie_cache.get(key)
    if cached_result:
        return {"derived": cached_result, "source": "cache"}
    # recompute and cache
    derived = generate_derived_movies(n)
    movie_cache.set(key, derived, compute_cost=1.0, entry_type="derived")
    return {"derived": derived, "source": "computed"}

@router.get("/cache/stats")
def cache_stats():
    stats = movie_cache.stats()
    return JSONResponse(content=stats)
