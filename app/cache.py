# app/cache.py
import os
import json
import logging
from unittest.mock import MagicMock

logger = logging.getLogger(__name__)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


def _create_redis_client():
    try:
        import redis

        client = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
        )
        client.ping()
        logger.info(f"Redis connecté : {REDIS_URL}")
        return client
    except Exception as e:
        logger.warning(f"Redis indisponible ({e}) — MagicMock activé")
        return MagicMock()


redis_client = _create_redis_client()


def get_cached(key: str):
    """
    Récupère une valeur JSON en cache et la désérialise.
    Retourne None si la clé n'existe pas ou si une erreur survient.
    """
    try:
        value = redis_client.get(key)
        if not value:
            return None
        return json.loads(value)
    except Exception as e:
        logger.warning(f"Erreur lecture cache pour {key}: {e}")
        return None


def set_cached(key: str, value, ttl: int = 300):
    """
    Sérialise une valeur en JSON puis la stocke en cache.
    ttl par défaut : 300 secondes.
    """
    try:
        redis_client.set(key, json.dumps(value), ex=ttl)
    except Exception as e:
        logger.warning(f"Erreur écriture cache pour {key}: {e}")


def delete_cached(key: str):
    """
    Supprime une clé du cache.
    """
    try:
        redis_client.delete(key)
    except Exception as e:
        logger.warning(f"Erreur suppression cache pour {key}: {e}")