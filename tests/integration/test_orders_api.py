import pytest


@pytest.mark.integration
class TestOrders:
    def _setup_panier(self, client, user_id, stock=10, price=100.0, quantity=2):
        product_response = client.post(
            "/products/",
            json={"name": "Produit Commande", "price": price, "stock": stock},
        )
        assert product_response.status_code == 201
        product = product_response.json()

        add_response = client.post(
            f"/cart/?user_id={user_id}",
            json={"product_id": product['id'], "quantity": quantity},
        )
        assert add_response.status_code == 201
        return product

    def test_creation_commande_valide(self, client):
        self._setup_panier(client, user_id=200)
        response = client.post("/orders/", json={"user_id": 200})
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "pending"
        assert data["total_ttc"] > 0

    def test_total_ttc_correct(self, client):
        self._setup_panier(client, user_id=201, price=100.0, quantity=2)
        response = client.post("/orders/", json={"user_id": 201})
        assert response.status_code == 201
        order = response.json()
        assert order["total_ht"] == pytest.approx(200.0, rel=1e-2)
        assert order["total_ttc"] == pytest.approx(240.0, rel=1e-2)

    def test_commande_decremente_stock(self, client):
        product = self._setup_panier(client, user_id=202, stock=10, quantity=2)
        create_order = client.post("/orders/", json={"user_id": 202})
        assert create_order.status_code == 201

        updated = client.get(f"/products/{product['id']}")
        assert updated.status_code == 200
        assert updated.json()["stock"] == 8

    def test_commande_vide_le_panier(self, client):
        self._setup_panier(client, user_id=203)
        response = client.post("/orders/", json={"user_id": 203})
        assert response.status_code == 201

        cart = client.get("/cart/203")
        assert cart.status_code == 200
        assert cart.json()["items"] == []

    def test_panier_vide_retourne_400(self, client):
        response = client.post("/orders/", json={"user_id": 9999})
        assert response.status_code == 400

    def test_commande_avec_coupon(self, client, api_coupon):
        product_response = client.post(
            "/products/",
            json={"name": "PC", "price": 100.0, "stock": 5},
        )
        assert product_response.status_code == 201
        product = product_response.json()

        add_response = client.post(
            "/cart/?user_id=204",
            json={"product_id": product['id'], "quantity": 1},
        )
        assert add_response.status_code == 201

        response = client.post(
            "/orders/",
            json={"user_id": 204, "coupon_code": api_coupon["code"]},
        )
        assert response.status_code == 201
        order = response.json()
        assert order["total_ttc"] == pytest.approx(108.0, rel=1e-2)
        assert order["coupon_code"] == api_coupon["code"]

    def test_statut_pending_vers_paid(self, client):
        self._setup_panier(client, user_id=205)
        order_response = client.post("/orders/", json={"user_id": 205})
        assert order_response.status_code == 201
        order = order_response.json()

        response = client.patch(
            f"/orders/{order['id']}/status",
            json={"status": "paid"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "paid"

    def test_transition_invalide_400(self, client):
        self._setup_panier(client, user_id=206)
        order_response = client.post("/orders/", json={"user_id": 206})
        assert order_response.status_code == 201
        order = order_response.json()

        response = client.patch(
            f"/orders/{order['id']}/status",
            json={"status": "shipped"},
        )
        assert response.status_code == 400

    def test_coupon_inexistant_retourne_404(self, client):
        product = self._setup_panier(client, user_id=207, stock=5, price=50.0, quantity=1)
        assert product["id"] is not None

        response = client.post(
            "/orders/",
            json={"user_id": 207, "coupon_code": "FAKECODE"},
        )
        assert response.status_code == 404
        assert "Coupon" in response.json()["detail"] or "coupon" in response.json()["detail"]

    def test_get_commande_par_id(self, client):
        self._setup_panier(client, user_id=208, stock=5, price=80.0, quantity=2)
        create_response = client.post("/orders/", json={"user_id": 208})
        assert create_response.status_code == 201
        created = create_response.json()

        get_response = client.get(f"/orders/{created['id']}")
        assert get_response.status_code == 200
        order = get_response.json()
        assert order["id"] == created["id"]
        assert order["total_ttc"] == created["total_ttc"]
        assert order["status"] == created["status"]
