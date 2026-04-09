# app/services/pricing.py
from typing import Optional, List, Tuple
from app.models import Product, Coupon
from app.config import MONTANT_MINIMUM_COUPON, MONTANT_MINIMUM_GRATUIT

TVA_RATE = 0.20  # Taux TVA France (20%)
def calcul_prix_ttc(prix_ht: float) -> float:
    """Calcule le prix TTC à partir du prix HT. Lève ValueError si prix <
    0."""
    if prix_ht < 0:
        raise ValueError(f"Prix HT invalide : {prix_ht}")
    return round(prix_ht * (1 + TVA_RATE), 2)
def appliquer_coupon(prix: float, coupon: Coupon) -> float:
    """Applique une réduction. Lève ValueError si coupon inactif ou réduction
    invalide."""
    if not coupon.actif:
        raise ValueError(f"Coupon inactif : {coupon.code}")
    if not 0 < coupon.reduction <= 100:
        raise ValueError(f"Réduction invalide : {coupon.reduction}")
    return round(prix * (1 - coupon.reduction / 100), 2)

def calculer_total(
    produits: List[Tuple[Product, int]],
    coupon: Optional[Coupon] = None
) -> float:
    if not produits:
        return 0.0  # liste vide → 0

    total_ht = sum(p.price * q for p, q in produits)  # somme HT
    total_ttc = calcul_prix_ttc(total_ht)  # → TTC

    if coupon:
        total_ttc = appliquer_coupon(total_ttc, coupon)  # réduction

    return total_ttc


def valider_coupon(coupon: Coupon, panier_total: float) -> bool:
    """
    Valide qu'un coupon peut être appliqué sur un panier.

    Paramètres :
        coupon      -- instance Coupon à valider
        panier_total -- montant TTC du panier (float, >= 0)

    Retourne :
        True si toutes les règles sont respectées

    Lève :
        ValueError -- avec message explicite indiquant la règle violée :
            - Règle 1 : coupon doit être actif
            - Règle 2 : réduction dans ]0, 100]
            - Règle 3 : panier_total >= MONTANT_MINIMUM_COUPON (10.0€)
            - Règle 4 : coupon 100% uniquement si panier_total >= MONTANT_MINIMUM_GRATUIT (50.0€)
    """
    # Règle 1 : coupon actif
    if not coupon.actif:
        raise ValueError(f"Coupon inactif : {coupon.code}")

    # Règle 2 : réduction valide (dans ]0, 100])
    if not 0 < coupon.reduction <= 100:
        raise ValueError(
            f"réduction invalide : {coupon.reduction} (doit être dans ]0, 100])"
        )

    # Règle 3 : montant minimum du panier
    if panier_total < MONTANT_MINIMUM_COUPON:
        raise ValueError(
            f"montant minimum non atteint : panier={panier_total}€ "
            f"(minimum requis : {MONTANT_MINIMUM_COUPON}€)"
        )

    # Règle 4 : coupon 100% gratuit → seuil plus élevé
    if coupon.reduction == 100 and panier_total < MONTANT_MINIMUM_GRATUIT:
        raise ValueError(
            f"coupon gratuit (100%) requiert un panier >= {MONTANT_MINIMUM_GRATUIT}€ "
            f"(actuel : {panier_total}€)"
        )

    return True