from config import REDIS_URL, TASKIQ_BACKEND_POSTGRES_URL
from taskiq_redis import ListQueueBroker
from taskiq_pg.psycopg import PsycopgResultBackend

broker = ListQueueBroker(url=REDIS_URL).with_result_backend(PsycopgResultBackend(dsn=TASKIQ_BACKEND_POSTGRES_URL))
