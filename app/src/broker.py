from config import REDIS_URL
from taskiq_redis import ListQueueBroker, RedisAsyncResultBackend

broker = ListQueueBroker(url=REDIS_URL).with_result_backend(RedisAsyncResultBackend(redis_url=REDIS_URL))
