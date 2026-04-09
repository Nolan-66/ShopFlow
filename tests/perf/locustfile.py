# tests/perf/locustfile.py
from locust import HttpUser, task, between
import random

PRODUCT_IDS = list(range(1, 21))  # IDs des 20 produits créés


class ShopFlowUser(HttpUser):
    wait_time = between(0.5, 2.0)

    def on_start(self):
        self.user_id = random.randint(10000, 99999)

    @task(5)
    def browse_products(self):
        """Scénario le plus fréquent : lister les produits."""
        self.client.get('/products/', name='/products/ [list]')

    @task(3)
    def get_product_detail(self):
        """Consulter un produit au hasard."""
        pid = random.choice(PRODUCT_IDS)
        self.client.get(f'/products/{pid}', name='/products/{id}')

    @task(2)
    def add_to_cart(self):
        """Ajouter un produit au panier."""
        pid = random.choice(PRODUCT_IDS)
        self.client.post(
            '/cart/',
            params={'user_id': self.user_id},
            json={'product_id': pid, 'quantity': 1},
            name='/cart/ [add]',
        )

    @task(1)
    def place_order(self):
        """Simuler un achat complet : ajout panier puis commande."""
        pid = random.choice(PRODUCT_IDS)
        # 1. Ajouter un produit au panier
        self.client.post(
            '/cart/',
            params={'user_id': self.user_id},
            json={'product_id': pid, 'quantity': 1},
            name='/cart/ [add]',
        )
        # 2. Passer la commande — 400 (panier vide ou stock épuisé) est acceptable
        with self.client.post(
            '/orders/',
            json={'user_id': self.user_id, 'coupon_code': None},
            name='/orders/ [create]',
            catch_response=True,
        ) as resp:
            if resp.status_code in (201, 400):
                resp.success()

    @task(1)
    def health_check(self):
        self.client.get('/health', name='/health [smoke]')
