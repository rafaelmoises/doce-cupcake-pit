from decimal import Decimal

import pytest

from app.extensions import db
from app.models import Pedido, Produto, Usuario
from app.services import pedido_service as svc

END = {"cep": "01001-000", "logradouro": "Rua A", "numero": "1", "bairro": "B", "cidade": "C", "uf": "SP"}


def _ids(app):
    return (Usuario.query.filter_by(email="maria@t.com").first(),
            Produto.query.filter_by(nome="Baunilha").first(),
            Produto.query.filter_by(nome="Chocolate").first())


def test_taxa_de_entrega_rn04(app):
    assert svc.calcular_taxa("50.00", "entrega") == Decimal("8.00")
    assert svc.calcular_taxa("120.00", "entrega") == Decimal("0.00")
    assert svc.calcular_taxa("10.00", "retirada") == Decimal("0.00")


def test_criar_pedido_baixa_estoque_e_congela_preco(app):
    u, baun, _ = _ids(app)
    ped = svc.criar_pedido(u, {str(baun.id): 2}, "entrega", "pix", END)
    assert ped.subtotal == Decimal("20.00") and ped.taxa_entrega == Decimal("8.00") and ped.total == Decimal("28.00")
    assert db.session.get(Produto, baun.id).estoque == 3
    assert ped.itens[0].preco_unitario == Decimal("10.00")
    assert ped.pagamento.status == "aprovado" and ped.entrega.status == "recebido"


def test_boleto_fica_pendente_rn06(app):
    u, baun, _ = _ids(app)
    ped = svc.criar_pedido(u, {str(baun.id): 1}, "retirada", "boleto")
    assert ped.pagamento.status == "pendente" and ped.taxa_entrega == 0 and ped.entrega.endereco is None


def test_estoque_insuficiente_nao_cria_pedido_nem_baixa_estoque_rn03(app):
    u, baun, choc = _ids(app)
    with pytest.raises(svc.EstoqueInsuficiente):
        svc.criar_pedido(u, {str(baun.id): 1, str(choc.id): 99}, "retirada", "pix")
    assert Pedido.query.count() == 0
    assert db.session.get(Produto, baun.id).estoque == 5  # rollback


def test_carrinho_vazio_e_dados_invalidos(app):
    u, baun, _ = _ids(app)
    with pytest.raises(svc.ErroDeNegocio):
        svc.criar_pedido(u, {}, "entrega", "pix", END)
    with pytest.raises(svc.ErroDeNegocio):
        svc.criar_pedido(u, {str(baun.id): 1}, "entrega", "dinheiro", END)
    with pytest.raises(svc.ErroDeNegocio):
        svc.criar_pedido(u, {str(baun.id): 1}, "entrega", "pix", {**END, "cep": "123"})
    with pytest.raises(svc.ErroDeNegocio):
        svc.criar_pedido(u, {str(baun.id): 1}, "entrega", "pix", {})


def test_transicao_de_status_rn07(app):
    u, baun, _ = _ids(app)
    ped = svc.criar_pedido(u, {str(baun.id): 1}, "retirada", "pix")
    with pytest.raises(svc.ErroDeNegocio):
        svc.avancar_status(ped.entrega, "entregue")  # pulou etapas
    svc.avancar_status(ped.entrega, "em_preparo")
    svc.avancar_status(ped.entrega, "saiu_para_entrega")
    svc.avancar_status(ped.entrega, "entregue")
    assert ped.entrega.entregue_em is not None


def test_nao_prepara_pedido_com_pagamento_pendente(app):
    u, baun, _ = _ids(app)
    ped = svc.criar_pedido(u, {str(baun.id): 1}, "retirada", "boleto")
    with pytest.raises(svc.ErroDeNegocio):
        svc.avancar_status(ped.entrega, "em_preparo")
    svc.confirmar_pagamento(ped)
    svc.avancar_status(ped.entrega, "em_preparo")
    with pytest.raises(svc.ErroDeNegocio):
        svc.confirmar_pagamento(ped)  # já confirmado
