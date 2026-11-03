# Mapeamento de Terreiros e Unidades de Saude - Recife/PE

Trabalho de Banco de Dados (SR1 + SR2) - aplicacao em Python com interface
grafica (Tkinter) conectada a um banco SQLite.

## Como executar

Precisa apenas do Python 3 instalado (Tkinter e SQLite ja vem junto):

```
python app.py
```

Na primeira vez, abra a aba **1. Banco de Dados** e clique nos botoes na ordem:

1. `1) Criar Tabelas (DDL)` - roda o script `scripts/criacao_tabelas.sql`
2. `2) Inserir Dados (DML)` - roda o script `scripts/inserir_dados_tabelas.sql`

O banco e gravado no arquivo `terreiros_saude.db`, na propria pasta do projeto.
O botao `Recriar Banco do Zero` apaga tudo e refaz os dois passos.

## Arquivos

| Arquivo | O que faz |
|---|---|
| `app.py` | Interface grafica (Tkinter) |
| `banco.py` | Conexao com o SQLite e execucao dos scripts/consultas |
| `consultas.py` | As 12 consultas DQL do trabalho |
| `scripts/criacao_tabelas.sql` | DDL - criacao das tabelas e constraints |
| `scripts/inserir_dados_tabelas.sql` | DML - insercao dos dados |

## Abas do sistema

- **1. Banco de Dados** - executa os scripts DDL/DML e mostra a quantidade de
  registros de cada tabela.
- **2. Consultas (DQL)** - lista as consultas do trabalho. Ao selecionar, o SQL
  aparece na caixa de texto (da pra editar antes de executar) e o resultado
  vem na tabela abaixo.
- **3. Cadastrar Membro** - formulario que grava um novo membro no banco
  (parte de persistencia de dados).
- **4. SQL Livre** - digita qualquer comando SQL e executa.

## Consultas implementadas (requisito DQL)

| Letra | Requisito | Consulta |
|---|---|---|
| a | WHERE | Terreiros fundados a partir de 2000 |
| b1 | INNER JOIN | Terreiros com lideranca e endereco |
| b2 | LEFT OUTER JOIN | Membros e unidades (inclui quem nao tem cadastro) |
| b3 | RIGHT OUTER JOIN | Todas as cidades e seus terreiros |
| b4 | FULL OUTER JOIN | Bairros com terreiros e unidades |
| c | GROUP BY | Quantidade de membros por terreiro |
| d | HAVING | Unidades que atendem mais de 1 membro |
| e | ORDER BY | Terreiros do mais antigo ao mais novo |
| f | Funcoes numericas | COUNT, MIN, MAX, AVG, ROUND, ABS, SUM por nacao |
| g | Funcoes literais | UPPER, LOWER, SUBSTR, LENGTH, REPLACE, TRIM, INSTR |
| h | Funcoes de data | STRFTIME, JULIANDAY, DATE - idade dos membros |
| i | UNION | Mapa geral de terreiros + unidades de saude |

## Observacao

As consultas `b3` e `b4` usam `RIGHT OUTER JOIN` e `FULL OUTER JOIN`, que o
SQLite so suporta a partir da versao 3.39. Para conferir a versao instalada:

```
python -c "import sqlite3; print(sqlite3.sqlite_version)"
```

Python 3.12 ou mais novo ja vem com uma versao compativel.
