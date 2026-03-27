import pytest


@pytest.mark.integration
class TestCart:
    def _creer_produit(self, client, stock=10, price=50.0, name="Produit Test"):
        response = client.post(
            "/products/",
            json={"name": name, "price": price, "stock": stock},
        )
        assert response.status_code == 201
        return response.json()

    def test_ajout_produit_au_panier(self, client):
        product = self._creer_produit(client)
        response = client.post(
            "/cart/?user_id=100",
            json={"product_id": product["id"], "quantity": 2},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == 100
        assert len(data["items"]) == 1
        assert data["items"][0]["quantity"] == 2

    def test_sous_total_calcule(self, client):
        product = self._creer_produit(client, price=50.0)
        add = client.post(
            "/cart/?user_id=101",
            json={"product_id": product["id"], "quantity": 2},
        )
        assert add.status_code == 201

        response = client.get("/cart/101")
        assert response.status_code == 200
        assert response.json()["sous_total"] == pytest.approx(120.0, rel=1e-2)

    def test_ajout_stock_insuffisant_400(self, client):
        product = self._creer_produit(client, stock=0)
        response = client.post(
            "/cart/?user_id=102",
            json={"product_id": product["id"], "quantity": 1},
        )
        assert response.status_code == 400

    def test_ajout_meme_produit_incremente_quantite(self, client):
        product = self._creer_produit(client, stock=20)
        r1 = client.post(
            "/cart/?user_id=103",
            json={"product_id": product["id"], "quantity": 2},
        )
        assert r1.status_code == 201
        r2 = client.post(
            "/cart/?user_id=103",
            json={"product_id": product["id"], "quantity": 3},
        )
        assert r2.status_code == 201

        cart = client.get("/cart/103").json()
        assert cart["items"][0]["quantity"] == 5

    def test_vider_panier(self, client):
        product = self._creer_produit(client)
        add = client.post(
            "/cart/?user_id=104",
            json={"product_id": product["id"], "quantity": 1},
        )
        assert add.status_code == 201

        response = client.delete("/cart/104")
        assert response.status_code == 204

        cart = client.get("/cart/104").json()
        assert cart["items"] == []
