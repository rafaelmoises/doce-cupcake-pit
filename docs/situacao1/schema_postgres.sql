-- Esquema físico do Doce Cupcake (PostgreSQL). Gerado a partir dos modelos SQLAlchemy.

CREATE TABLE categorias (
	id SERIAL NOT NULL, 
	nome VARCHAR(60) NOT NULL, 
	descricao VARCHAR(200), 
	PRIMARY KEY (id), 
	UNIQUE (nome)
);

CREATE TABLE usuarios (
	id SERIAL NOT NULL, 
	nome VARCHAR(120) NOT NULL, 
	email VARCHAR(160) NOT NULL, 
	senha_hash VARCHAR(255) NOT NULL, 
	telefone VARCHAR(20), 
	perfil VARCHAR(10) NOT NULL, 
	criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_usuarios_email ON usuarios (email);

CREATE TABLE enderecos (
	id SERIAL NOT NULL, 
	usuario_id INTEGER NOT NULL, 
	cep VARCHAR(9) NOT NULL, 
	logradouro VARCHAR(160) NOT NULL, 
	numero VARCHAR(10) NOT NULL, 
	complemento VARCHAR(80), 
	bairro VARCHAR(80) NOT NULL, 
	cidade VARCHAR(80) NOT NULL, 
	uf VARCHAR(2) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(usuario_id) REFERENCES usuarios (id)
);

CREATE TABLE pedidos (
	id SERIAL NOT NULL, 
	usuario_id INTEGER NOT NULL, 
	status VARCHAR(12) NOT NULL, 
	subtotal NUMERIC(10, 2) NOT NULL, 
	taxa_entrega NUMERIC(10, 2) NOT NULL, 
	total NUMERIC(10, 2) NOT NULL, 
	criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(usuario_id) REFERENCES usuarios (id)
);

CREATE TABLE produtos (
	id SERIAL NOT NULL, 
	categoria_id INTEGER NOT NULL, 
	nome VARCHAR(100) NOT NULL, 
	descricao VARCHAR(500), 
	preco NUMERIC(10, 2) NOT NULL, 
	estoque INTEGER NOT NULL, 
	imagem_url VARCHAR(255), 
	ativo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_produto_preco CHECK (preco >= 0), 
	CONSTRAINT ck_produto_estoque CHECK (estoque >= 0), 
	FOREIGN KEY(categoria_id) REFERENCES categorias (id)
);

CREATE TABLE entregas (
	id SERIAL NOT NULL, 
	pedido_id INTEGER NOT NULL, 
	endereco_id INTEGER, 
	tipo VARCHAR(10) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	previsao DATE, 
	entregue_em TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (pedido_id), 
	FOREIGN KEY(pedido_id) REFERENCES pedidos (id), 
	FOREIGN KEY(endereco_id) REFERENCES enderecos (id)
);

CREATE TABLE itens_pedido (
	id SERIAL NOT NULL, 
	pedido_id INTEGER NOT NULL, 
	produto_id INTEGER NOT NULL, 
	quantidade INTEGER NOT NULL, 
	preco_unitario NUMERIC(10, 2) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_item_quantidade CHECK (quantidade > 0), 
	FOREIGN KEY(pedido_id) REFERENCES pedidos (id), 
	FOREIGN KEY(produto_id) REFERENCES produtos (id)
);

CREATE TABLE pagamentos (
	id SERIAL NOT NULL, 
	pedido_id INTEGER NOT NULL, 
	metodo VARCHAR(10) NOT NULL, 
	status VARCHAR(10) NOT NULL, 
	valor NUMERIC(10, 2) NOT NULL, 
	pago_em TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (pedido_id), 
	FOREIGN KEY(pedido_id) REFERENCES pedidos (id)
);
