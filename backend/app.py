from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Database configuration (this matches your setup in setup_database.py)
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "1234"
POSTGRES_DB = "TestMovie"
POSTGRES_HOST = "localhost"
POSTGRES_PORT = "5432"

# SQLAlchemy database URI (matches the one in setup_database.py)
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # To avoid warnings

# Initialize the SQLAlchemy instance
db = SQLAlchemy(app)

# Movie Model (this will interact with the 'movies' table created in the database)
class Movie(db.Model):
    __tablename__ = 'movies'  
    title = db.Column(db.String(255), primary_key=True)  # Use title as the primary key
    year = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Float)
    genre = db.Column(db.String(50))

    def __repr__(self):
        return f"<Movie {self.title}>"


@app.route('/', methods=['GET'])
def index():
    return "Welcome to the backend"


# Route to get all movies
@app.route('/movies', methods=['GET'])
def get_movies():
    movies = Movie.query.all()
    return jsonify([{
        
        "title": m.title,
        "year": m.year,
        "rating": m.rating,
        "genre": m.genre
    } for m in movies])

# Route to get a single movie by ID
@app.route('/movies/<title>', methods=['GET'])
def get_movie(title):
    movie = Movie.query.get(title)
    if not movie:
        return jsonify({"error": "Movie not found"}), 404
    return jsonify({"title": movie.title, "year": movie.year, "rating": movie.rating, "genre": movie.genre})

# Route to add a new movie
@app.route('/movies', methods=['POST'])
def add_movie():
    data = request.json
    new_movie = Movie(title=data['title'], year=data['year'], rating=data.get('rating'), genre=data.get('genre'))
    db.session.add(new_movie)
    db.session.commit()

    return jsonify({"message": "Movie added!", "movie": {"title": new_movie.title, "year": new_movie.year, "rating": new_movie.rating, "genre": new_movie.genre}}), 201

# Route to update an existing movie
@app.route('/movies/<title>', methods=['PUT'])
def update_movie(title):
    movie = Movie.query.get(title)
    if not movie:
        return jsonify({"error": "Movie not found"}), 404

    data = request.json
    movie.title = data.get('title', movie.title)
    movie.year = data.get('year', movie.year)
    movie.rating = data.get('rating', movie.rating)
    movie.genre = data.get('genre', movie.genre)

    db.session.commit()
    return jsonify({"message": "Movie Updatet!", "movie": {"title": movie.title, "year": movie.year, "rating": movie.rating, "genre": movie.genre}}), 201

# Route to delete a movie
@app.route('/movies/<title>', methods=['DELETE'])
def delete_movie(title):
    # Fetch the movie by its title (since title is the primary key)
    movie = Movie.query.get(title)
    
    if not movie:
        return jsonify({"error": "Movie not found"}), 404

    db.session.delete(movie)
    db.session.commit()
    
    return jsonify({"message": "Movie deleted!"}), 200

if __name__ == '__main__':
    app.run(debug=True)
