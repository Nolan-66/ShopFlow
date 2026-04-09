import pytest

from app.services.stock import verifier_stock, reserver_stock, liberer_stock

REDIS_MOCK_PATH = "app.services.stock.redis_client"


@pytest.mark.unit
class TestVerifierStock:
    def test_stock_suffisant(self, product_sample):
        assert verifier_stock(product_sample, 5) is True

    def test_stock_insuffisant(self, product_sample):
        assert verifier_stock(product_sample, 999) is False

    def test_stock_exactement_disponible(self, product_sample):
        assert verifier_stock(product_sample, 10) is True

    def test_quantite_zero_leve_exception(self, product_sample):
        with pytest.raises(ValueError):
            verifier_stock(product_sample, 0)

    def test_quantite_negative_leve_exception(self, product_sample):
        with pytest.raises(ValueError):
            verifier_stock(product_sample, -1)


class TestReserverStock:
    def test_reservation_reussie(self, product_sample, db_session, mocker):
        mock_redis = mocker.patch(REDIS_MOCK_PATH)

        stock_avant = product_sample.stock
        updated = reserver_stock(product_sample, 3, db_session)

        assert updated.stock == stock_avant - 3
        mock_redis.delete.assert_called_once()

    def test_reservation_verifie_cle_redis(self, product_sample, db_session, mocker):
        mock_redis = mocker.patch(REDIS_MOCK_PATH)

        reserver_stock(product_sample, 1, db_session)

        expected_key = f"product:{product_sample.id}:stock"
        mock_redis.delete.assert_called_once_with(expected_key)

    def test_stock_insuffisant_leve_exception(self, product_sample, db_session, mocker):
        mocker.patch(REDIS_MOCK_PATH)

        with pytest.raises(ValueError, match="insuffisant"):
            reserver_stock(product_sample, 999, db_session)

    def test_stock_insuffisant_ne_modifie_pas_bdd(self, product_sample, db_session, mocker):
        mocker.patch(REDIS_MOCK_PATH)

        stock_avant = product_sample.stock

        with pytest.raises(ValueError):
            reserver_stock(product_sample, 999, db_session)

        assert product_sample.stock == stock_avant

    def test_redis_non_appele_si_exception(self, product_sample, db_session, mocker):
        mock_redis = mocker.patch(REDIS_MOCK_PATH)

        with pytest.raises(ValueError):
            reserver_stock(product_sample, 999, db_session)

        mock_redis.delete.assert_not_called()


class TestLibererStock:
    def test_liberation_stock(self, product_sample, db_session, mocker):
        mock_redis = mocker.patch(REDIS_MOCK_PATH)

        stock_avant = product_sample.stock
        updated = liberer_stock(product_sample, 2, db_session)

        assert updated.stock == stock_avant + 2

        expected_key = f"product:{product_sample.id}:stock"
        mock_redis.set.assert_called_once_with(expected_key, updated.stock)