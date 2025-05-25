import time
import random
import requests

API = "http://127.0.0.1:8000"

def simulate_load_all_movies():
    print("🔄 Loading all movies into 'all_movies' cache...")
    res = requests.get(f"{API}/movies")
    data = res.json()
    print(f"✅ Loaded {len(data['movies'])} movies from: {data['source']}")
    return data['movies']

def simulate_top_n(n):
    print(f"📈 Deriving top {n} movies...")
    all_movies = requests.get(f"{API}/movies").json()["movies"]
    sorted_movies = sorted(all_movies, key=lambda m: m["rating"], reverse=True)
    top_n = sorted_movies[:n]
    for movie in top_n:
        title = movie["title"]
        requests.get(f"{API}/movies/{title}")
    print(f"✅ Accessed top {n} movie items.")

def spam_derived_access(n, rounds=10):
    for i in range(rounds):
        print(f"🎯 Round {i+1}/{rounds}: Simulating top {n} access")
        simulate_top_n(n)
        time.sleep(0.5)

def run_progressive_simulation():
    all_movies = simulate_load_all_movies()
    sizes = [100, 90, 80, 70, 60, 50, 40, 30, 20, 10]

    for n in sizes:
        spam_derived_access(n, rounds=5)

def run_simulation():
    print("🚀 Starting progressive cache simulation...")
    run_progressive_simulation()
    print("🏁 Simulation complete.")

if __name__ == "__main__":
    run_simulation()
