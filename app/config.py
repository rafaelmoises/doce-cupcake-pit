import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-troque-em-producao")
    _db = os.environ.get("DATABASE_URL", "sqlite:///cupcakes.db")
    # Render/Heroku/Neon entregam "postgres://" ou "postgresql://"; força o driver psycopg2
    if _db.startswith("postgres://"):
        _db = "postgresql://" + _db[len("postgres://"):]
    if _db.startswith("postgresql://"):
        _db = "postgresql+psycopg2://" + _db[len("postgresql://"):]
    SQLALCHEMY_DATABASE_URI = _db
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TAXA_ENTREGA = "8.00"          # RN04
    FRETE_GRATIS_A_PARTIR_DE = "120.00"  # RN04


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "teste"
    WTF_CSRF_ENABLED = False
