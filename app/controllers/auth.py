import re

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.extensions import db
from app.models import Usuario

bp = Blueprint("auth", __name__)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        telefone = request.form.get("telefone", "").strip()
        senha = request.form.get("senha", "")
        erros = []
        if not nome:
            erros.append("Informe seu nome.")
        if not EMAIL_RE.match(email):
            erros.append("Informe um e-mail válido.")
        elif Usuario.query.filter_by(email=email).first():  # RN01
            erros.append("Este e-mail já está cadastrado.")
        if len(senha) < 8:  # RN02
            erros.append("A senha deve ter no mínimo 8 caracteres.")
        if erros:
            for e in erros:
                flash(e, "erro")
            return render_template("auth/cadastro.html", form=request.form), 400
        u = Usuario(nome=nome, email=email, telefone=telefone, perfil="cliente")
        u.definir_senha(senha)
        db.session.add(u)
        db.session.commit()
        session["user_id"] = u.id
        flash("Conta criada com sucesso! Bem-vindo(a).", "ok")
        return redirect(url_for("loja.vitrine"))
    return render_template("auth/cadastro.html", form={})


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        u = Usuario.query.filter_by(email=email).first()
        if u and u.confere_senha(request.form.get("senha", "")):
            carrinho = session.get("carrinho")
            session.clear()
            session["user_id"] = u.id
            if carrinho:
                session["carrinho"] = carrinho
            destino = request.args.get("next") or ""
            if u.eh_admin:
                return redirect(url_for("admin.produtos"))
            return redirect(destino if destino.startswith("/") and not destino.startswith("//") else url_for("loja.vitrine"))
        flash("E-mail ou senha inválidos.", "erro")  # sem revelar qual campo errou
        return render_template("auth/login.html"), 401
    return render_template("auth/login.html")


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Você saiu da sua conta.", "ok")
    return redirect(url_for("loja.vitrine"))
