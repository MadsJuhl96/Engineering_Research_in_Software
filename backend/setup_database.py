import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database

#Database Config
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "1234"
POSTGRES_DB = "TestMovie"
POSTGRES_HOST = "localhost"
POSTGRES_PORT = "5432"
CSV_FILE_PATH = "backend/imdb-movies-dataset.csv" 

#  Create Database URI
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Connect to PostgreSQL
engine = create_engine(DATABASE_URL)

# Auto-create the database if it doesn’t exist
if not database_exists(engine.url):
    create_database(engine.url)
    print(f"Database '{POSTGRES_DB}' created!")
else:
    print(f"Database '{POSTGRES_DB}' already exists.")

# Read CSV file
df = pd.read_csv(CSV_FILE_PATH)

# Convert column names to lowercase and replace spaces with underscores (PostgreSQL best practice)
df.columns = [col.lower().replace(" ", "_") for col in df.columns]

# Write DataFrame to PostgreSQL (automatically creates table)
df.to_sql("movies", engine, if_exists="replace", index=False)

print("✅ Data successfully loaded into 'movies' table!")
