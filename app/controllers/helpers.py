import secrets
from functools import wraps

from flask import abort, flash, g, redirect, request, session, url_for

from app.extensions import db
from app.models import Usuario


def usuario_atual():
    uid = session.get("user_id")
    return db.session.get(Usuario, uid) if uid else None


def login_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if not g.usuario:
            flash("Faça login para continuar.", "erro")
            return redirect(url_for("auth.login", next=request.path))
        return f(*a, **kw)
    return wrapper


def admin_required(f):  # RN08
    @wraps(f)
    def wrapper(*a, **kw):
        if not g.usuario:
            flash("Faça login para continuar.", "erro")
            return redirect(url_for("auth.login", next=request.path))
        if not g.usuario.eh_admin:
            abort(403)
        return f(*a, **kw)
    return wrapper


def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return session["_csrf"]


def verificar_csrf(app):
    if app.config.get("TESTING"):
        return
    if request.method == "POST" and request.form.get("_csrf") != session.get("_csrf"):
        abort(400)
