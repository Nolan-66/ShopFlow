# app/cache.py
import os, logging
from unittest.mock import MagicMock
logger = logging.getLogger(__name__)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
def _create_redis_client():
    try:
        import redis
        client = redis.from_url(REDIS_URL, decode_responses=True,
        socket_connect_timeout=2)
        client.ping()
        logger.info(f"Redis connecté : {REDIS_URL}")
        return client
    except Exception as e:
        logger.warning(f"Redis indisponible ({e}) — MagicMock activé")
        return MagicMock() # silencieux si Redis absent
    
redis_client = _create_redis_client()
# ↑ Cet objet est mocké dans les tests via mocker.patch('app.cache.redis_client')