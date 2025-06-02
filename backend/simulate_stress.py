import time
import random
import json
from datetime import datetime, timedelta
from sqlalchemy.sql import func
from models import Movie
from database import SessionLocal
from cache import movie_cache

POPULAR_N = [50, 100, 150, 200, 250, 300, 350, 400, 222, 1000, 900, 800, 700, 600, 576, 459]

def sort_by_year(movies, descending=True):
    return sorted(movies, key=lambda m: m['year'], reverse=descending)

def sort_by_title(movies, descending=False):
    return sorted(movies, key=lambda m: m['title'], reverse=descending)

def generate_derived_movies(n, order_by_rating=True, order_by_year=False, order_by_title=False):
    session = SessionLocal()
    try:
        query = session.query(Movie)
        if order_by_rating:
            query = query.order_by(Movie.rating.desc())
        elif order_by_year:
            query = query.order_by(Movie.year.desc())
        elif order_by_title:
            query = query.order_by(Movie.title.asc())
        movies = query.limit(n).all()
        return [
            {
                "title": m.title,
                "year": m.year if m.year is not None else 0,
                "rating": m.rating,
                "genre": m.genre
            }
            for m in movies if m.year is not None
        ]
    finally:
        session.close()

def run_with_cache(duration_minutes=1, output_file="results_with_cache.json"):
    cache = movie_cache
    end_time = datetime.now() + timedelta(minutes=duration_minutes)
    requests_made = 0
    total_request_time = 0.0
    total_derived_time = 0.0
    total_compute_time = 0.0
    miss_count = 0

    while datetime.now() < end_time:
        n = random.choice(POPULAR_N if random.random() < 0.7 else range(10, 500, 5))
        key_original = f"derived:{n}:original"
        key_year = f"derived:{n}:year"
        key_title = f"derived:{n}:title"

        start = time.perf_counter()
        original_data = cache.get(key_original)
        if original_data is None:
            compute_start = time.perf_counter()
            original_data = generate_derived_movies(n)
            compute_elapsed = time.perf_counter() - compute_start
            total_compute_time += compute_elapsed
            miss_count += 1
            cache.set(key_original, original_data, compute_cost=compute_elapsed)
        miss_or_hit_time = time.perf_counter() - start

        # Year sortering
        if (sorted_by_year := cache.get(key_year)) is None:
            derived_start = time.perf_counter()
            sorted_by_year = sort_by_year(original_data)
            derived_elapsed = time.perf_counter() - derived_start
            cache.set(key_year, sorted_by_year, compute_cost=derived_elapsed)
            total_derived_time += derived_elapsed

        # Title sortering
        if (sorted_by_title := cache.get(key_title)) is None:
            derived_start = time.perf_counter()
            sorted_by_title = sort_by_title(original_data)
            derived_elapsed = time.perf_counter() - derived_start
            cache.set(key_title, sorted_by_title, compute_cost=derived_elapsed)
            total_derived_time += derived_elapsed

        total_request_time += miss_or_hit_time
        requests_made += 1
        time.sleep(random.uniform(0.2, 0.5))

    stats = cache.stats()
    stats.update({
        "total_requests": requests_made,
        "total_duration_seconds": duration_minutes * 60,
        "avg_request_time": total_request_time / requests_made if requests_made else 0.0,
        "avg_derived_compute_time": total_derived_time / requests_made if requests_made else 0.0,
        "avg_compute_cost": total_compute_time / miss_count if miss_count else 0.0,
        "miss_count": miss_count,
        "cache_size": len(cache),
    })

    with open(output_file, "w") as f:
        json.dump(stats, f, indent=2)

    print("=== Cache Enabled Benchmark ===")
    for k, v in stats.items():
        if isinstance(v, float):
            print(f"{k:25}: {v:.3f}")
        else:
            print(f"{k:25}: {v}")

def run_without_cache(duration_minutes=1, output_file="results_no_cache.json"):
    end_time = datetime.now() + timedelta(minutes=duration_minutes)
    recompute_times = []
    per_sort_times = {"rating": [], "year": [], "title": []}
    requests_made = 0
    total_request_time = 0.0

    while datetime.now() < end_time:
        n = random.choice(POPULAR_N if random.random() < 0.7 else range(10, 500, 5))
        method_name, kwargs = random.choice([
            ("rating", {"order_by_rating": True}),
            ("year", {"order_by_year": True}),
            ("title", {"order_by_title": True}),
        ])

        start = time.perf_counter()
        generate_derived_movies(n, **kwargs)
        elapsed = time.perf_counter() - start

        recompute_times.append(elapsed)
        per_sort_times[method_name].append(elapsed)

        total_request_time += elapsed
        requests_made += 1
        time.sleep(random.uniform(0.2, 0.5))

    result = {
        "total_requests": requests_made,
        "avg_recompute_latency": sum(recompute_times) / len(recompute_times),
        "total_recompute_time": sum(recompute_times),
        "avg_request_time": total_request_time / requests_made,
        "total_duration_seconds": duration_minutes * 60,
        "avg_recompute_latency_per_sort": {
            k: sum(v)/len(v) if v else 0.0 for k, v in per_sort_times.items()
        }
    }

    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)

    print("=== No Cache Benchmark ===")
    for k, v in result.items():
        if isinstance(v, float):
            print(f"{k:25}: {v:.3f}")
        else:
            print(f"{k:25}: {v}")
