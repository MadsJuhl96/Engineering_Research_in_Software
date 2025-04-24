from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import Column, Integer, String, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from redis_client import redis_client  # Redis client
from fastapi.encoders import jsonable_encoder
import json

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

@app.get("/")
def index():
    return {"message": "Welcome to the FastAPI backend"}

@app.get("/movies")
async def get_movies(db: Session = Depends(get_db)):
    cached_movies = await redis_client.get("all_movies")

    if cached_movies:
        movies = json.loads(cached_movies)
        return {"source": "redis", "movies": movies}

    movies = db.query(Movie).all()
    movies_data = jsonable_encoder(movies)

    await redis_client.set("all_movies", json.dumps(movies_data))
    return {"source": "database", "movies": movies_data}

@app.get("/movies/{title}")
async def get_movie(title: str, db: Session = Depends(get_db)):
    # Try to get from Redis cache
    cached = await redis_client.hgetall(f"movie:{title}")
    if cached:
        return {"source": "redis", "movie": cached}
    
    # Fallback to DB
    movie = db.query(Movie).filter(Movie.title == title).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    movie_data = {
        "title": movie.title,
        "year": movie.year,
        "rating": movie.rating,
        "genre": movie.genre
    }

    # Cache it in Redis
    await redis_client.hset(f"movie:{title}", mapping=movie_data)
    await redis_client.expire(f"movie:{title}", 3600)  # Optional: 1 hour TTL

    return {"source": "database", "movie": movie_data}

@app.post("/movies", status_code=201)
def add_movie(movie: MovieSchema, db: Session = Depends(get_db)):
    new_movie = Movie(**movie.model_dump())
    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)
    return {"message": "Movie added!", "movie": new_movie}

@app.put("/movies/{title}")
def update_movie(title: str, updated_movie: MovieSchema, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.title == title).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    for key, value in updated_movie.model_dump(exclude_unset=True).items():
        setattr(movie, key, value)

    db.commit()

    # Update Redis cache
    redis_client.delete(f"movie:{title}")
    
    return {"message": "Movie updated!", "movie": movie}

@app.delete("/movies/{title}")
def delete_movie(title: str, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.title == title).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    db.delete(movie)
    db.commit()

    # Remove from Redis
    redis_client.delete(f"movie:{title}")
    
    return {"message": "Movie deleted!"}

# Create tables
Base.metadata.create_all(engine)
