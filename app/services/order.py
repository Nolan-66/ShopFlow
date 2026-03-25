from typing import Optional
from sqlalchemy.orm import Session
from app.models import Cart, Order, OrderItem, Coupon
from app.services.pricing import calcul_prix_ttc, appliquer_coupon
from app.services.cart import vider_panier


STATUTS_VALIDES = {"pending", "paid", "cancelled"}


def creer_commande(
    user_id: int,
    cart: Cart,
    session: Session,
    coupon: Optional[Coupon] = None
) -> Order:
    if not cart.items:
        raise ValueError("Impossible de créer une commande à partir d'un panier vide")

    total_ht = sum(item.product.price * item.quantity for item in cart.items)
    total_ttc = calcul_prix_ttc(total_ht)

    coupon_code = None
    if coupon:
        total_ttc = appliquer_coupon(total_ttc, coupon)
        coupon_code = coupon.code

    order = Order(
        user_id=user_id,
        total_ht=round(total_ht, 2),
        total_ttc=round(total_ttc, 2),
        coupon_code=coupon_code,
        status="pending"
    )
    session.add(order)
    session.flush()

    for item in cart.items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.product.price
        )
        session.add(order_item)

        item.product.stock -= item.quantity
        if item.product.stock < 0:
            raise ValueError(f"Stock insuffisant pour '{item.product.name}'")

    session.commit()
    session.refresh(order)

    vider_panier(cart, session)
    session.refresh(order)
    return order


def mettre_a_jour_statut(order_id: int, nouveau_statut: str, session: Session) -> Order:
    if nouveau_statut not in STATUTS_VALIDES:
        raise ValueError(f"Statut invalide : {nouveau_statut}")

    order = session.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise ValueError(f"Commande {order_id} introuvable")

    order.status = nouveau_statut
    session.commit()
    session.refresh(order)
    return order