# 🧁 Doce Cupcake – Loja Virtual de Cupcakes

Projeto Integrador Transdisciplinar em Engenharia de Software (PIT II).
Vitrine, carrinho, pedido, pagamento (simulado), acompanhamento de entrega e painel administrativo.

**Stack:** Python 3 · Flask (padrão MVC + camada de serviço) · SQLAlchemy · PostgreSQL (SQLite em dev/testes) · HTML/CSS/JS · pytest

## Executar localmente
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python wsgi.py                                          # http://127.0.0.1:5000
pytest --cov=app                                        # testes (31) e cobertura
```
O banco e os dados de exemplo são criados no primeiro acesso.

| Perfil | E-mail | Senha |
|---|---|---|
| Administrador | admin@cupcakes.com | Admin@123 |
| Cliente | cliente@cupcakes.com | Cliente@123 |

> Em produção defina `ADMIN_EMAIL`, `ADMIN_PASSWORD` e `SECRET_KEY`.

## Estrutura
```
app/models        # Model: entidades e integridade
app/controllers   # Controller: rotas (auth, loja, pedido, admin)
app/services      # regras de negócio (RN03–RN07)
app/templates     # View: telas Jinja2
app/static        # CSS
tests/            # pytest: modelos, serviço e rotas
docs/situacao1    # PIT II S1: DER, modelo lógico/físico, dicionário, SQL
docs/situacao2    # PIT II S2: manual de uso
docs/situacao3    # PIT II S3: formulário de testes, laudo, evidências
```

## Publicar no Render
1. Suba o projeto para o GitHub.
2. No Render: **New → Blueprint** e aponte para o repositório (usa o `render.yaml`).
3. Informe `ADMIN_PASSWORD` e aguarde o deploy.

## Regras de negócio
RN01 e-mail único · RN02 senha ≥ 8 com hash · RN03 estoque suficiente · RN04 taxa R$ 8 (grátis ≥ R$ 120 ou retirada) ·
RN05 preço congelado no pedido · RN06 Pix/cartão aprovados, boleto pendente · RN07 ordem dos status · RN08 painel só para admin.
