# # app.py
# from fastapi import FastAPI, HTTPException, Depends
# from sqlalchemy import Column, Integer, String, Float, create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker, Session
# from pydantic import BaseModel
# from fastapi.encoders import jsonable_encoder
# from typing import Optional
# import time
# import numpy as np
# from PIL import Image, ImageFilter
# import io
# import random
# from ml_cache import RuleBasedCache

# # Database configuration
# POSTGRES_USER = "postgres"
# POSTGRES_PASSWORD = "1234"
# POSTGRES_DB = "TestMovie"
# POSTGRES_HOST = "localhost"
# POSTGRES_PORT = "5432"
# DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# # SQLAlchemy setup
# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()

# # FastAPI instance
# app = FastAPI()

# # Rule-based caches
# movie_cache = RuleBasedCache(maxsize=100)
# derived_cache = RuleBasedCache(maxsize=10)

# # SQLAlchemy Movie model
# class Movie(Base):
#     __tablename__ = "movies"
#     title = Column(String(255), primary_key=True)
#     year = Column(Integer, nullable=False)
#     rating = Column(Float)
#     genre = Column(String(50))

# # Pydantic schema
# class MovieSchema(BaseModel):
#     title: str
#     year: int
#     rating: Optional[float] = None
#     genre: Optional[str] = None

# # DB session dependency
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# # Simulate expensive image processing
# def simulate_image_processing(num_images: int = 5, image_size=(5000, 5000)):
#     for _ in range(num_images):
#         array = np.random.randint(0, 256, image_size + (3,), dtype=np.uint8)
#         img = Image.fromarray(array)
#         img = img.filter(ImageFilter.GaussianBlur(2))
#         img = img.resize((256, 256))
#         buf = io.BytesIO()
#         img.save(buf, format='JPEG')

# @app.on_event("startup")
# def fill_cache_with_movies():
#     db = SessionLocal()
#     try:
#         movies = db.query(Movie).all()
#         print(f"[Startup] Caching {len(movies)} movies individually...")
#         for movie in movies:
#             key = f"movie:{movie.title}"
#             compute_cost = random.uniform(1.0, 5.0)
#             size = random.uniform(0.5, 3.0)
#             movie_cache.set(key, jsonable_encoder(movie), compute_cost=compute_cost, size=size)
#         print("[Startup] Finished caching individual movies.")
#     finally:
#         db.close()

# @app.get("/")
# def index():
#     return {"message": "Welcome to the FastAPI backend"}

# @app.get("/movies")
# def get_movies(db: Session = Depends(get_db)):
#     start_time = time.perf_counter()
#     cached = movie_cache.get("all_movies")
#     if cached:
#         duration = time.perf_counter() - start_time
#         return {"source": "memory_cache", "duration_seconds": round(duration, 3), "movies": cached}
#     movies = db.query(Movie).all()
#     movies_data = jsonable_encoder(movies)
#     simulate_image_processing()
#     movie_cache.set("all_movies", movies_data, compute_cost=1.5)
#     duration = time.perf_counter() - start_time
#     return {"source": "database", "duration_seconds": round(duration, 3), "movies": movies_data}

# @app.get("/movies/derived/top10")
# def get_top10_cached():
#     cached_top10 = derived_cache.get("top_10")
#     if cached_top10:
#         return {"source": "derived_cache", "movies": cached_top10}

#     all_movies = [movie_cache.get(k) for k in movie_cache.cache.keys() if k.startswith("movie:")]
#     all_movies = [m for m in all_movies if m and m.get("rating") is not None]

#     top_10 = sorted(all_movies, key=lambda m: m["rating"], reverse=True)[:10]
#     derived_cache.set("top_10", top_10, compute_cost=2.0, size=1.0)
#     return {"source": "computed", "movies": top_10}

# @app.get("/movies/derived/by-genre")
# def get_movies_by_genre():
#     cache_key = "by_genre"
#     cached = derived_cache.get(cache_key)
#     if cached:
#         return {"source": "derived_cache", "data": cached}

