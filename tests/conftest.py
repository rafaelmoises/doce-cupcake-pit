import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import Categoria, Produto, Usuario


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        cat = Categoria(nome="Clássicos")
        db.session.add(cat)
        db.session.add_all([
            Produto(nome="Baunilha", preco="10.00", estoque=5, categoria=cat),
            Produto(nome="Chocolate", preco="50.00", estoque=2, categoria=cat),
            Produto(nome="Inativo", preco="5.00", estoque=9, categoria=cat, ativo=False),
        ])
        admin = Usuario(nome="Admin", email="admin@t.com", perfil="admin"); admin.definir_senha("Admin@123")
        cli = Usuario(nome="Maria Souza", email="maria@t.com"); cli.definir_senha("Senha@123")
        db.session.add_all([admin, cli])
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, email, senha):
    return client.post("/login", data={"email": email, "senha": senha})


@pytest.fixture
def cliente_logado(client):
    login(client, "maria@t.com", "Senha@123")
    return client


@pytest.fixture
def admin_logado(client):
    login(client, "admin@t.com", "Admin@123")
    return client


ENDERECO = {"tipo": "entrega", "metodo": "pix", "cep": "01001-000", "logradouro": "Praça da Sé",
            "numero": "10", "bairro": "Sé", "cidade": "São Paulo", "uf": "SP"}
