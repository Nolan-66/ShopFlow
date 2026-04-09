import pytest

from app.models import Coupon
from app.services.cart import get_or_create_cart, ajouter_au_panier
from app.services.order import creer_commande, mettre_a_jour_statut


@pytest.mark.unit
class TestCreerCommande:
    def test_creer_commande_depuis_panier(self, product_sample, db_session):
        cart = ajouter_au_panier(
            product=product_sample,
            quantite=2,
            user_id=42,
            session=db_session,
        )

        order = creer_commande(
            user_id=42,
            cart=cart,
            session=db_session,
        )

        assert order is not None
        assert order.user_id == 42
        assert order.status == "pending"
        assert order.total_ht == round(product_sample.price * 2, 2)
        assert order.total_ttc == round(product_sample.price * 2 * 1.20, 2)
        assert len(order.items) == 1
        assert order.items[0].product_id == product_sample.id
        assert order.items[0].quantity == 2
        assert order.items[0].unit_price == product_sample.price

    def test_creer_commande_panier_vide_leve_exception(self, db_session):
        cart = get_or_create_cart(user_id=42, session=db_session)

        with pytest.raises(ValueError, match="panier vide"):
            creer_commande(
                user_id=42,
                cart=cart,
                session=db_session,
            )

    def test_creer_commande_avec_coupon(self, product_sample, coupon_sample, db_session):
        cart = ajouter_au_panier(
            product=product_sample,
            quantite=1,
            user_id=42,
            session=db_session,
        )

        order = creer_commande(
            user_id=42,
            cart=cart,
            session=db_session,
            coupon=coupon_sample,
        )

        total_ht_attendu = round(product_sample.price, 2)
        total_ttc_sans_coupon = round(product_sample.price * 1.20, 2)
        total_ttc_avec_coupon = round(total_ttc_sans_coupon * 0.8, 2)

        assert order.coupon_code == coupon_sample.code
        assert order.total_ht == total_ht_attendu
        assert order.total_ttc == total_ttc_avec_coupon

    def test_creer_commande_vide_le_panier(self, product_sample, db_session):
        cart = ajouter_au_panier(
            product=product_sample,
            quantite=2,
            user_id=42,
            session=db_session,
        )

        creer_commande(
            user_id=42,
            cart=cart,
            session=db_session,
        )

        cart_apres = get_or_create_cart(user_id=42, session=db_session)
        assert len(cart_apres.items) == 0

    def test_creer_commande_decremente_le_stock(self, product_sample, db_session):
        stock_avant = product_sample.stock

        cart = ajouter_au_panier(
            product=product_sample,
            quantite=3,
            user_id=42,
            session=db_session,
        )

        creer_commande(
            user_id=42,
            cart=cart,
            session=db_session,
        )

        assert product_sample.stock == stock_avant - 3


@pytest.mark.unit
class TestMettreAJourStatut:
    def test_mettre_a_jour_statut_commande(self, product_sample, db_session):
        cart = ajouter_au_panier(
            product=product_sample,
            quantite=1,
            user_id=42,
            session=db_session,
        )

        order = creer_commande(
            user_id=42,
            cart=cart,
            session=db_session,
        )

        updated = mettre_a_jour_statut(
            order_id=order.id,
            nouveau_statut="paid",
            session=db_session,
        )

        assert updated.status == "paid"

    def test_statut_invalide_leve_exception(self):
        class DummySession:
            pass

        with pytest.raises(ValueError, match="Statut invalide"):
            mettre_a_jour_statut(
                order_id=1,
                nouveau_statut="unknown",
                session=DummySession(),
            )

    def test_commande_introuvable_leve_exception(self, db_session):
        with pytest.raises(ValueError, match="introuvable"):
            mettre_a_jour_statut(
                order_id=9999,
                nouveau_statut="paid",
                session=db_session,
            )