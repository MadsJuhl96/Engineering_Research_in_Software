import json
from simulate_stress import run_with_cache, run_without_cache

def compare_results(with_file, without_file):
    with open(with_file) as f:
        with_cache = json.load(f)
    with open(without_file) as f:
        no_cache = json.load(f)

    print("\n📊 COMPARISON RESULTS")
    print("=" * 40)

    print("With Cache:")
    print(f"- Total requests           : {with_cache.get('total_requests')}")
    print(f"- Eviction count           : {with_cache.get('eviction_count')}")
    print(f"- Hit rate                 : {with_cache.get('hit_rate')*100:.2f}%")
    print(f"- Avg hit latency          : {with_cache.get('avg_hit_latency')*1000:.4f} ms")
    print(f"- Avg miss latency         : {with_cache.get('avg_miss_latency')*1000:.4f} ms")
    print(f"- Avg request time         : {with_cache.get('avg_request_time')*1000:.4f} ms")
    print(f"- Avg derived compute time : {with_cache.get('avg_derived_compute_time')*1000:.4f} ms")

    compute_cost = with_cache.get('avg_compute_cost', 0)
    recompute_count = with_cache.get('miss_count', 0)
    cached_items = with_cache.get('cache_size', 0)
    storage_cost = 0.001
    total_cost_with_cache = compute_cost * recompute_count + storage_cost * cached_items
    print(f"- Total cost estimate      : {total_cost_with_cache * 1000:.4f} ms-equivalent")

    print("\nWithout Cache:")
    print(f"- Total requests           : {no_cache.get('total_requests')}")
    print(f"- Avg recompute latency    : {no_cache.get('avg_recompute_latency')*1000:.4f} ms")
    print(f"- Total recompute time     : {no_cache.get('total_recompute_time'):.4f} s")
    print(f"- Avg request time         : {no_cache.get('avg_request_time')*1000:.4f} ms")

    cpu_cost = 0.0002
    total_cost_no_cache = no_cache.get("total_recompute_time", 0) + (cpu_cost * no_cache.get("total_requests", 0))
    print(f"- Total cost estimate      : {total_cost_no_cache * 1000:.4f} ms-equivalent")
    print("=" * 40)

if __name__ == "__main__":
    with_file = "results_with_cache.json"
    without_file = "results_no_cache.json"

    print("🚀 Running benchmark WITH cache...")
    run_with_cache(duration_minutes=2.5, output_file=with_file)

    print("\n🚀 Running benchmark WITHOUT cache...")
    run_without_cache(duration_minutes=2.5, output_file=without_file)

    compare_results(with_file, without_file)
