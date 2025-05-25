from fastapi import FastAPI
from database import Base, engine
import logging
from cache import movie_cache
from endpoints import router as api_router
from dashboard import router as dashboard_router
from models import Movie
from sqlalchemy.orm import Session
from simulate_stress import run_simulation
import threading

app = FastAPI()
logging.basicConfig(level=logging.DEBUG)

# Create DB tables
Base.metadata.create_all(bind=engine)

@app.on_event("startup")
def fill_cache():
    db = Session(bind=engine)
    try:
        movies = db.query(Movie).all()
        for movie in movies:
            key = f"movie:{movie.title}"
            movie_cache.set(key, movie)
        print(f"✅ Preloaded {len(movies)} movies into cache")
    finally:
        db.close()

@app.on_event("startup")
def launch_simulation():
    thread = threading.Thread(target=run_simulation, args=(movie_cache,), daemon=True)
    thread.start()
    print("🚀 Cache stress simulation started in background")

# Include endpoints
app.include_router(api_router)
app.include_router(dashboard_router)
