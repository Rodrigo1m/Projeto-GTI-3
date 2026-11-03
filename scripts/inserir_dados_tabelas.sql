INSERT INTO cidade (nome)
VALUES
    ('Recife'),
    ('Olinda'),
    ('Jaboatão dos Guararapes'),
    ('Paulista'),
    ('Camaragibe'),
    ('São Lourenço da Mata'),
    ('Abreu e Lima'),
    ('Igarassu'),
    ('Cabo de Santo Agostinho'),
    ('Ipojuca'),
    ('Moreno'),
    ('Itapissuma'),
    ('Ilha de Itamaracá'),
    ('Araçoiaba'),
    ('Carpina'),
    ('Vitória de Santo Antão'),
    ('Caruaru'),
    ('Garanhuns'),
    ('Petrolina'),
    ('Gravatá');

INSERT INTO bairro (nome, id_cidade)
VALUES
    -- Recife (id_cidade = 1)
    ('Boa Viagem', 1),
    ('Pina', 1),
    ('Brasília Teimosa', 1),
    ('Setúbal', 1),
    ('Imbiribeira', 1),
    ('Ipsep', 1),
    ('Cohab', 1),
    ('Ibura', 1),
    ('Várzea', 1),
    ('Caxangá', 1),
    ('Cidade Universitária', 1),
    ('Madalena', 1),
    ('Torre', 1),
    ('Graças', 1),
    ('Espinheiro', 1),
    ('Aflitos', 1),
    ('Casa Forte', 1),
    ('Parnamirim', 1),
    ('Casa Amarela', 1),
    ('Tamarineira', 1),
    ('Encruzilhada', 1),
    ('Campo Grande', 1),
    ('Arruda', 1),
    ('Água Fria', 1),
    ('Dois Unidos', 1),
    ('Santo Antônio', 1),
    ('São José', 1),
    ('Boa Vista', 1),
    ('Santo Amaro', 1),
    ('Derby', 1),
    ('Ilha do Leite', 1),
    ('Afogados', 1),
    ('Areias', 1),
    ('Jardim São Paulo', 1),
    ('Torreão', 1),
    ('Córrego do Jenipapo', 1),
    ('Lagoa Encantada', 1),
    ('Macaxeira', 1),
    ('Córrego do Arcanjo', 1),

    -- Olinda (id_cidade = 2)
    ('Casa Caiada', 2),
    ('Bairro Novo', 2),
    ('Carmo', 2),
    ('Rio Doce', 2),
    ('Jardim Atlântico', 2),
    ('Peixinhos', 2),
    ('Ouro Preto', 2),
    ('Salgadinho', 2),
    ('Varadouro', 2),

    -- Jaboatão dos Guararapes (id_cidade = 3)
    ('Piedade', 3),
    ('Candeias', 3),
    ('Barra de Jangada', 3),
    ('Prazeres', 3),
    ('Cavaleiro', 3),
    ('Curado', 3),
    ('Jardim Piedade', 3),
    ('Socorro', 3);
    
INSERT INTO endereco (
    logradouro,
    id_bairro,
    cep,
    latitude,
    longitude
)
VALUES
    ('Rua Padre Antonio Prado, 42', 36, '52091-200', -8.0015607, -34.9373825),
    ('Rua Dr. Moacir Sales, 125', 37, '51340-520', -8.122712, -34.9511602),
    ('Rua Manoel Aleixo da Silva, Qd16, Lote 15', 38, '52090-675', -8.0130959, -34.9285959),
    ('Rua Engenho Canavieira, Nº125', 8, '51270-150', -8.1109635, -34.9489656),
    ('Rua Divisópolis, 12', 25, '52150-340', -7.9991486, -34.9131341),
    ('Subida da Carrapeta, 28', 39, '52190-121', -8.0050107, -34.9243511),
    ('2ª Travessia do Bandeira, 701', 27, '50090-190', -8.074341, -34.8918465),
    ('Rua das Moças, 1020', 23, '52120-320', -8.0227594, -34.8874255);

INSERT INTO lideranca_religiosa (nome)
VALUES
    ('Darlingleison Ramos da Silva'),
    ('Jeferson Itanage Pereira de Freitas'),
    ('Silvia Maria da Conceição Alves'),
    ('Maria José Demesio de Souza'),
    ('Moisés Nelson Carneiro da Silva'),
    ('Flávio Cavalcanti da Silva'),
    ('Ana Cristina Nepomuceno de Oliveira'),
    ('Albério Ferreira da Silva');

INSERT INTO servico_saude (nome,sigla)
VALUES
    ('Unidade de Saude da Familia','USF'),
	('Unidade Básica de Saúde','UBS'),    
    ('Laboratorio de Patologia Clinica','SADT');

