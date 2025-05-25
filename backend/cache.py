import time
import logging
from collections import OrderedDict
from typing import Any, Dict, List

logger = logging.getLogger("RuleBasedCache")
logger.setLevel(logging.DEBUG)  # Adjust to INFO in production if needed

class RuleBasedCache:
    def __init__(
        self,
        maxsize: int = 100,
        weight_access_penalty: float = 2.0,
        weight_age: float = 0.5,
        weight_compute_cost: float = 0.3,
        weight_size: float = 0.2,
        weight_latency: float = 0.4,
    ):
        self.maxsize = maxsize
        self.cache: OrderedDict[str, Any] = OrderedDict()
        self.metadata: Dict[str, Dict[str, Any]] = {}

        # Global stats
        self.total_requests = 0
        self.total_hits = 0
        self.total_misses = 0
        self.eviction_count = 0

        # Latency stats
        self.hit_latencies: List[float] = []
        self.miss_latencies: List[float] = []

        # Eviction weights (configurable)
        self.weight_access_penalty = weight_access_penalty
        self.weight_age = weight_age
        self.weight_compute_cost = weight_compute_cost
        self.weight_size = weight_size
        self.weight_latency = weight_latency

    def _evict(self):
        if len(self.cache) < self.maxsize:
            return

        def eviction_score(meta):
            age = time.time() - meta["last_access"]
            access_penalty = 1 / (meta["access_count"] + 1)
            avg_latency = (
                sum(meta["latencies"]) / len(meta["latencies"])
                if meta.get("latencies") else 0.01
            )
            return (
                access_penalty * self.weight_access_penalty +
                age * self.weight_age +
                meta["compute_cost"] * self.weight_compute_cost +
                meta["size"] * self.weight_size +
                avg_latency * self.weight_latency
            )

        scored_items = [
            (key, eviction_score(meta))
            for key, meta in self.metadata.items()
        ]
        scored_items.sort(key=lambda x: x[1], reverse=True)
        key_to_evict, score = scored_items[0]

        logger.info(f"Evicting key '{key_to_evict}' with score {score:.4f}")

        self.cache.pop(key_to_evict, None)
        self.metadata.pop(key_to_evict, None)
        self.eviction_count += 1

    def set(self, key: str, value: Any, compute_cost=1.0, size=1.0):
        if key in self.cache:
            self.cache.pop(key)
        else:
            self._evict()

        self.cache[key] = value
        self.metadata[key] = {
            "access_count": 0,
            "last_access": time.time(),
            "compute_cost": compute_cost,
            "size": size,
            "latencies": []
        }

    def get(self, key: str):
        self.total_requests += 1

        start = time.time()
        if key in self.cache:
            self.total_hits += 1
            meta = self.metadata[key]

            value = self.cache[key]
            latency = time.time() - start

            meta["access_count"] += 1
            meta["last_access"] = time.time()

            latencies: List[float] = meta["latencies"]
            latencies.append(latency)
            if len(latencies) > 10:
                latencies.pop(0)  # Keep sliding window of last 10 latencies

            self.hit_latencies.append(latency)
            if len(self.hit_latencies) > 100:
                self.hit_latencies.pop(0)  # Keep sliding window for global stats

            return value
        else:
            latency = time.time() - start
            self.total_misses += 1

            self.miss_latencies.append(latency)
            if len(self.miss_latencies) > 100:
                self.miss_latencies.pop(0)

            return None

    def stats(self):
        hit_rate = self.total_hits / self.total_requests if self.total_requests else 0
        avg_hit_latency = sum(self.hit_latencies) / len(self.hit_latencies) if self.hit_latencies else 0.0
        avg_miss_latency = sum(self.miss_latencies) / len(self.miss_latencies) if self.miss_latencies else 0.0

        return {
            "total_items": len(self.cache),
            "maxsize": self.maxsize,
            "hit_rate": hit_rate,
            "eviction_count": self.eviction_count,
            "avg_hit_latency": avg_hit_latency,
            "avg_miss_latency": avg_miss_latency,
            "total_requests": self.total_requests,
            "total_hits": self.total_hits,
            "total_misses": self.total_misses,
            "entries": {
                key: {
                    "access_count": meta["access_count"],
                    "last_access": meta["last_access"],
                    "compute_cost": meta["compute_cost"],
                    "size": meta["size"],
                    "avg_latency": (
                        sum(meta["latencies"]) / len(meta["latencies"])
                        if meta["latencies"] else 0.0
                    ),
                }
                for key, meta in self.metadata.items()
            }
        }


# Instances for import in app
movie_cache = RuleBasedCache(maxsize=100)
derived_cache = RuleBasedCache(maxsize=10)
