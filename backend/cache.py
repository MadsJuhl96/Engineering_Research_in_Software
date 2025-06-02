import time  # For measuring access times and latency

# Represents a single cache entry, storing its value and metadata
class CacheEntry:
    def __init__(self, value):
        self.value = value                        # Actual value stored in cache
        self.access_count = 0                     # How many times the entry has been accessed
        self.last_access = time.time()            # Time when the entry was last accessed
        self.total_latency = 0.0                  # Cumulative latency for all accesses
        self.hits = 0                             # How many successful hits this entry received

    def update_access(self, latency):
        """Update metadata when this entry is accessed."""
        self.access_count += 1                    # Increment how many times it's been used
        self.last_access = time.time()            # Update the last accessed time
        self.total_latency += latency             # Add access latency
        self.hits += 1                            # Count this as a hit

    @property
    def avg_latency(self):
        """Return the average latency per access for this entry."""
        return self.total_latency / self.hits if self.hits else 0.0


# A rule-based cache system that stores key-value pairs and evicts based on a smart scoring system
class RuleBasedCache:
    def __init__(self, maxsize=200):
        self.maxsize = maxsize                    # Maximum allowed items in the cache
        self.data = {}                            # Dictionary for cache entries
        self.eviction_count = 0                   # Number of evictions performed
        self.hits = 0                             # Total number of cache hits
        self.misses = 0                           # Total number of cache misses
        self.hit_latency = 0.0                    # Total latency from all hits
        self.miss_latency = 0.0                   # Total latency from all misses
        self.costs = {}                           # Optional compute cost per key

    def __len__(self):
        """Returns the current number of entries in the cache."""
        return len(self.data)

    def get(self, key):
        """Try to get a cached value by key. Measure latency, count hits/misses."""
        start = time.perf_counter()               # Start latency timer
        entry = self.data.get(key)                # Try to get the cache entry
        latency = time.perf_counter() - start     # Measure time taken

        if entry:
            # Cache hit
            entry.update_access(latency)
            self.hit_latency += latency
            self.hits += 1
            return entry.value
        else:
            # Cache miss
            self.miss_latency += latency
            self.misses += 1
            return None

    def set(self, key, value, compute_cost=None):
        """Add a new entry to the cache. Evict if over capacity."""
        if key not in self.data:
            self.data[key] = CacheEntry(value)    # Store new entry
            if compute_cost is not None:
                self.costs[key] = compute_cost    # Save cost for scoring
        self._evict_if_needed()                   # Ensure size limit is respected

    def _evict_if_needed(self):
        """Evict least useful items based on a weighted score system."""
        if not self.data:
            return  # Nothing to evict

        now = time.time()

        # Get maximum values for normalization
        access_values = [entry.access_count for entry in self.data.values()]
        access_max = max(access_values) or 1

        time_values = [entry.last_access for entry in self.data.values()]
        time_min = min(time_values)
        time_max = max(time_values) or (time_min + 1)

        cost_values = [self.costs.get(k, 0) for k in self.data.keys()]
        cost_max = max(cost_values) or 1

        # Set weights for scoring criteria
        access_weight = 0.5  # Frequency of access
        time_weight = 0.2    # Recency of access
        cost_weight = 0.5    # Computation cost to reproduce the item

        def compute_score(key, entry):
            """Compute a weighted score for a cache entry."""
            # Normalize metrics to 0–1 scale
            norm_access = entry.access_count / access_max
            norm_time = (entry.last_access - time_min) / (time_max - time_min)
            norm_cost = self.costs.get(key, 0) / cost_max

            # Final weighted score combines all factors
            score = (
                access_weight * norm_access +
                time_weight * norm_time +
                cost_weight * norm_cost
            )
            return score

        # While cache exceeds max size, evict the lowest scoring entry
        while len(self.data) > self.maxsize:
            scored_items = [
                (
                    key,
                    compute_score(key, entry),
                    entry.access_count,
                    entry.last_access,
                    self.costs.get(key, 0)
                )
                for key, entry in self.data.items()
            ]
            # Find the item with the lowest score
            victim_key, victim_score, acc, last, cost = min(scored_items, key=lambda x: x[1])

            # Logging the eviction decision
            print(f"[Eviction] ❌ '{victim_key}' evicted | Score: {victim_score:.4f} | Accesses: {acc} | Last Used: {last:.0f} | Cost: {cost:.3f} ms")

            # Remove the item from both cache and cost tracking
            del self.data[victim_key]
            self.eviction_count += 1
            if victim_key in self.costs:
                del self.costs[victim_key]

    def stats(self):
        """Return performance statistics and usage metrics."""
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

# Global instance of the cache to be used, e.g., for storing movie metadata
movie_cache = RuleBasedCache(maxsize=200)
