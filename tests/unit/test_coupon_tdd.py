# tests/unit/test_coupon_tdd.py - TDD : écrire les tests AVANT le code
import pytest

# L'import suivant va échouer (ImportError) — c'est normal en RED !
from app.services.pricing import valider_coupon
from app.models import Coupon


class TestValiderCoupon:

    def test_coupon_actif_valide(self):
        """Coupon actif + montant suffisant → True."""
        c = Coupon(code='PROMO20', reduction=20.0, actif=True)
        assert valider_coupon(c, panier_total=50.0) is True

    def test_coupon_inactif_leve_exception(self):
        c = Coupon(code='OLD', reduction=10.0, actif=False)
        with pytest.raises(ValueError, match='inactif'):
            valider_coupon(c, panier_total=50.0)

    def test_montant_minimum_non_atteint(self):
        """Panier < 10€ → ValueError."""
        c = Coupon(code='PROMO10', reduction=10.0, actif=True)
        with pytest.raises(ValueError, match='minimum'):
            valider_coupon(c, panier_total=5.0)

    def test_coupon_gratuit_panier_insuffisant(self):
        """reduction=100 mais panier < 50€ → ValueError."""
        c = Coupon(code='FREE', reduction=100.0, actif=True)
        with pytest.raises(ValueError, match='50'):
            valider_coupon(c, panier_total=30.0)

    def test_coupon_gratuit_panier_suffisant(self):
        """reduction=100 et panier >= 50€ → True."""
        c = Coupon(code='FREE100', reduction=100.0, actif=True)
        assert valider_coupon(c, panier_total=50.0) is True

    def test_reduction_invalide_leve_exception(self):
        c = Coupon(code='BAD', reduction=0.0, actif=True)
        with pytest.raises(ValueError, match='réduction'):
            valider_coupon(c, panier_total=100.0)

    @pytest.mark.parametrize('total,attendu', [
        (10.0, True),   # exactement le minimum
        (9.99, False),  # juste en dessous du minimum
        (100.0, True),  # largement suffisant
    ])
    def test_seuil_montant_minimum(self, total, attendu):
        c = Coupon(code='T', reduction=10.0, actif=True)
        if attendu:
            assert valider_coupon(c, panier_total=total) is True
        else:
            with pytest.raises(ValueError):
                valider_coupon(c, panier_total=total)

    def test_panier_total_zero(self):
        """Cas limite : panier_total=0 → ValueError minimum."""
        c = Coupon(code='PROMO', reduction=10.0, actif=True)
        with pytest.raises(ValueError, match='minimum'):
            valider_coupon(c, panier_total=0)

    def test_panier_total_negatif(self):
        """Cas limite : panier_total négatif → ValueError minimum."""
        c = Coupon(code='PROMO', reduction=10.0, actif=True)
        with pytest.raises(ValueError, match='minimum'):
            valider_coupon(c, panier_total=-5.0)
