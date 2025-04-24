import redis.asyncio as redis

# Create Redis client (default Redis host/port)
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
