from fastapi import FastAPI
from database import Base, engine

from cache import movie_cache
from endpoints import router as api_router
from dashboard import router as dashboard_router
from models import Movie
from sqlalchemy.orm import Session

app = FastAPI()

# Create tables
Base.metadata.create_all(bind=engine)

# Startup event to fill movie_cache
@app.on_event("startup")
def fill_cache():
    db = Session(bind=engine)
    try:
        movies = db.query(Movie).all()
        for movie in movies:
            key = f"movie:{movie.title}"
            movie_cache.set(key, movie)
    finally:
        db.close()

# Include routers
app.include_router(api_router)
app.include_router(dashboard_router)
