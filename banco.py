"""
Camada de acesso ao banco de dados SQLite.
Cria o banco, roda os scripts DDL e DML e executa as consultas.
"""

import os
import sqlite3

# caminhos dos arquivos
PASTA = os.path.dirname(os.path.abspath(__file__))
BANCO = os.path.join(PASTA, "terreiros_saude.db")
SCRIPT_CRIACAO = os.path.join(PASTA, "scripts", "criacao_tabelas.sql")
SCRIPT_INSERCAO = os.path.join(PASTA, "scripts", "inserir_dados_tabelas.sql")


def conectar():
    """Abre a conexao com o banco e liga as chaves estrangeiras."""
    con = sqlite3.connect(BANCO)
    con.execute("PRAGMA foreign_keys = ON")
    return con


def banco_existe():
    """Verifica se o banco ja foi criado (se tem a tabela terreiro)."""
    if not os.path.exists(BANCO):
        return False
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='terreiro'")
    existe = cur.fetchone() is not None
    con.close()
    return existe


def ler_script(caminho):
    with open(caminho, "r", encoding="utf-8") as arq:
        return arq.read()


def criar_tabelas():
    """Executa o script DDL de criacao das tabelas."""
    con = conectar()
    con.executescript(ler_script(SCRIPT_CRIACAO))
    con.commit()
    con.close()


def inserir_dados():
    """Executa o script DML de insercao dos dados."""
    con = conectar()
    con.executescript(ler_script(SCRIPT_INSERCAO))
    con.commit()
    con.close()


def apagar_banco():
    """Remove o arquivo do banco para poder recriar do zero."""
    if os.path.exists(BANCO):
        os.remove(BANCO)


def executar_consulta(sql, parametros=()):
    """Roda um SELECT e devolve (colunas, linhas)."""
    con = conectar()
    cur = con.cursor()
    cur.execute(sql, parametros)
    colunas = [d[0] for d in cur.description]
    linhas = cur.fetchall()
    con.close()
    return colunas, linhas


def executar_comando(sql, parametros=()):
    """Roda INSERT/UPDATE/DELETE e devolve quantas linhas foram afetadas."""
    con = conectar()
    cur = con.cursor()
    cur.execute(sql, parametros)
    con.commit()
    total = cur.rowcount
    con.close()
    return total


def contar_registros():
    """Conta quantos registros tem em cada tabela (usado na tela inicial)."""
    tabelas = [
        "cidade", "bairro", "endereco", "distrito_sanitario", "servico_saude",
        "unidade_saude", "lideranca_religiosa", "terreiro",
        "membro_terreiro", "membro_unidade_saude",
    ]
    con = conectar()
    cur = con.cursor()
    resultado = []
    for t in tabelas:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        resultado.append((t, cur.fetchone()[0]))
    con.close()
    return resultado
