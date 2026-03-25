# app/services/stock.py
import logging
from sqlalchemy.orm import Session
from app.models import Product
from app.cache import redis_client
logger = logging.getLogger(__name__)
def verifier_stock(product: Product, quantite: int) -> bool:
    """Retourne True si stock >= quantite, False sinon."""
    if quantite <= 0:
        raise ValueError(f"Quantité invalide : {quantite}")
    return product.stock >= quantite
def liberer_stock(product: Product, quantite: int, session: Session) -> Product:
    """Libère du stock (annulation) et met à jour le cache Redis."""
    if quantite <= 0:
        raise ValueError(f"Quantité invalide : {quantite}")
    product.stock += quantite
    session.commit()
    session.refresh(product)
    redis_client.set(f"product:{product.id}:stock", product.stock)
    return product
def reserver_stock(product: Product, quantite: int, session: Session) -> Product:
    if not verifier_stock(product, quantite):
        raise ValueError(
        f"Stock insuffisant pour '{product.name}' : "
        f"{product.stock} disponible(s), {quantite} demandé(s)."
        )
    product.stock -= quantite
    session.commit()
    session.refresh(product)
    cache_key = f"product:{product.id}:stock"
    redis_client.delete(cache_key) # invalider le cache
    logger.info(f"Stock réservé : {product.id}, qty={quantite}")
    return product