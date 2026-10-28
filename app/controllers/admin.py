from decimal import Decimal, InvalidOperation

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app.extensions import db
from app.models import Categoria, Pedido, Produto, STATUS_ENTREGA, ROTULO_STATUS
from app.services import pedido_service as svc
from app.controllers.helpers import admin_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/produtos")
@admin_required
def produtos():
    return render_template("admin/produtos.html", produtos=Produto.query.order_by(Produto.nome).all())


def _ler_produto(form):
    erros, dados = [], {}
    dados["nome"] = form.get("nome", "").strip()
    dados["descricao"] = form.get("descricao", "").strip()
    dados["imagem_url"] = form.get("imagem_url", "").strip() or None
    if not dados["nome"]:
        erros.append("Informe o nome do produto.")
    try:
        dados["preco"] = Decimal(form.get("preco", "").replace(",", "."))
        if dados["preco"] < 0:
            raise InvalidOperation
    except InvalidOperation:
        erros.append("Preço inválido.")
    try:
        dados["estoque"] = int(form.get("estoque", ""))
        if dados["estoque"] < 0:
            raise ValueError
    except ValueError:
        erros.append("Estoque deve ser um número inteiro maior ou igual a zero.")
    cat = db.session.get(Categoria, form.get("categoria_id", type=int)) if form.get("categoria_id") else None
    if not cat:
        erros.append("Escolha uma categoria.")
    else:
        dados["categoria_id"] = cat.id
    return dados, erros


@bp.route("/produtos/novo", methods=["GET", "POST"])
@admin_required
def produto_novo():
    if request.method == "POST":
        dados, erros = _ler_produto(request.form)
        if erros:
            for e in erros:
                flash(e, "erro")
            return render_template("admin/produto_form.html", p=None, form=request.form, categorias=Categoria.query.all()), 400
        db.session.add(Produto(**dados, ativo=True))
        db.session.commit()
        flash("Produto cadastrado.", "ok")
        return redirect(url_for("admin.produtos"))
    return render_template("admin/produto_form.html", p=None, form={}, categorias=Categoria.query.all())


@bp.route("/produtos/<int:pid>/editar", methods=["GET", "POST"])
@admin_required
def produto_editar(pid):
    p = db.session.get(Produto, pid) or abort(404)
    if request.method == "POST":
        dados, erros = _ler_produto(request.form)
        if erros:
            for e in erros:
                flash(e, "erro")
            return render_template("admin/produto_form.html", p=p, form=request.form, categorias=Categoria.query.all()), 400
        for k, v in dados.items():
            setattr(p, k, v)
        db.session.commit()
        flash("Produto atualizado.", "ok")
        return redirect(url_for("admin.produtos"))
    return render_template("admin/produto_form.html", p=p, form={}, categorias=Categoria.query.all())


@bp.route("/produtos/<int:pid>/alternar", methods=["POST"])
@admin_required
def produto_alternar(pid):
    p = db.session.get(Produto, pid) or abort(404)
    p.ativo = not p.ativo
    db.session.commit()
    flash("Produto ativado." if p.ativo else "Produto desativado.", "ok")
    return redirect(url_for("admin.produtos"))


@bp.route("/categorias", methods=["GET", "POST"])
@admin_required
def categorias():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        if not nome:
            flash("Informe o nome da categoria.", "erro")
        elif Categoria.query.filter_by(nome=nome).first():
            flash("Já existe uma categoria com esse nome.", "erro")
        else:
            db.session.add(Categoria(nome=nome, descricao=request.form.get("descricao", "").strip()))
            db.session.commit()
            flash("Categoria criada.", "ok")
        return redirect(url_for("admin.categorias"))
    return render_template("admin/categorias.html", categorias=Categoria.query.order_by(Categoria.nome).all())


@bp.route("/categorias/<int:cid>/excluir", methods=["POST"])
@admin_required
def categoria_excluir(cid):
    c = db.session.get(Categoria, cid) or abort(404)
    if c.produtos:
        flash("Não é possível excluir uma categoria que possui produtos.", "erro")
    else:
        db.session.delete(c)
        db.session.commit()
        flash("Categoria excluída.", "ok")
    return redirect(url_for("admin.categorias"))


@bp.route("/pedidos")
@admin_required
def pedidos():
    return render_template("admin/pedidos.html", pedidos=Pedido.query.order_by(Pedido.id.desc()).all(),
                           etapas=STATUS_ENTREGA, rotulos=ROTULO_STATUS)


@bp.route("/pedidos/<int:pid>/status", methods=["POST"])
@admin_required
def pedido_status(pid):
    p = db.session.get(Pedido, pid) or abort(404)
    try:
        svc.avancar_status(p.entrega, request.form.get("status", ""))
        flash(f"Pedido #{p.id} atualizado para {p.entrega.rotulo}.", "ok")
    except svc.ErroDeNegocio as e:
        flash(str(e), "erro")
    return redirect(url_for("admin.pedidos"))


@bp.route("/pedidos/<int:pid>/pagamento", methods=["POST"])
@admin_required
def pedido_pagamento(pid):
    p = db.session.get(Pedido, pid) or abort(404)
    try:
        svc.confirmar_pagamento(p)
        flash(f"Pagamento do pedido #{p.id} confirmado.", "ok")
    except svc.ErroDeNegocio as e:
        flash(str(e), "erro")
    return redirect(url_for("admin.pedidos"))
