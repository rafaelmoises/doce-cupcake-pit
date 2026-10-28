from decimal import Decimal

from flask import Blueprint, abort, flash, g, redirect, render_template, request, session, url_for

from app.extensions import db
from app.models import STATUS_ENTREGA, ROTULO_STATUS, Pedido
from app.services import pedido_service as svc
from app.controllers.helpers import login_required

bp = Blueprint("pedido", __name__)


@bp.route("/pedido/finalizar", methods=["GET", "POST"])
@login_required
def finalizar():
    carrinho = session.get("carrinho", {})
    linhas, subtotal = svc.carrinho_detalhado(carrinho)
    if not linhas:
        flash("Seu carrinho está vazio.", "erro")
        return redirect(url_for("loja.carrinho"))
    tipo = request.form.get("tipo", "entrega")
    taxa = svc.calcular_taxa(subtotal, tipo)
    if request.method == "POST":
        try:
            pedido = svc.criar_pedido(g.usuario, carrinho, tipo, request.form.get("metodo"), request.form)
        except svc.EstoqueInsuficiente as e:
            return render_template("pedido/erro_estoque.html", mensagem=str(e)), 409
        except svc.ErroDeNegocio as e:
            flash(str(e), "erro")
            return render_template("pedido/finalizar.html", linhas=linhas, subtotal=subtotal, taxa=taxa,
                                   total=subtotal + taxa, form=request.form), 400
        session.pop("carrinho", None)
        return redirect(url_for("pedido.confirmacao", pid=pedido.id))
    return render_template("pedido/finalizar.html", linhas=linhas, subtotal=subtotal, taxa=taxa,
                           total=subtotal + taxa, form={"tipo": "entrega", "metodo": "pix"})


def _pedido_do_usuario(pid):
    p = db.session.get(Pedido, pid)
    if not p or (p.usuario_id != g.usuario.id and not g.usuario.eh_admin):
        abort(404)
    return p


@bp.route("/pedido/<int:pid>/confirmacao")
@login_required
def confirmacao(pid):
    return render_template("pedido/confirmacao.html", p=_pedido_do_usuario(pid))


@bp.route("/pedidos")
@login_required
def meus_pedidos():
    return render_template("pedido/lista.html", pedidos=g.usuario.pedidos)


@bp.route("/pedidos/<int:pid>")
@login_required
def acompanhar(pid):
    return render_template("pedido/acompanhar.html", p=_pedido_do_usuario(pid), etapas=STATUS_ENTREGA, rotulos=ROTULO_STATUS)
