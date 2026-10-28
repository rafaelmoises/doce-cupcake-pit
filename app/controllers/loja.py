from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from app.extensions import db
from app.models import Categoria, Produto
from app.services.pedido_service import carrinho_detalhado

bp = Blueprint("loja", __name__)


@bp.route("/")
def vitrine():
    q = request.args.get("q", "").strip()
    cat = request.args.get("categoria", type=int)
    consulta = Produto.query.filter_by(ativo=True)
    if q:
        consulta = consulta.filter(Produto.nome.ilike(f"%{q}%"))
    if cat:
        consulta = consulta.filter_by(categoria_id=cat)
    produtos = consulta.order_by(Produto.nome).all()
    return render_template("loja/vitrine.html", produtos=produtos, categorias=Categoria.query.order_by(Categoria.nome).all(), q=q, cat=cat)


@bp.route("/produto/<int:pid>")
def detalhe(pid):
    p = db.session.get(Produto, pid)
    if not p or not p.ativo:
        abort(404)
    return render_template("loja/detalhe.html", p=p)


@bp.route("/carrinho")
def carrinho():
    linhas, total = carrinho_detalhado(session.get("carrinho", {}))
    return render_template("loja/carrinho.html", linhas=linhas, total=total)


def _qtd():
    try:
        return max(int(request.form.get("quantidade", 1)), 0)
    except ValueError:
        return 1


@bp.route("/carrinho/adicionar/<int:pid>", methods=["POST"])
def adicionar(pid):
    p = db.session.get(Produto, pid)
    if not p or not p.ativo:
        abort(404)
    c = dict(session.get("carrinho", {}))
    nova = c.get(str(pid), 0) + max(_qtd(), 1)
    if nova > p.estoque:
        flash(f'Só temos {p.estoque} unidade(s) de "{p.nome}" em estoque.', "erro")
        return redirect(request.referrer or url_for("loja.vitrine"))
    c[str(pid)] = nova
    session["carrinho"] = c
    flash(f'"{p.nome}" adicionado ao carrinho.', "ok")
    return redirect(url_for("loja.carrinho"))


@bp.route("/carrinho/atualizar/<int:pid>", methods=["POST"])
def atualizar(pid):
    c = dict(session.get("carrinho", {}))
    p = db.session.get(Produto, pid)
    qtd = _qtd()
    if str(pid) in c and p:
        if qtd == 0:
            c.pop(str(pid))
        elif qtd > p.estoque:
            flash(f'Só temos {p.estoque} unidade(s) de "{p.nome}" em estoque.', "erro")
        else:
            c[str(pid)] = qtd
    session["carrinho"] = c
    return redirect(url_for("loja.carrinho"))


@bp.route("/carrinho/remover/<int:pid>", methods=["POST"])
def remover(pid):
    c = dict(session.get("carrinho", {}))
    c.pop(str(pid), None)
    session["carrinho"] = c
    flash("Item removido do carrinho.", "ok")
    return redirect(url_for("loja.carrinho"))
