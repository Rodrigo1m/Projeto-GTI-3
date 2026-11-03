"""
Consultas DQL do trabalho.
Cada consulta tem um titulo, a descricao do requisito e o SQL.
"""

CONSULTAS = [

    # ------------------------------------------------------------------
    # a) SELECAO COM CONDICOES (WHERE)
    # ------------------------------------------------------------------
    {
        "titulo": "a) WHERE - Terreiros fundados a partir de 2000",
        "requisito": "Selecao com condicoes (WHERE)",
        "sql": """
SELECT
    nome,
    religiao,
    nacao,
    ano_fundacao
FROM terreiro
WHERE ano_fundacao >= 2000
  AND nacao = 'Angola'
ORDER BY ano_fundacao;
"""
    },

    # ------------------------------------------------------------------
    # b) JUNCOES
    # ------------------------------------------------------------------
    {
        "titulo": "b1) INNER JOIN - Terreiros com lideranca e endereco",
        "requisito": "Selecao com multiplas entidades (INNER JOIN)",
        "sql": """
SELECT
    t.nome              AS terreiro,
    l.nome              AS lideranca,
    e.logradouro        AS endereco,
    b.nome              AS bairro,
    c.nome              AS cidade
FROM terreiro t
INNER JOIN lideranca_religiosa l ON l.id_lideranca = t.id_lideranca
INNER JOIN endereco e            ON e.id_endereco  = t.id_endereco
INNER JOIN bairro b              ON b.id_bairro    = e.id_bairro
INNER JOIN cidade c              ON c.id_cidade    = b.id_cidade;
"""
    },
    {
        "titulo": "b2) LEFT OUTER JOIN - Membros e unidades (inclui sem cadastro)",
        "requisito": "Selecao com multiplas entidades (LEFT OUTER JOIN)",
        "sql": """
-- traz todos os membros, mesmo os que nao tem cadastro em unidade de saude
SELECT
    m.nome                                  AS membro,
    t.nome                                  AS terreiro,
    COALESCE(u.nome, 'SEM CADASTRO')        AS unidade_saude
FROM membro_terreiro m
LEFT OUTER JOIN terreiro t             ON t.id_terreiro = m.id_terreiro
LEFT OUTER JOIN membro_unidade_saude c ON c.id_membro   = m.id_membro
LEFT OUTER JOIN unidade_saude u        ON u.id_unidade  = c.id_unidade
ORDER BY m.nome;
"""
    },
    {
        "titulo": "b3) RIGHT OUTER JOIN - Todas as cidades e seus terreiros",
        "requisito": "Selecao com multiplas entidades (RIGHT OUTER JOIN)",
        "sql": """
-- traz todas as cidades, inclusive as que ainda nao tem terreiro cadastrado
SELECT
    c.nome                                  AS cidade,
    COALESCE(t.nome, 'SEM TERREIRO')        AS terreiro,
    COALESCE(b.nome, '-')                   AS bairro
FROM terreiro t
JOIN      endereco e ON e.id_endereco = t.id_endereco
JOIN      bairro   b ON b.id_bairro   = e.id_bairro
RIGHT OUTER JOIN cidade c ON c.id_cidade = b.id_cidade
ORDER BY c.nome, terreiro;
"""
    },
    {
        "titulo": "b4) FULL OUTER JOIN - Bairros com terreiros e unidades",
        "requisito": "Selecao com multiplas entidades (FULL OUTER JOIN)",
        "sql": """
-- junta os bairros que tem terreiro com os bairros que tem unidade de saude
SELECT
    COALESCE(x.bairro, y.bairro)        AS bairro,
    COALESCE(x.terreiros, 0)            AS qtd_terreiros,
    COALESCE(y.unidades, 0)             AS qtd_unidades
FROM (
        SELECT b.nome AS bairro, COUNT(*) AS terreiros
        FROM terreiro t
        JOIN endereco e ON e.id_endereco = t.id_endereco
        JOIN bairro   b ON b.id_bairro   = e.id_bairro
        GROUP BY b.nome
     ) x
FULL OUTER JOIN (
        SELECT b.nome AS bairro, COUNT(*) AS unidades
        FROM unidade_saude u
        JOIN endereco e ON e.id_endereco = u.id_endereco
        JOIN bairro   b ON b.id_bairro   = e.id_bairro
        GROUP BY b.nome
     ) y ON y.bairro = x.bairro
ORDER BY bairro;
"""
    },

    # ------------------------------------------------------------------
    # c) AGRUPAMENTOS (GROUP BY)
    # ------------------------------------------------------------------
    {
        "titulo": "c) GROUP BY - Quantidade de membros por terreiro",
        "requisito": "Selecao com multiplas entidades e agrupamentos (GROUP BY)",
        "sql": """
SELECT
    t.nome              AS terreiro,
    t.nacao             AS nacao,
    b.nome              AS bairro,
    COUNT(m.id_membro)  AS total_membros
FROM terreiro t
JOIN endereco e        ON e.id_endereco = t.id_endereco
JOIN bairro   b        ON b.id_bairro   = e.id_bairro
LEFT JOIN membro_terreiro m ON m.id_terreiro = t.id_terreiro
GROUP BY t.id_terreiro, t.nome, t.nacao, b.nome
ORDER BY total_membros DESC, t.nome;
"""
    },

    # ------------------------------------------------------------------
    # d) AGRUPAMENTOS ESPECIALIZADOS (HAVING)
    # ------------------------------------------------------------------
    {
        "titulo": "d) HAVING - Unidades que atendem mais de 1 membro",
        "requisito": "Selecao com multiplas entidades e agrupamentos especializados (HAVING)",
        "sql": """
SELECT
    u.nome                  AS unidade_saude,
    s.nome                  AS tipo_servico,
    d.nome                  AS distrito,
    COUNT(c.id_membro)      AS membros_atendidos
FROM unidade_saude u
JOIN servico_saude s          ON s.id_servico  = u.id_servico
JOIN distrito_sanitario d     ON d.id_distrito = u.id_distrito
JOIN membro_unidade_saude c   ON c.id_unidade  = u.id_unidade
GROUP BY u.id_unidade, u.nome, s.nome, d.nome
HAVING COUNT(c.id_membro) > 1
ORDER BY membros_atendidos DESC;
"""
    },

    # ------------------------------------------------------------------
    # e) ORDENACOES (ORDER BY)
    # ------------------------------------------------------------------
    {
        "titulo": "e) ORDER BY - Terreiros do mais antigo ao mais novo",
        "requisito": "Selecao com multiplas entidades e ordenacoes (ORDER BY)",
        "sql": """
SELECT
    t.nome          AS terreiro,
    t.ano_fundacao  AS fundacao,
    t.nacao         AS nacao,
    l.nome          AS lideranca,
    b.nome          AS bairro
FROM terreiro t
JOIN lideranca_religiosa l ON l.id_lideranca = t.id_lideranca
JOIN endereco e            ON e.id_endereco  = t.id_endereco
JOIN bairro   b            ON b.id_bairro    = e.id_bairro
ORDER BY t.ano_fundacao ASC, t.nome DESC;
"""
    },

    # ------------------------------------------------------------------
    # f) FUNCOES NUMERICAS
    # ------------------------------------------------------------------
    {
        "titulo": "f) Funcoes numericas - Estatisticas por nacao",
        "requisito": "Selecao com multiplas entidades e funcoes numericas",
        "sql": """
-- COUNT, MIN, MAX, AVG, ROUND, ABS e SUM
SELECT
    t.nacao                             AS nacao,
    COUNT(*)                            AS qtd_terreiros,
    MIN(t.ano_fundacao)                 AS mais_antigo,
    MAX(t.ano_fundacao)                 AS mais_novo,
    ROUND(AVG(t.ano_fundacao), 1)       AS media_fundacao,
    ROUND(AVG(ABS(e.latitude)), 4)      AS latitude_media,
    SUM(2026 - t.ano_fundacao)          AS soma_anos_atividade
FROM terreiro t
JOIN endereco e ON e.id_endereco = t.id_endereco
GROUP BY t.nacao
ORDER BY qtd_terreiros DESC;
"""
    },

    # ------------------------------------------------------------------
    # g) FUNCOES LITERAIS
    # ------------------------------------------------------------------
    {
        "titulo": "g) Funcoes literais - Tratamento de texto",
        "requisito": "Selecao com multiplas entidades e funcoes literais",
        "sql": """
-- UPPER, LOWER, SUBSTR, LENGTH, REPLACE, TRIM e concatenacao (||)
SELECT
    UPPER(t.nome)                                   AS terreiro_maiusculo,
    SUBSTR(l.nome, 1, INSTR(l.nome, ' ') - 1)       AS primeiro_nome_lideranca,
    LENGTH(t.nome)                                  AS tamanho_nome,
    LOWER(b.nome) || ' / ' || LOWER(c.nome)         AS localizacao,
    REPLACE(TRIM(e.logradouro), 'Rua ', 'R. ')      AS endereco_abreviado
FROM terreiro t
JOIN lideranca_religiosa l ON l.id_lideranca = t.id_lideranca
JOIN endereco e            ON e.id_endereco  = t.id_endereco
JOIN bairro   b            ON b.id_bairro    = e.id_bairro
JOIN cidade   c            ON c.id_cidade    = b.id_cidade
ORDER BY tamanho_nome DESC;
"""
    },

    # ------------------------------------------------------------------
    # h) FUNCOES DE DATA
    # ------------------------------------------------------------------
    {
        "titulo": "h) Funcoes de data - Idade dos membros",
        "requisito": "Selecao com multiplas entidades e funcoes de data",
        "sql": """
-- a data esta gravada como DD/MM/AAAA, entao converto para AAAA-MM-DD com SUBSTR
SELECT
    m.nome                                          AS membro,
    t.nome                                          AS terreiro,
    m.data_nascimento                               AS nascimento,
    STRFTIME('%Y', 'now')
        - STRFTIME('%Y', SUBSTR(m.data_nascimento, 7, 4) || '-' ||
                         SUBSTR(m.data_nascimento, 4, 2) || '-' ||
                         SUBSTR(m.data_nascimento, 1, 2))    AS idade_aprox,
    CAST(JULIANDAY('now')
        - JULIANDAY(SUBSTR(m.data_nascimento, 7, 4) || '-' ||
                    SUBSTR(m.data_nascimento, 4, 2) || '-' ||
                    SUBSTR(m.data_nascimento, 1, 2)) AS INTEGER) AS dias_de_vida,
    DATE(t.data_cadastro)                           AS cadastro_terreiro
FROM membro_terreiro m
JOIN terreiro t ON t.id_terreiro = m.id_terreiro
ORDER BY idade_aprox DESC;
"""
    },

    # ------------------------------------------------------------------
    # i) UNIAO (UNION)
    # ------------------------------------------------------------------
    {
        "titulo": "i) UNION - Mapa geral de terreiros e unidades de saude",
        "requisito": "Selecao com multiplas entidades e uniao (UNION)",
        "sql": """
SELECT
    'TERREIRO'      AS tipo,
    t.nome          AS nome,
    b.nome          AS bairro,
    e.logradouro    AS endereco
FROM terreiro t
JOIN endereco e ON e.id_endereco = t.id_endereco
JOIN bairro   b ON b.id_bairro   = e.id_bairro

UNION

SELECT
    'UNIDADE SAUDE' AS tipo,
    u.nome          AS nome,
    b.nome          AS bairro,
    e.logradouro    AS endereco
FROM unidade_saude u
JOIN endereco e ON e.id_endereco = u.id_endereco
JOIN bairro   b ON b.id_bairro   = e.id_bairro

ORDER BY bairro, tipo;
"""
    },
]
