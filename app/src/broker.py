from taskiq_redis import RedisAsyncResultBackend, ListQueueBroker
from config import REDIS_URL

broker = ListQueueBroker(REDIS_URL).with_result_backend(RedisAsyncResultBackend(REDIS_URL))