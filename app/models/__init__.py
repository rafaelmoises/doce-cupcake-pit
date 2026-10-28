from datetime import datetime, date
from decimal import Decimal

from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db

STATUS_ENTREGA = ["recebido", "em_preparo", "saiu_para_entrega", "entregue"]  # RN07
ROTULO_STATUS = {
    "recebido": "Recebido",
    "em_preparo": "Em preparo",
    "saiu_para_entrega": "Saiu para entrega",
    "entregue": "Entregue",
}


class Usuario(db.Model):
    __tablename__ = "usuarios"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), nullable=False, unique=True, index=True)  # RN01
    senha_hash = db.Column(db.String(255), nullable=False)
    telefone = db.Column(db.String(20))
    perfil = db.Column(db.String(10), nullable=False, default="cliente")
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    enderecos = db.relationship("Endereco", backref="usuario", cascade="all, delete-orphan")
    pedidos = db.relationship("Pedido", backref="usuario", order_by="Pedido.id.desc()")

    def definir_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)  # RN02

    def confere_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    @property
    def eh_admin(self):
        return self.perfil == "admin"


class Endereco(db.Model):
    __tablename__ = "enderecos"
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    cep = db.Column(db.String(9), nullable=False)
    logradouro = db.Column(db.String(160), nullable=False)
    numero = db.Column(db.String(10), nullable=False)
    complemento = db.Column(db.String(80))
    bairro = db.Column(db.String(80), nullable=False)
    cidade = db.Column(db.String(80), nullable=False)
    uf = db.Column(db.String(2), nullable=False)

    def __str__(self):
        comp = f", {self.complemento}" if self.complemento else ""
        return f"{self.logradouro}, {self.numero}{comp} - {self.bairro}, {self.cidade}/{self.uf} - CEP {self.cep}"


class Categoria(db.Model):
    __tablename__ = "categorias"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(60), nullable=False, unique=True)
    descricao = db.Column(db.String(200))
    produtos = db.relationship("Produto", backref="categoria")


class Produto(db.Model):
    __tablename__ = "produtos"
    id = db.Column(db.Integer, primary_key=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id"), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(500))
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    estoque = db.Column(db.Integer, nullable=False, default=0)
    imagem_url = db.Column(db.String(255))
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        db.CheckConstraint("preco >= 0", name="ck_produto_preco"),
        db.CheckConstraint("estoque >= 0", name="ck_produto_estoque"),
    )

    @property
    def disponivel(self):
        return self.ativo and self.estoque > 0


class Pedido(db.Model):
    __tablename__ = "pedidos"
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    status = db.Column(db.String(12), nullable=False, default="confirmado")
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    taxa_entrega = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    itens = db.relationship("ItemPedido", backref="pedido", cascade="all, delete-orphan")
    pagamento = db.relationship("Pagamento", backref="pedido", uselist=False, cascade="all, delete-orphan")
    entrega = db.relationship("Entrega", backref="pedido", uselist=False, cascade="all, delete-orphan")

    def calcular_total(self):
        self.subtotal = sum((i.subtotal() for i in self.itens), Decimal("0"))
        self.total = self.subtotal + (self.taxa_entrega or Decimal("0"))
        return self.total


class ItemPedido(db.Model):
    __tablename__ = "itens_pedido"
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedidos.id"), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id"), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Numeric(10, 2), nullable=False)  # RN05
    produto = db.relationship("Produto")

    __table_args__ = (db.CheckConstraint("quantidade > 0", name="ck_item_quantidade"),)

    def subtotal(self):
        return Decimal(self.preco_unitario) * self.quantidade


class Pagamento(db.Model):
    __tablename__ = "pagamentos"
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedidos.id"), nullable=False, unique=True)
    metodo = db.Column(db.String(10), nullable=False)  # pix | cartao | boleto
    status = db.Column(db.String(10), nullable=False, default="pendente")  # pendente | aprovado
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    pago_em = db.Column(db.DateTime)


class Entrega(db.Model):
    __tablename__ = "entregas"
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedidos.id"), nullable=False, unique=True)
    endereco_id = db.Column(db.Integer, db.ForeignKey("enderecos.id"))  # nulo na retirada
    tipo = db.Column(db.String(10), nullable=False)  # entrega | retirada
    status = db.Column(db.String(20), nullable=False, default="recebido")
    previsao = db.Column(db.Date)
    entregue_em = db.Column(db.DateTime)
    endereco = db.relationship("Endereco")

    @property
    def rotulo(self):
        return ROTULO_STATUS.get(self.status, self.status)

    @property
    def indice_status(self):
        return STATUS_ENTREGA.index(self.status)
