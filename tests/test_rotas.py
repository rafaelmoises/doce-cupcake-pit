from app.extensions import db
from app.models import Pedido, Produto, Usuario
from tests.conftest import ENDERECO, login


def _pid(nome):
    return Produto.query.filter_by(nome=nome).first().id


# ---------- vitrine ----------
def test_vitrine_lista_apenas_ativos(client):
    r = client.get("/")
    assert r.status_code == 200 and b"Baunilha" in r.data and b"Inativo" not in r.data


def test_busca_e_filtro(client):
    assert b"Chocolate" not in client.get("/?q=baun").data
    assert b"Baunilha" in client.get("/?q=baun").data


def test_produto_inexistente_404(client):
    assert client.get("/produto/9999").status_code == 404
    assert b"Voltar" in client.get("/produto/9999").data


# ---------- cadastro / login ----------
def test_cadastro_valida_senha_curta_e_email_duplicado(client):
    r = client.post("/cadastro", data={"nome": "Ana", "email": "ana@t.com", "senha": "123"})
    assert r.status_code == 400 and b"m\xc3\xadnimo 8" in r.data
    r = client.post("/cadastro", data={"nome": "Ana", "email": "maria@t.com", "senha": "12345678"})
    assert r.status_code == 400 and "já está cadastrado".encode() in r.data


def test_cadastro_ok_faz_login(client):
    r = client.post("/cadastro", data={"nome": "Ana", "email": "ana@t.com", "senha": "12345678"}, follow_redirects=True)
    assert r.status_code == 200 and b"Ana" in r.data
    assert Usuario.query.filter_by(email="ana@t.com").first() is not None


def test_login_invalido_nao_revela_campo(client):
    r = login(client, "maria@t.com", "errada")
    assert r.status_code == 401 and "E-mail ou senha inválidos".encode() in r.data


def test_login_bloqueia_open_redirect(client):
    r = client.post("/login?next=//evil.com", data={"email": "maria@t.com", "senha": "Senha@123"})
    assert "evil.com" not in r.headers["Location"]


# ---------- carrinho ----------
def test_carrinho_adicionar_atualizar_remover(client):
    pid = _pid("Baunilha")
    client.post(f"/carrinho/adicionar/{pid}", data={"quantidade": 2})
    assert b"R$ 20,00" in client.get("/carrinho").data
    client.post(f"/carrinho/atualizar/{pid}", data={"quantidade": 3})
    assert b"R$ 30,00" in client.get("/carrinho").data
    client.post(f"/carrinho/remover/{pid}")
    assert "vazio".encode() in client.get("/carrinho").data


def test_carrinho_nao_excede_estoque(client):
    pid = _pid("Chocolate")
    r = client.post(f"/carrinho/adicionar/{pid}", data={"quantidade": 5}, follow_redirects=True)
    assert "Só temos 2".encode() in r.data


def test_nao_adiciona_produto_inativo(client):
    assert client.post(f"/carrinho/adicionar/{_pid('Inativo')}", data={"quantidade": 1}).status_code == 404


# ---------- checkout ----------
def test_checkout_exige_login(client):
    r = client.get("/pedido/finalizar")
    assert r.status_code == 302 and "/login" in r.headers["Location"]


def test_fluxo_completo_de_compra(cliente_logado):
    c = cliente_logado
    c.post(f"/carrinho/adicionar/{_pid('Baunilha')}", data={"quantidade": 2})
    r = c.post("/pedido/finalizar", data=ENDERECO, follow_redirects=True)
    assert r.status_code == 200 and b"realizado com sucesso" in r.data
    ped = Pedido.query.one()
    assert ped.total == 28 and db.session.get(Produto, _pid("Baunilha")).estoque == 3
    assert b"Meus pedidos" in c.get("/pedidos").data and f"#{ped.id}".encode() in c.get("/pedidos").data


def test_checkout_endereco_incompleto(cliente_logado):
    cliente_logado.post(f"/carrinho/adicionar/{_pid('Baunilha')}", data={"quantidade": 1})
    r = cliente_logado.post("/pedido/finalizar", data={"tipo": "entrega", "metodo": "pix"})
    assert r.status_code == 400 and b"endere" in r.data and Pedido.query.count() == 0


def test_checkout_erro_de_estoque_mostra_tela_de_erro(cliente_logado):
    c = cliente_logado
    pid = _pid("Chocolate")
    c.post(f"/carrinho/adicionar/{pid}", data={"quantidade": 2})
    db.session.get(Produto, pid).estoque = 1  # alguém comprou antes
    db.session.commit()
    r = c.post("/pedido/finalizar", data=ENDERECO)
    assert r.status_code == 409 and "Produto indisponível".encode() in r.data and Pedido.query.count() == 0


def test_usuario_nao_ve_pedido_de_outro(client, app):
    c = client
    login(c, "maria@t.com", "Senha@123")
    c.post(f"/carrinho/adicionar/{_pid('Baunilha')}", data={"quantidade": 1})
    c.post("/pedido/finalizar", data=ENDERECO)
    pid = Pedido.query.one().id
    c.post("/logout")
    u = Usuario(nome="Outro", email="o@t.com"); u.definir_senha("12345678"); db.session.add(u); db.session.commit()
    login(c, "o@t.com", "12345678")
    assert c.get(f"/pedidos/{pid}").status_code == 404


# ---------- admin ----------
def test_admin_protegido(client, cliente_logado):
    assert cliente_logado.get("/admin/produtos").status_code == 403
    client.post("/logout")
    assert client.get("/admin/produtos").status_code == 302


def test_admin_crud_produto(admin_logado):
    c = admin_logado
    cid = 1
    r = c.post("/admin/produtos/novo", data={"nome": "Novo", "categoria_id": cid, "preco": "12,50", "estoque": "4"}, follow_redirects=True)
    assert b"Produto cadastrado" in r.data
    p = Produto.query.filter_by(nome="Novo").first()
    assert p.preco == 12.5
    c.post(f"/admin/produtos/{p.id}/editar", data={"nome": "Novo2", "categoria_id": cid, "preco": "13", "estoque": "6"})
    assert db.session.get(Produto, p.id).nome == "Novo2"
    c.post(f"/admin/produtos/{p.id}/alternar")
    assert db.session.get(Produto, p.id).ativo is False


def test_admin_produto_invalido(admin_logado):
    r = admin_logado.post("/admin/produtos/novo", data={"nome": "", "categoria_id": 1, "preco": "abc", "estoque": "-1"})
    assert r.status_code == 400 and b"Pre\xc3\xa7o inv\xc3\xa1lido" in r.data


def test_admin_atualiza_status_e_confirma_boleto(cliente_logado, client):
    c = cliente_logado
    c.post(f"/carrinho/adicionar/{_pid('Baunilha')}", data={"quantidade": 1})
    c.post("/pedido/finalizar", data={**ENDERECO, "metodo": "boleto"})
    pid = Pedido.query.one().id
    c.post("/logout")
    login(c, "admin@t.com", "Admin@123")
    r = c.post(f"/admin/pedidos/{pid}/status", data={"status": "em_preparo"}, follow_redirects=True)
    assert "pagamento ainda não foi confirmado".encode() in r.data
    c.post(f"/admin/pedidos/{pid}/pagamento")
    r = c.post(f"/admin/pedidos/{pid}/status", data={"status": "em_preparo"}, follow_redirects=True)
    assert b"Em preparo" in r.data


def test_admin_categoria_com_produtos_nao_exclui(admin_logado):
    r = admin_logado.post("/admin/categorias/1/excluir", follow_redirects=True)
    assert "possui produtos".encode() in r.data
