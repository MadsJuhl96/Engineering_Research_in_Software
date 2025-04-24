import pandas as pd
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.orm import sessionmaker
from models import Base, engine  # ✅ Import models and engine

# CSV File Path
CSV_FILE_PATH = "backend/imdb-movies-dataset.csv"

# Auto-create the database if it doesn’t exist
if not database_exists(engine.url):
    create_database(engine.url)
    print(f"✅ Database 'TestMovie' created!")

# Create tables from models.py
Base.metadata.create_all(engine)
print("✅ Database tables created successfully!")

# Read CSV file
df = pd.read_csv(CSV_FILE_PATH)

# Convert column names to lowercase and replace spaces with underscores (PostgreSQL best practice)
df.columns = [col.lower().replace(" ", "_") for col in df.columns]

# Insert data into PostgreSQL
df.to_sql("movies", engine, if_exists="append", index=False, chunksize=1000)

print("✅ Data successfully loaded into 'movies' table!")
