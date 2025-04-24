import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database
from app import Base  # Import Base from FastAPI API

# Database Config
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "1234"
POSTGRES_DB = "TestMovie"
POSTGRES_HOST = "localhost"
POSTGRES_PORT = "5432"
CSV_FILE_PATH = "backend/imdb-movies-dataset.csv"

# Create Database URI
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Connect to PostgreSQL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Auto-create the database if it doesn’t exist
if not database_exists(engine.url):
    create_database(engine.url)
    print(f"✅ Database '{POSTGRES_DB}' created!")

# Create tables based on FastAPI models
Base.metadata.create_all(engine)
print("✅ Database tables created successfully!")

# Read CSV file
df = pd.read_csv(CSV_FILE_PATH)

# Convert column names to lowercase and replace spaces with underscores (PostgreSQL best practice)
df.columns = [col.lower().replace(" ", "_") for col in df.columns]

# Insert data into PostgreSQL without replacing the table
df.to_sql("movies", engine, if_exists="append", index=False, chunksize=1000)

print("✅ Data successfully loaded into 'movies' table!")
