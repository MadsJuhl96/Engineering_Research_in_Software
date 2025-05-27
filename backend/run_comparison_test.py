import json
from simulate_stress import run_with_cache, run_without_cache

def compare_results(with_file, without_file):
    with open(with_file) as f:
        with_cache = json.load(f)
    with open(without_file) as f:
        no_cache = json.load(f)

    print("\n📊 COMPARISON RESULTS")
    print("=" * 40)

    # ---- WITH CACHE ----
    print("With Cache:")
    print(f"- Total requests           : {with_cache.get('total_requests', 0)}")
    print(f"- Eviction count           : {with_cache.get('eviction_count', 0)}")
    print(f"- Hit rate                 : {round(with_cache.get('hit_rate', 0) * 100, 2)}%")
    print(f"- Avg hit latency          : {round(with_cache.get('avg_hit_latency', 0) * 1000, 4)} ms")
    print(f"- Avg miss latency         : {round(with_cache.get('avg_miss_latency', 0) * 1000, 4)} ms")
    print(f"- Avg request time         : {round(with_cache.get('avg_request_time', 0) * 1000, 4)} ms")
    print(f"- Avg derived compute time : {round(with_cache.get('avg_compute_cost', 0) * 1000, 4)} ms")

    # Total cost for cache: recomputation + storage
    compute_cost = with_cache.get('avg_compute_cost', 0)
    recompute_count = with_cache.get('miss_count', 0)
    cached_items = with_cache.get('cache_size', 0)
    storage_cost_per_item = 0.001  # Juster evt.

    total_cost_with_cache = (compute_cost * recompute_count) + (storage_cost_per_item * cached_items)
    print(f"- Total cost estimate      : {round(total_cost_with_cache * 1000, 4)} ms-equivalent")

    # ---- WITHOUT CACHE ----
    print("\nWithout Cache:")
    print(f"- Total requests           : {no_cache.get('total_requests', 0)}")
    print(f"- Avg recompute time       : {round(no_cache.get('avg_recompute_latency', 0) * 1000, 4)} ms")
    print(f"- Total recompute time     : {round(no_cache.get('total_recompute_time', 0), 4)} s")
    print(f"- Avg request time         : {round(no_cache.get('avg_request_time', 0) * 1000, 4)} ms")

    # Total cost without cache: recomputation + per-request CPU
    recompute_time_total = no_cache.get("total_recompute_time", 0)
    cpu_cost_per_request = 0.0002  # Valgfri antagelse
    total_cost_no_cache = recompute_time_total + (cpu_cost_per_request * no_cache.get("total_requests", 0))
    print(f"- Total cost estimate      : {round(total_cost_no_cache * 1000, 4)} ms-equivalent")

    print("=" * 40)



if __name__ == "__main__":
    with_file = "results_with_cache.json"
    without_file = "results_no_cache.json"

    print("🚀 Running benchmark WITH cache...")
    run_with_cache(duration_minutes=0.5, output_file=with_file)

    print("\n🚀 Running benchmark WITHOUT cache...")
    run_without_cache(duration_minutes=0.5, output_file=without_file)

    compare_results(with_file, without_file)
