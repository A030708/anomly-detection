import redis
import json
import logging
from config import Config

logger = logging.getLogger(__name__)

class MessageQueue:
    def __init__(self):
        try:
            self.redis = redis.from_url(Config.REDIS_URL)
            logger.info("Connected to Redis.")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis = None

    def push_log(self, log_data: dict):
        if not self.redis: return
        try:
            self.redis.lpush("log_queue", json.dumps(log_data))
        except Exception as e:
            logger.error(f"Redis Push Error: {e}")

    def pop_log(self, timeout=0):
        if not self.redis: return None
        try:
            res = self.redis.brpop("log_queue", timeout=timeout)
            if res:
                return json.loads(res[1])
        except Exception as e:
            logger.error(f"Redis Pop Error: {e}")
        return None

    def get_queue_size(self):
        if not self.redis: return 0
        return self.redis.llen("log_queue")
