from decimal import Decimal

from app.extensions import db
from app.models import ItemPedido, Pedido, Produto, Usuario


def test_senha_armazenada_como_hash_e_confere(app):
    u = Usuario.query.filter_by(email="maria@t.com").first()
    assert u.senha_hash != "Senha@123"
    assert u.confere_senha("Senha@123")
    assert not u.confere_senha("errada")


def test_email_unico(app):
    import pytest
    from sqlalchemy.exc import IntegrityError
    u = Usuario(nome="Outra", email="maria@t.com", senha_hash="x")
    db.session.add(u)
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_produto_disponivel(app):
    assert Produto.query.filter_by(nome="Baunilha").first().disponivel
    assert not Produto.query.filter_by(nome="Inativo").first().disponivel


def test_calcular_total_do_pedido(app):
    p = Produto.query.filter_by(nome="Baunilha").first()
    ped = Pedido(usuario_id=1, taxa_entrega=Decimal("8.00"))
    ped.itens.append(ItemPedido(produto=p, quantidade=3, preco_unitario=p.preco))
    assert ped.calcular_total() == Decimal("38.00")
