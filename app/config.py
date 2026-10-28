import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-troque-em-producao")
    _db = os.environ.get("DATABASE_URL", "sqlite:///cupcakes.db")
    # Render/Heroku entregam "postgres://", o SQLAlchemy exige "postgresql://"
    SQLALCHEMY_DATABASE_URI = _db.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TAXA_ENTREGA = "8.00"          # RN04
    FRETE_GRATIS_A_PARTIR_DE = "120.00"  # RN04


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "teste"
    WTF_CSRF_ENABLED = False
