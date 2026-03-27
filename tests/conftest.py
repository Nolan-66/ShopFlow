import pytest
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Coupon, Product


fake = Faker("fr_FR")


@pytest.fixture(scope="function")
def db_engine():
    """BDD SQLite en mémoire, isolée pour chaque test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Session SQLAlchemy fraîche pour chaque test."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def product_sample(db_session):
    p = Product(
        name="Laptop Pro",
        price=999.99,
        stock=10,
        category="informatique",
    )
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


@pytest.fixture
def coupon_sample(db_session):
    c = Coupon(
        code="PROMO20",
        reduction=20.0,
        actif=True,
    )
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    return c


@pytest.fixture(scope="function")
def client(db_engine):
    """TestClient FastAPI avec override get_db vers la SQLite de test."""
    SessionTest = sessionmaker(bind=db_engine)

    def override_get_db():
        session = SessionTest()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture

def api_product(client):
    """Crée un produit via l'API et le retourne."""
    response = client.post(
        "/products/",
        json={
            "name": "Clavier Mécanique",
            "price": 89.99,
            "stock": 25,
            "category": "peripheriques",
        },
    )
    assert response.status_code == 201
    product = response.json()
    yield product
    client.delete(f"/products/{product['id']}")


@pytest.fixture

def api_coupon(client):
    """Crée un coupon via l'API et le retourne."""
    response = client.post(
        "/coupons/",
        json={"code": "TEST10", "reduction": 10.0, "actif": True},
    )
    assert response.status_code == 201
    yield response.json()


@pytest.fixture

def fake_product_data():
    """Payload produit réaliste généré avec Faker."""
    return {
        "name": fake.catch_phrase()[:50],
        "price": round(
            fake.pyfloat(min_value=1, max_value=2000, right_digits=2, positive=True),
            2,
        ),
        "stock": fake.random_int(min=0, max=500),
        "category": fake.random_element(
            ["informatique", "peripheriques", "audio", "gaming"]
        ),
    }


@pytest.fixture

def multiple_products(client):
    """Crée 5 produits différents via l'API."""
    faker_inst = Faker("fr_FR")
    products = []
    for i in range(5):
        r = client.post(
            "/products/",
            json={
                "name": faker_inst.word().capitalize() + f" {i}",
                "price": round(10.0 + i * 20, 2),
                "stock": 10,
            },
        )
        assert r.status_code == 201
        products.append(r.json())

    yield products

    for p in products:
        client.delete(f"/products/{p['id']}")
