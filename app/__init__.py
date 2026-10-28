from flask import Flask, g, render_template, session

from app.config import Config
from app.extensions import db


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)
    db.init_app(app)

    from app.controllers import admin, auth, helpers, loja, pedido
    for m in (auth, loja, pedido, admin):
        app.register_blueprint(m.bp)

    @app.before_request
    def _antes():
        helpers.verificar_csrf(app)
        g.usuario = helpers.usuario_atual()

    @app.context_processor
    def _ctx():
        carrinho = session.get("carrinho", {})
        return {"csrf_token": helpers.csrf_token, "qtd_carrinho": sum(carrinho.values()),
                "usuario": g.get("usuario")}

    @app.template_filter("brl")
    def brl(v):
        s = f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {s}"

    @app.template_filter("data")
    def data(v):
        return v.strftime("%d/%m/%Y %H:%M") if hasattr(v, "hour") else (v.strftime("%d/%m/%Y") if v else "-")

    for codigo, titulo, msg in [(403, "Acesso negado", "Você não tem permissão para acessar esta página."),
                                (404, "Página não encontrada", "O endereço que você tentou acessar não existe."),
                                (400, "Requisição inválida", "Não foi possível processar sua solicitação. Tente novamente."),
                                (500, "Erro interno", "Algo deu errado do nosso lado. Tente novamente em instantes.")]:
        app.register_error_handler(codigo, lambda e, c=codigo, t=titulo, m=msg: (render_template("erro.html", codigo=c, titulo=t, mensagem=m), c))

    with app.app_context():
        db.create_all()
    return app