#     all_movies = [movie_cache.get(k) for k in movie_cache.cache.keys() if k.startswith("movie:")]
#     genre_groups = {}
#     for m in all_movies:
#         if m and m.get("genre"):
#             genre_groups.setdefault(m["genre"], []).append(m["title"])
#     derived_cache.set(cache_key, genre_groups, compute_cost=2.5, size=2.0)
#     return {"source": "computed", "data": genre_groups}

# @app.get("/movies/{title}")
# def get_movie(title: str, db: Session = Depends(get_db)):
#     key = f"movie:{title}"
#     cached = movie_cache.get(key)
#     if cached:
#         return {"source": "memory_cache", "movie": cached}
#     movie = db.query(Movie).filter(Movie.title == title).first()
#     if not movie:
#         raise HTTPException(status_code=404, detail="Movie not found")
#     movie_data = jsonable_encoder(movie)
#     movie_cache.set(key, movie_data)
#     return {"source": "database", "movie": movie_data}

# @app.get("/cache/stats")
# def cache_stats():
#     return {
#         "movie_cache": movie_cache.stats(),
#         "derived_cache": derived_cache.stats()
#     }

# @app.post("/simulate-access")
# def simulate_random_accesses(n: int = 20):
#     keys = list(movie_cache.cache.keys())
#     for _ in range(n):
#         if keys:
#             k = random.choice(keys)
#             movie_cache.get(k)
#     return {"message": f"{n} random cache accesses simulated."}

# Base.metadata.create_all(engine)



# from fastapi.responses import HTMLResponse
# import json

# @app.get("/dashboard", response_class=HTMLResponse)
# def dashboard():
#     html = """
#     <!DOCTYPE html>
#     <html>
#     <head>
#         <title>Cache Dashboard</title>
#         <style>
#             body { font-family: Arial; margin: 2rem; background: #f9f9f9; }
#             h1 { color: #333; }
#             table { border-collapse: collapse; width: 100%; margin-bottom: 2rem; }
#             th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
#             th { background-color: #eee; }
#             .section { margin-bottom: 3rem; }
#             .timestamp { color: #777; font-size: 0.9em; }
#         </style>
#     </head>
#     <body>
#         <h1>📊 Cache Metrics Dashboard</h1>

#         <div class="section">
#             <h2>🎬 Movie Cache</h2>
#             <table id="movieCache">
#                 <thead><tr><th>Key</th><th>Hits</th><th>Cost</th><th>Size</th><th>Last Access</th></tr></thead>
#                 <tbody></tbody>
#             </table>
#         </div>

#         <div class="section">
#             <h2>🧠 Derived Cache</h2>
#             <table id="derivedCache">
#                 <thead><tr><th>Key</th><th>Hits</th><th>Cost</th><th>Size</th><th>Last Access</th></tr></thead>
#                 <tbody></tbody>
#             </table>
#         </div>

#         <div class="timestamp" id="lastUpdate">⏱️ Loading...</div>

#         <script>
#             async function fetchData() {
#                 const res = await fetch("/cache/stats");
#                 const data = await res.json();

#                 function renderTable(id, cacheData) {
#                     const tbody = document.querySelector(`#${id} tbody`);
#                     tbody.innerHTML = "";
#                     for (const [key, meta] of Object.entries(cacheData.entries || {})) {
#                         const row = document.createElement("tr");
#                         row.innerHTML = `
#                             <td>${key}</td>
#                             <td>${meta.hits}</td>
#                             <td>${meta.compute_cost.toFixed(2)}</td>
#                             <td>${meta.size.toFixed(2)}</td>
#                             <td>${new Date(meta.last_accessed * 1000).toLocaleTimeString()}</td>
#                         `;
#                         tbody.appendChild(row);
#                     }
#                 }

#                 renderTable("movieCache", data.movie_cache);
#                 renderTable("derivedCache", data.derived_cache);
#                 document.getElementById("lastUpdate").innerText = "⏱️ Updated: " + new Date().toLocaleTimeString();
#             }

#             fetchData();
#             setInterval(fetchData, 5000);
#         </script>
#     </body>
#     </html>
#     """
#     return HTMLResponse(content=html)

