from config import REDIS_URL
from taskiq_redis import RedisStreamBroker, RedisAsyncResultBackend

broker = RedisStreamBroker(url=REDIS_URL).with_result_backend(RedisAsyncResultBackend(redis_url=REDIS_URL))
