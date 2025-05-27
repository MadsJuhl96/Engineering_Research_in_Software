import time
import random
import json
from datetime import datetime, timedelta
from sqlalchemy.sql import func
from models import Movie
from database import SessionLocal
from cache import movie_cache  # Din cache-klasse, som skal have get/set/stats

# --- Konfiguration ---
POPULAR_N = [50, 100, 150, 200, 250, 300, 350, 400, 222, 1000, 900, 800, 700, 600, 576, 459]

# --- Hjælpefunktioner til deriverede data (sorteringer) ---
def sort_by_year(movies, descending=True):
    return sorted(movies, key=lambda m: m['year'], reverse=descending)

def sort_by_title(movies, descending=False):
    return sorted(movies, key=lambda m: m['title'], reverse=descending)


# --- Hent original data fra DB ---
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


# --- Benchmark med cache ---
def run_with_cache(duration_minutes=1, output_file="results_with_cache.json"):
    cache = movie_cache
    if random.random() < 0.7:
        n = random.choice(POPULAR_N)
    else:
        n = random.choice(range(10, 1000, 5))

    end_time = datetime.now() + timedelta(minutes=duration_minutes)
    requests_made = 0
    total_request_time = 0.0
    total_derived_time = 0.0
    total_compute_time = 0.0
    miss_count = 0

    while datetime.now() < end_time:
        if random.random() < 0.7:
            n = random.choice(POPULAR_N)
        else:
            n = random.choice(range(10, 500, 5))

        # Keys til de forskellige caches
        key_original = f"derived:{n}:original"
        key_year = f"derived:{n}:year"
        key_title = f"derived:{n}:title"

        start = time.perf_counter()
        original_data = cache.get(key_original)
        if original_data is None:
            # Cache miss for original data
            compute_start = time.perf_counter()
            original_data = generate_derived_movies(n)
            compute_elapsed = time.perf_counter() - compute_start
            total_compute_time += compute_elapsed
            miss_count += 1
            cache.set(key_original, original_data, compute_cost=compute_elapsed)
        miss_or_hit_time = time.perf_counter() - start

        # Hent eller beregn sorteret efter år
        start_year = time.perf_counter()
        sorted_by_year = cache.get(key_year)
        if sorted_by_year is None:
            derived_start = time.perf_counter()
            sorted_by_year = sort_by_year(original_data)
            derived_elapsed = time.perf_counter() - derived_start
            cache.set(key_year, sorted_by_year, compute_cost=derived_elapsed)
            total_derived_time += derived_elapsed
        else:
            total_derived_time += time.perf_counter() - start_year

        # Hent eller beregn sorteret efter titel
        start_title = time.perf_counter()
        sorted_by_title = cache.get(key_title)
        if sorted_by_title is None:
            derived_start = time.perf_counter()
            sorted_by_title = sort_by_title(original_data)
            derived_elapsed = time.perf_counter() - derived_start
            cache.set(key_title, sorted_by_title, compute_cost=derived_elapsed)
            total_derived_time += derived_elapsed
        else:
            total_derived_time += time.perf_counter() - start_title

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
    print(f"Total Requests           : {requests_made}")
    print(f"Eviction Count           : {stats['eviction_count']}")
    print(f"Hit Rate                 : {stats['hit_rate']*100:.2f}%")
    print(f"Avg Hit Latency          : {stats['avg_hit_latency']*1000:.3f} ms")
    print(f"Avg Miss Latency         : {stats['avg_miss_latency']*1000:.3f} ms")
    print(f"Avg Request Time         : {stats['avg_request_time']*1000:.3f} ms")
    print(f"Avg Compute Cost (DB)    : {stats['avg_compute_cost']*1000:.3f} ms")
    print(f"Avg Derived Compute Time : {stats['avg_derived_compute_time']*1000:.3f} ms")
    print(f"Miss Count               : {miss_count}")
    print(f"Cache Size               : {stats['cache_size']}")
    print(f"Duration (sec)           : {stats['total_duration_seconds']}")



# --- Benchmark uden cache ---
def run_without_cache(duration_minutes=1, output_file="results_no_cache.json"):
    if random.random() < 0.7:
        n = random.choice(POPULAR_N)
    else:
        n = random.choice(range(10, 1000, 5))

    sort_methods = [
        ("rating", {"order_by_rating": True, "order_by_year": False, "order_by_title": False}),
        ("year", {"order_by_rating": False, "order_by_year": True, "order_by_title": False}),
        ("title", {"order_by_rating": False, "order_by_year": False, "order_by_title": True}),
    ]
    end_time = datetime.now() + timedelta(minutes=duration_minutes)
    recompute_times = []
    per_sort_times = {name: [] for name, _ in sort_methods}
    requests_made = 0
    total_request_time = 0.0

    while datetime.now() < end_time:
        if random.random() < 0.7:
            n = random.choice(POPULAR_N)
        else:
            n = random.choice(range(10, 500, 5))

        sort_name, kwargs = random.choice(sort_methods)

        start = time.perf_counter()
        generate_derived_movies(n, **kwargs)
        elapsed = time.perf_counter() - start

        recompute_times.append(elapsed)
        per_sort_times[sort_name].append(elapsed)

        total_request_time += elapsed
        requests_made += 1

        time.sleep(random.uniform(0.2, 0.5))

    avg_recompute = sum(recompute_times) / len(recompute_times) if recompute_times else 0.0
    avg_sort_times = {k: (sum(v)/len(v) if v else 0.0) for k,v in per_sort_times.items()}

    result = {
        "total_requests": requests_made,
        "avg_recompute_latency": avg_recompute,
        "total_recompute_time": sum(recompute_times),
        "avg_request_time": total_request_time / requests_made if requests_made else 0.0,
        "total_duration_seconds": duration_minutes * 60,
        "avg_recompute_latency_per_sort": avg_sort_times,
    }

    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)

    print("=== No Cache Benchmark ===")
    print(f"Total Requests         : {requests_made}")
    print(f"Avg Recomputation Time : {avg_recompute*1000:.3f} ms")
    print(f"Total Recomputation    : {sum(recompute_times):.3f} s")
    print(f"Avg Request Time       : {result['avg_request_time']*1000:.3f} ms")
    print(f"Duration (sec)         : {result['total_duration_seconds']}")
    print("Avg Recomputation Time pr. sortering:")
    for sort_name, avg_time in avg_sort_times.items():
        print(f" - {sort_name:6}: {avg_time*1000:.3f} ms")


if __name__ == "__main__":
    with_file = "results_with_cache.json"
    without_file = "results_no_cache.json"

    print("🚀 Running benchmark WITH cache...")
    run_with_cache(duration_minutes=20, output_file=with_file)

    print("\n🚀 Running benchmark WITHOUT cache...")
    run_without_cache(duration_minutes=20, output_file=without_file)