INSERT INTO terreiro (
	nome,
	id_lideranca,
	id_endereco,
	religiao,
	nacao,
	regente,
	ano_fundacao
)
VALUES
	('Abaça Oyá Togum',1,1,'Candomblé','Umbanda / Linha Branca, Nagô','Iansã, Oxum',1992),
	('Abassá Axé Ogum Bará Oya Lemim',2,2,'Candomblé','Angola','Ogum, Exu',2007),
	('Abassá Axé Oxum Omitaladê',3,3,'Candomblé','Angola','Oxum',2000),
	('Abassá Axé Ya Ogunté Oyá Lecy',4,4,'Candomblé','Angola','Iemanjá Ogunté',1998),
	('Abassá das Águas',5,5,'Candomblé','Jêje Mahin','Orixá',2009),
	('Abassá das Issabas de Oxóssi',6,6,'Candomblé','Angola','Mestre Sibamba, Oxóssi, Mestra Ritinha',2002),
	('Abassá de Angola Omulu Oba Milacy',7,7,'Candomblé','Angola','Omulu',1979),
	('Abassá de Oxum Aladè',8,8,'Candomblé','Jêje Egbá','Oxum, Bessen, Oiá',2006);

INSERT INTO distrito_sanitario  (nome, regiao_rpa)
VALUES
    -- Recife (id_cidade = 1)
    ('1', 1),
    ('2', 1),
    ('3', 3),
    ('4', 4),
    ('5', 5),
    ('6', 6),    
    ('7', 3),
    ('8', 6);

INSERT INTO endereco (
    logradouro,
    id_bairro,
    latitude,
    longitude
)
VALUES
    ('Rua artenis, 9', 29, -8.039675921, -34.87696931),
    ('Rua Álvaves de azevedo, 126', 29, -8.0497116, -34.8888619),
    ('Rua Corrego do Curio, 73 ', 25, -8.000609099, -34.91593382),
    ('ESTRADA DO ARRAIAL, S/N1', 19, -8.027559011, -34.91869407),
    ('rua maria candida, 87', 38, -8.011935328, -34.93183889),
    ('RUA SÃO FRANCISCO DE PAULA, 47', 10, -8.03069298, -34.95576363),
    ('rua jupiraci, 130', 33, -8.10100432, -34.93792792),
    ('rua sargento silvino de macedo, 129', 5, -8.113355928, -34.90688825),
    ('av campo verde, s/n - tres carneiros baixo', 7, -8.12778535, -34.95613879);

INSERT INTO unidade_saude (
    nome,
    id_servico,
    fone,
    id_endereco,
    id_distrito,
    horario_atendimento
)
VALUES
	('us 232 psf ilha santa terezinha',1,'3355-4668',9,1,'segunda a sexta 08:00 - 17:00'),
	('camesp - centro de análises médicas especializadas',3,'3231 7199',10,1,'segunda a sexta 08:00 - 17:00'),
	('us 222 psf corrego do curio',1,'3355-4665',11,2,'segunda a sexta 08:00 - 17:00'),
	('US 109 CS Francisco Pignatari',2,'3355-4400',12,3,'segunda a sexta 08:00 - 17:00'),
	('us 305 psf da macaxeira',1,'3355-6839',13,7,'segunda a sexta 08:00 - 17:00'),
	('US 149 CS Olinto Oliveira',2,'3355-6442/6443',14,4,'segunda a sexta 08:00 - 17:00'),
	('us 186 psf jardim ',1,'3355-6211',15,5,'segunda a sexta 08:00 - 17:00'),
	('us 296 psf coqueiral imbiribeira',1,'3355-6103',16,6,'segunda a sexta 08:00 - 17:00'),
	('us 313 psf três carneiros baixo zumbi do pacheco',1,'3355-4712',17,8,'segunda a sexta 08:00 - 17:00');

INSERT INTO membro_terreiro  (
    nome,
    data_nascimento,
    fone,
    email,
    id_terreiro
)
VALUES
	('Membro terreiro 3 - Usuário 1','26/04/2000','','',3),
	('Membro terreiro 3 - Usuário 2','23/04/1998','','',3),
	('Membro terreiro 1 - Usuário 1','06/05/2005','','',1),
	('Membro terreiro 1 - Usuário 2','18/02/2010','','',1),
	('Membro terreiro 2 - Usuário 1','05/04/1998','','',2),
	('Membro terreiro 2 - Usuário 2','03/09/1996','','',2),
	('Membro terreiro 4 - Usuário 1','26/10/1990','','',4),
	('Membro terreiro 4 - Usuário 2','16/11/1987','','',4),
	('Membro terreiro 5 - Usuário 1','19/02/1995','','',5),
	('Membro terreiro 5 - Usuário 2','18/01/2001','','',5),
	('Membro terreiro 6 - Usuário 1','02/07/2002','','',6),
	('Membro terreiro 6 - Usuário 2','15/06/1994','','',6),
	('Membro terreiro 7 - Usuário 1','14/08/1990','','',7),
	('Membro terreiro 7 - Usuário 2','26/09/1989','','',7),
	('Membro terreiro 8 - Usuário 1','22/01/2011','','',8),
	('Membro terreiro 8 - Usuário 2','13/04/1997','','',8);

INSERT INTO membro_unidade_saude (
	id_membro,
	id_unidade
)
VALUES
	(1,1),
	(1,3),
	(2,2),
	(3,2),
	(4,4),
	(5,5),
	(5,7),
	(6,6),
	(7,8),
	(8,8),
	(10,8),
	(14,9),
	(15,3),
	(15,2);
	
