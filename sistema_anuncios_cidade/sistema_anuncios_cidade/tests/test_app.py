import pytest
from app import create_app
from app.extensions import db
from app.models import User, Category, Ad

@pytest.fixture()
def app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test",
        "ADMIN_EMAIL": "admin@test.local",
        "ADMIN_PASSWORD": "admin12345",
        "UPLOAD_FOLDER": "/tmp/anuncios-test-uploads",
    })
    with app.app_context():
        db.drop_all()
        db.create_all()
        db.session.add(Category(name="Eletrônicos"))
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()

def test_home_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"FEIRA DA CIDADE" in response.data

def test_seller_registration(client):
    response = client.post("/conta/cadastro", data={
        "name": "Vendedor Teste", "phone": "35999999999",
        "email": "vendedor@test.local", "password": "senha12345"
    }, follow_redirects=True)
    assert response.status_code == 200
    with client.application.app_context():
        assert User.query.filter_by(email="vendedor@test.local").first() is not None

def test_duplicate_email_rejected(client):
    data = {"name":"Teste","phone":"35999999999","email":"dup@test.local","password":"senha12345"}
    client.post("/conta/cadastro", data=data)
    response = client.post("/conta/cadastro", data=data)
    assert "Este e-mail já está cadastrado".encode("utf-8") in response.data
