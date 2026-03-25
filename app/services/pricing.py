# app/services/pricing.py
from typing import Optional, List, Tuple
from app.models import Product, Coupon
TVA_RATE = 0.20 # Taux TVA France (20%)
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
        return 0.0 # liste vide → 0
        total_ht = sum(p.price * q for p, q in produits) # somme HT
        total_ttc = calcul_prix_ttc(total_ht) # → TTC
    if coupon:
        total_ttc = appliquer_coupon(total_ttc, coupon) # réduction
        return total_ttc