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
    __tablename__ = 'movies'  # This matches the table name used in setup_database.py
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
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
@app.route('/movies/<int:id>', methods=['GET'])
def get_movie(id):
    movie = Movie.query.get(id)
    if not movie:
        return jsonify({"error": "Movie not found"}), 404
    return jsonify({"id": movie.id, "title": movie.title, "year": movie.year, "rating": movie.rating, "genre": movie.genre})

# Route to add a new movie
@app.route('/movies', methods=['POST'])
def add_movie():
    data = request.json
    new_movie = Movie(title=data['title'], year=data['year'], rating=data.get('rating'), genre=data.get('genre'))
    db.session.add(new_movie)
    db.session.commit()
    return jsonify({"message": "Movie added!", "movie": {"id": new_movie.id, "title": new_movie.title}}), 201

# Route to update an existing movie
@app.route('/movies/<int:id>', methods=['PUT'])
def update_movie(id):
    movie = Movie.query.get(id)
    if not movie:
        return jsonify({"error": "Movie not found"}), 404

    data = request.json
    movie.title = data.get('title', movie.title)
    movie.year = data.get('year', movie.year)
    movie.rating = data.get('rating', movie.rating)
    movie.genre = data.get('genre', movie.genre)

    db.session.commit()
    return jsonify({"message": "Movie updated!", "movie": {"id": movie.id, "title": movie.title}})

# Route to delete a movie
@app.route('/movies/<int:id>', methods=['DELETE'])
def delete_movie(id):
    movie = Movie.query.get(id)
    if not movie:
        return jsonify({"error": "Movie not found"}), 404

    db.session.delete(movie)
    db.session.commit()
    return jsonify({"message": "Movie deleted!"})

if __name__ == '__main__':
    app.run(debug=True)
