import time

class CacheEntry:
    def __init__(self, value):
        self.value = value
        self.access_count = 0
        self.last_access = time.time()
        self.total_latency = 0.0
        self.hits = 0

    def update_access(self, latency):
        self.access_count += 1
        self.last_access = time.time()
        self.total_latency += latency
        self.hits += 1

    @property
    def avg_latency(self):
        return self.total_latency / self.hits if self.hits else 0.0


class RuleBasedCache:
    def __init__(self, maxsize=200):
        self.maxsize = maxsize
        self.data = {}
        self.eviction_count = 0
        self.hits = 0
        self.misses = 0
        self.hit_latency = 0.0
        self.miss_latency = 0.0
        self.costs = {}

    def __len__(self):
        return len(self.data)

    def get(self, key):
        start = time.perf_counter()
        entry = self.data.get(key)
        latency = time.perf_counter() - start
        if entry:
            entry.update_access(latency)
            self.hit_latency += latency
            self.hits += 1
            return entry.value
        else:
            self.miss_latency += latency
            self.misses += 1
            return None

    def set(self, key, value, compute_cost=None):
        if key not in self.data:
            self.data[key] = CacheEntry(value)
            if compute_cost is not None:
                self.costs[key] = compute_cost
        self._evict_if_needed()

    def _evict_if_needed(self):
        if not self.data:
            return

        now = time.time()
        access_values = [entry.access_count for entry in self.data.values()]
        access_max = max(access_values) or 1

        time_values = [entry.last_access for entry in self.data.values()]
        time_min = min(time_values)
        time_max = max(time_values) or (time_min + 1)

        cost_values = [self.costs.get(k, 0) for k in self.data.keys()]
        cost_max = max(cost_values) or 1

        access_weight = 0.5
        time_weight = 0.2
        cost_weight = 0.5

        def compute_score(key, entry):
            norm_access = entry.access_count / access_max
            norm_time = (entry.last_access - time_min) / (time_max - time_min)
            norm_cost = self.costs.get(key, 0) / cost_max
            score = (
                access_weight * norm_access +
                time_weight * norm_time +
                cost_weight * norm_cost
            )
            return score

        while len(self.data) > self.maxsize:
            scored_items = [
                (key, compute_score(key, entry), entry.access_count, entry.last_access, self.costs.get(key, 0))
                for key, entry in self.data.items()
            ]
            victim_key, victim_score, acc, last, cost = min(scored_items, key=lambda x: x[1])
            print(f"[Eviction] ❌ '{victim_key}' smides ud | Score: {victim_score:.4f} | Access: {acc} | Last: {last:.0f} | Cost: {cost:.3f} ms")
            del self.data[victim_key]
            self.eviction_count += 1
            if victim_key in self.costs:
                del self.costs[victim_key]

    def stats(self):
        total_requests = self.hits + self.misses
        avg_cost = sum(self.costs.values()) / len(self.costs) if self.costs else 0.0
        return {
            "total_requests": total_requests,
            "eviction_count": self.eviction_count,
            "hit_rate": self.hits / total_requests if total_requests > 0 else 0.0,
            "avg_hit_latency": self.hit_latency / self.hits if self.hits else 0.0,
            "avg_miss_latency": self.miss_latency / self.misses if self.misses else 0.0,
            "avg_compute_cost": avg_cost
        }

# Global instans
movie_cache = RuleBasedCache(maxsize=200)
