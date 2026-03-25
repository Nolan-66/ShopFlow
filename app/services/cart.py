from sqlalchemy.orm import Session
from app.models import Cart, CartItem, Product
from app.services.stock import verifier_stock


def get_or_create_cart(user_id: int, session: Session) -> Cart:
    cart = session.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        session.add(cart)
        session.commit()
        session.refresh(cart)
    return cart


def ajouter_au_panier(product: Product, quantite: int, user_id: int, session: Session) -> Cart:
    if quantite <= 0:
        raise ValueError("La quantité doit être supérieure à 0")

    cart = get_or_create_cart(user_id, session)

    item = session.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == product.id
    ).first()

    quantite_totale = quantite if not item else item.quantity + quantite

    if not verifier_stock(product, quantite_totale):
        raise ValueError(
            f"Stock insuffisant pour '{product.name}' : "
            f"{product.stock} disponible(s), {quantite_totale} demandé(s)."
        )

    if item:
        item.quantity = quantite_totale
    else:
        item = CartItem(cart_id=cart.id, product_id=product.id, quantity=quantite)
        session.add(item)

    session.commit()
    session.refresh(cart)
    return cart


def retirer_du_panier(cart: Cart, product_id: int, session: Session) -> Cart:
    item = session.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == product_id
    ).first()

    if not item:
        raise ValueError(f"Produit {product_id} absent du panier")

    session.delete(item)
    session.commit()
    session.refresh(cart)
    return cart


def vider_panier(cart: Cart, session: Session) -> None:
    session.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    session.commit()


def calculer_total_ttc(cart: Cart) -> float:
    total_ht = sum(item.product.price * item.quantity for item in cart.items)
    return round(total_ht * 1.20, 2)
