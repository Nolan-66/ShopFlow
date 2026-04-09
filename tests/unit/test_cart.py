import pytest

from app.models import CartItem
from app.services.cart import (
    get_or_create_cart,
    ajouter_au_panier,
    retirer_du_panier,
    vider_panier,
    calculer_total_ttc,
)


@pytest.mark.unit
class TestGetOrCreateCart:
    def test_cree_panier_si_absent(self, db_session):
        cart = get_or_create_cart(user_id=42, session=db_session)

        assert cart is not None
        assert cart.user_id == 42
        assert cart.id is not None

    def test_recupere_panier_existant(self, db_session):
        cart1 = get_or_create_cart(user_id=42, session=db_session)
        cart2 = get_or_create_cart(user_id=42, session=db_session)

        assert cart1.id == cart2.id


class TestAjouterAuPanier:
    def test_ajout_produit_panier(self, product_sample, db_session):
        cart = ajouter_au_panier(
            product=product_sample,
            quantite=2,
            user_id=42,
            session=db_session,
        )

        assert cart.user_id == 42
        assert len(cart.items) == 1
        assert cart.items[0].product_id == product_sample.id
        assert cart.items[0].quantity == 2

    def test_ajout_meme_produit_incremente_quantite(self, product_sample, db_session):
        ajouter_au_panier(product_sample, 2, 42, db_session)
        cart = ajouter_au_panier(product_sample, 3, 42, db_session)

        assert len(cart.items) == 1
        assert cart.items[0].quantity == 5

    def test_quantite_invalide_leve_exception(self, product_sample, db_session):
        with pytest.raises(ValueError):
            ajouter_au_panier(product_sample, 0, 42, db_session)

    def test_stock_insuffisant_leve_exception(self, product_sample, db_session):
        with pytest.raises(ValueError, match="Stock insuffisant"):
            ajouter_au_panier(product_sample, 999, 42, db_session)


class TestRetirerDuPanier:
    def test_retirer_produit_du_panier(self, product_sample, db_session):
        cart = ajouter_au_panier(product_sample, 2, 42, db_session)
        cart = retirer_du_panier(cart, product_sample.id, db_session)

        assert len(cart.items) == 0

    def test_retirer_produit_absent_leve_exception(self, product_sample, db_session):
        cart = get_or_create_cart(42, db_session)

        with pytest.raises(ValueError):
            retirer_du_panier(cart, product_sample.id, db_session)


class TestViderPanier:
    def test_vider_panier_supprime_items(self, product_sample, db_session):
        cart = ajouter_au_panier(product_sample, 2, 42, db_session)

        vider_panier(cart, db_session)

        cart = get_or_create_cart(42, db_session)
        assert len(cart.items) == 0


class TestCalculerTotalTtc:
    def test_calculer_total_ttc(self, product_sample, db_session):
        cart = ajouter_au_panier(product_sample, 2, 42, db_session)

        total = calculer_total_ttc(cart)

        assert total == round(product_sample.price * 2 * 1.20, 2)

    def test_calculer_total_ttc_panier_vide(self, db_session):
        cart = get_or_create_cart(42, db_session)

        total = calculer_total_ttc(cart)

        assert total == 0.0