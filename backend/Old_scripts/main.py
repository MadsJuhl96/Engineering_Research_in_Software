# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from endpoints import router
from database import engine, Base
from cache import movie_cache
from dashboard import router as dashboard_router
from models import preload_cache, start_stress_simulation

app = FastAPI()

app.include_router(router)
app.include_router(dashboard_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    preload_cache()
    start_stress_simulation()

@app.get("/")
def root():
    return {"message": "Movie API with optional caching is running."}
