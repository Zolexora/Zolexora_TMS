import logging
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from app.core.config import settings

logger = logging.getLogger(__name__)

redis_broker = RedisBroker(url=settings.REDIS_URL)
dramatiq.set_broker(redis_broker)
