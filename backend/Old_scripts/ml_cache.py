# import time
# from collections import OrderedDict
# from typing import Any, Dict


# class RuleBasedCache:
#     def __init__(self, maxsize: int = 100):
#         self.maxsize = maxsize
#         self.cache: OrderedDict[str, Any] = OrderedDict()
#         self.metadata: Dict[str, Dict[str, Any]] = {}

#     def _evict(self):
#         if len(self.cache) < self.maxsize:
#             return

#         print("[Eviction] Cache full. Evaluating what to evict...")

#         # Rank candidates using a weighted score based on:
#         # - Low access count
#         # - Long time since last access
#         # - High compute cost
#         # - Large size
#         def eviction_score(meta):
#             age = time.time() - meta["last_access"]
#             return (
#                 (1 / (meta["access_count"] + 1)) * 2 +
#                 age * 0.5 +
#                 meta["compute_cost"] * 0.3 +
#                 meta["size"] * 0.2
#             )

#         evictable_items = [
#             (key, eviction_score(meta))
#             for key, meta in self.metadata.items()
#         ]

#         evictable_items.sort(key=lambda x: x[1], reverse=True)
#         key_to_evict = evictable_items[0][0]

#         print(f"[Eviction] Evicting key: {key_to_evict}")
#         self.cache.pop(key_to_evict, None)
#         self.metadata.pop(key_to_evict, None)

#     def set(self, key: str, value: Any, compute_cost=1.0, size=1.0):
#         if key in self.cache:
#             self.cache.pop(key)
#         else:
#             self._evict()

#         self.cache[key] = value
#         self.metadata[key] = {
#             "access_count": 0,
#             "last_access": time.time(),
#             "compute_cost": compute_cost,
#             "size": size,
#         }

#     def get(self, key: str):
#         if key in self.cache:
#             self.metadata[key]["access_count"] += 1
#             self.metadata[key]["last_access"] = time.time()
#             return self.cache[key]
#         return None

# def stats(self):
#     # Return detailed info for dashboard consumption
#     return {
#         "total_items": len(self.cache),
#         "maxsize": self.maxsize,
#         "entries": {
#             key: {
#                 "access_count": meta["access_count"],
#                 "last_access": meta["last_access"],
#                 "compute_cost": meta["compute_cost"],
#                 "size": meta["size"]
#             } for key, meta in self.metadata.items()
#         }
#     }


#     def train_model(self):
#         # Dummy method to satisfy /cache/train endpoint
#         return {"message": "Rule-based strategy does not require training."}
