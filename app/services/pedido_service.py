"""Regras de negócio do pedido (camada de serviço usada pelos controllers)."""
import re
from datetime import date, datetime, timedelta
from decimal import Decimal

from flask import current_app

from app.extensions import db
from app.models import (STATUS_ENTREGA, Endereco, Entrega, ItemPedido, Pagamento,
                        Pedido, Produto)

METODOS = ("pix", "cartao", "boleto")
TIPOS_ENTREGA = ("entrega", "retirada")


class ErroDeNegocio(Exception):
    """Erro de regra de negócio, com mensagem pronta para o usuário."""


class EstoqueInsuficiente(ErroDeNegocio):
    pass


def calcular_taxa(subtotal, tipo):
    """RN04: taxa fixa; grátis na retirada ou a partir do valor mínimo."""
    if tipo == "retirada":
        return Decimal("0.00")
    limite = Decimal(current_app.config["FRETE_GRATIS_A_PARTIR_DE"])
    if Decimal(subtotal) >= limite:
        return Decimal("0.00")
    return Decimal(current_app.config["TAXA_ENTREGA"])


def carrinho_detalhado(carrinho):
    """Converte {produto_id: qtd} em lista de (produto, qtd, subtotal) e total."""
    linhas, total = [], Decimal("0")
    for pid, qtd in carrinho.items():
        produto = db.session.get(Produto, int(pid))
        if produto is None or not produto.ativo:
            continue
        sub = Decimal(produto.preco) * qtd
        linhas.append({"produto": produto, "quantidade": qtd, "subtotal": sub})
        total += sub
    return linhas, total


def validar_endereco(dados):
    obrig = ["cep", "logradouro", "numero", "bairro", "cidade", "uf"]
    faltando = [c for c in obrig if not (dados.get(c) or "").strip()]
    if faltando:
        raise ErroDeNegocio("Preencha o endereço completo para entrega (CEP, rua, número, bairro, cidade e UF).")
    if not re.fullmatch(r"\d{5}-?\d{3}", dados["cep"].strip()):
        raise ErroDeNegocio("CEP inválido. Use o formato 00000-000.")
    if len(dados["uf"].strip()) != 2:
        raise ErroDeNegocio("UF deve ter 2 letras.")


def criar_pedido(usuario, carrinho, tipo, metodo, dados_endereco=None):
    """Cria pedido, itens, pagamento e entrega em uma única transação (RN03, RN05, RN06)."""
    if not carrinho:
        raise ErroDeNegocio("Seu carrinho está vazio.")
    if tipo not in TIPOS_ENTREGA:
        raise ErroDeNegocio("Escolha entrega ou retirada.")
    if metodo not in METODOS:
        raise ErroDeNegocio("Escolha uma forma de pagamento.")
    endereco = None
    if tipo == "entrega":
        validar_endereco(dados_endereco or {})
        endereco = Endereco(usuario_id=usuario.id, **{k: (dados_endereco.get(k) or "").strip()
                            for k in ["cep", "logradouro", "numero", "complemento", "bairro", "cidade"]},
                            uf=dados_endereco["uf"].strip().upper())

    try:
        pedido = Pedido(usuario_id=usuario.id, status="confirmado")
        problemas = []
        for pid, qtd in carrinho.items():
            # with_for_update: trava a linha no PostgreSQL para evitar venda dupla
            produto = db.session.query(Produto).filter_by(id=int(pid)).with_for_update().first()
            if produto is None or not produto.ativo:
                problemas.append("Um dos produtos do carrinho não está mais disponível.")
                continue
            if produto.estoque < qtd:
                problemas.append(f'"{produto.nome}" tem apenas {produto.estoque} unidade(s) em estoque.')
                continue
            produto.estoque -= qtd
            pedido.itens.append(ItemPedido(produto=produto, quantidade=qtd, preco_unitario=produto.preco))
        if problemas:
            raise EstoqueInsuficiente("Produto indisponível: " + " ".join(problemas))

        pedido.subtotal = sum((i.subtotal() for i in pedido.itens), Decimal("0"))
        pedido.taxa_entrega = calcular_taxa(pedido.subtotal, tipo)
        pedido.calcular_total()
        aprovado = metodo in ("pix", "cartao")
        pedido.pagamento = Pagamento(metodo=metodo, valor=pedido.total,
                                     status="aprovado" if aprovado else "pendente",
                                     pago_em=datetime.utcnow() if aprovado else None)
        pedido.entrega = Entrega(tipo=tipo, endereco=endereco, status="recebido",
                                 previsao=date.today() + timedelta(days=2))
        db.session.add(pedido)
        db.session.commit()
        return pedido
    except Exception:
        db.session.rollback()
        raise


def avancar_status(entrega, novo_status):
    """RN07: só permite avançar para o status seguinte."""
    if novo_status not in STATUS_ENTREGA:
        raise ErroDeNegocio("Status inválido.")
    atual, novo = STATUS_ENTREGA.index(entrega.status), STATUS_ENTREGA.index(novo_status)
    if novo != atual + 1:
        raise ErroDeNegocio("Só é possível avançar para o próximo status da entrega.")
    if novo_status == "em_preparo" and entrega.pedido.pagamento.status != "aprovado":
        raise ErroDeNegocio("O pagamento ainda não foi confirmado.")
    entrega.status = novo_status
    if novo_status == "entregue":
        entrega.entregue_em = datetime.utcnow()
    db.session.commit()


def confirmar_pagamento(pedido):
    if pedido.pagamento.status == "aprovado":
        raise ErroDeNegocio("Pagamento já confirmado.")
    pedido.pagamento.status = "aprovado"
    pedido.pagamento.pago_em = datetime.utcnow()
    db.session.commit()
