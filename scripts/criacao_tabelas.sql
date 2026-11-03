CREATE TABLE cidade (
    id_cidade INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(100) NOT NULL
);

CREATE TABLE bairro (
    id_bairro INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(100) NOT NULL,
    id_cidade INTEGER NOT NULL,

    CONSTRAINT fk_bairro_cidade
        FOREIGN KEY (id_cidade)
        REFERENCES cidade(id_cidade)
);

CREATE TABLE endereco (
    id_endereco INTEGER PRIMARY KEY AUTOINCREMENT,
    logradouro VARCHAR(100) NOT NULL,
    id_bairro INTEGER NOT NULL,
    cep VARCHAR(10),
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,

    CONSTRAINT fk_endereco_bairro
        FOREIGN KEY (id_bairro)
        REFERENCES bairro(id_bairro)
);

CREATE TABLE distrito_sanitario (
    id_distrito INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(100) NOT NULL,
    regiao_rpa INTEGER NOT NULL CHECK (regiao_rpa > 0)
);

CREATE TABLE servico_saude (
    id_servico INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(100) NOT NULL,
    sigla VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE unidade_saude (
    id_unidade INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(100) NOT NULL,
    id_servico VARCHAR(100) NOT NULL,
    fone VARCHAR(20) NOT NULL UNIQUE,
    id_endereco INTEGER NOT NULL,
    id_distrito INTEGER NOT NULL,
    horario_atendimento VARCHAR(100) NOT NULL, 
    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_unidade_endereco
        FOREIGN KEY (id_endereco)
        REFERENCES endereco(id_endereco),

    CONSTRAINT fk_servico_saude
        FOREIGN KEY (id_servico)
        REFERENCES servico_saude(id_servico),
        
    CONSTRAINT fk_unidade_distrito
        FOREIGN KEY (id_distrito)
        REFERENCES distrito_sanitario(id_distrito)
);


CREATE TABLE lideranca_religiosa (
    id_lideranca INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(100) NOT NULL,
    fone VARCHAR(20) UNIQUE,
    email VARCHAR(254) UNIQUE
);

CREATE TABLE terreiro (
    id_terreiro INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(100) NOT NULL,
    id_lideranca INTEGER NOT NULL,
    id_endereco INTEGER NOT NULL,
    religiao VARCHAR(100) NOT NULL,
    nacao VARCHAR(100) NOT NULL,
    regente VARCHAR(100) NOT NULL,
    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP,
    ano_fundacao INTEGER NOT NULL
        CHECK (
            ano_fundacao > 1500
        ),

    CONSTRAINT fk_terreiro_lideranca
        FOREIGN KEY (id_lideranca)
        REFERENCES lideranca_religiosa(id_lideranca),

    CONSTRAINT fk_terreiro_endereco
        FOREIGN KEY (id_endereco)
        REFERENCES endereco(id_endereco)
);

CREATE TABLE membro_terreiro (
    id_membro INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(100) NOT NULL,
    data_nascimento DATE,
    fone VARCHAR(20),
    email VARCHAR(254),
    id_terreiro INTEGER NOT NULL,

    CONSTRAINT fk_membro_terreiro
        FOREIGN KEY (id_terreiro)
        REFERENCES terreiro(id_terreiro)
);

CREATE TABLE membro_unidade_saude (
    id_cadastro INTEGER PRIMARY KEY AUTOINCREMENT,
    id_membro INTEGER NOT NULL,
    id_unidade INTEGER NOT NULL,
    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_cadastro_membro
        FOREIGN KEY (id_membro)
        REFERENCES membro_terreiro(id_membro),

    CONSTRAINT fk_cadastro_unidade
        FOREIGN KEY (id_unidade)
        REFERENCES unidade_saude(id_unidade)
);
