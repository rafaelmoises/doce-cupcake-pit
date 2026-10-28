"""Carga inicial: categorias, cupcakes e usuários de demonstração."""
import os

from app.extensions import db
from app.models import Categoria, Produto, Usuario

CATALOGO = {
    "Clássicos": [
        ("Baunilha com Buttercream", "Massa fofinha de baunilha com cobertura cremosa de buttercream.", "7.50", 30),
        ("Chocolate Belga", "Massa de chocolate 50% cacau com ganache de chocolate belga.", "9.00", 25),
        ("Red Velvet", "Massa aveludada vermelha com cream cheese frosting.", "10.00", 20),
    ],
    "Frutas": [
        ("Limão Siciliano", "Massa cítrica com recheio de curd de limão e merengue.", "8.50", 18),
        ("Morango com Chantilly", "Recheio de geleia de morango e chantilly fresco.", "9.50", 15),
        ("Maracujá", "Massa amanteigada com mousse de maracujá.", "8.50", 12),
    ],
    "Especiais": [
        ("Brigadeiro Gourmet", "Massa de chocolate recheada com brigadeiro cremoso e granulado belga.", "10.50", 22),
        ("Doce de Leite com Coco", "Doce de leite argentino e coco queimado.", "10.00", 16),
        ("Cookies & Cream", "Massa de baunilha com pedaços de cookie e creme de biscoito.", "11.00", 3),
    ],
}


def seed():
    if Categoria.query.first():
        return False
    for nome, produtos in CATALOGO.items():
        cat = Categoria(nome=nome, descricao=f"Cupcakes {nome.lower()}")
        db.session.add(cat)
        for n, d, preco, est in produtos:
            cat.produtos.append(Produto(nome=n, descricao=d, preco=preco, estoque=est))
    admin = Usuario(nome="Administrador", email=os.environ.get("ADMIN_EMAIL", "admin@cupcakes.com"), perfil="admin")
    admin.definir_senha(os.environ.get("ADMIN_PASSWORD", "Admin@123"))
    cliente = Usuario(nome="Cliente Demo", email="cliente@cupcakes.com", telefone="11999990000")
    cliente.definir_senha("Cliente@123")
    db.session.add_all([admin, cliente])
    db.session.commit()
    return True
