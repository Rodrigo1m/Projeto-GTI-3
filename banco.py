"""
Camada de acesso ao banco de dados SQLite.
Cria o banco, roda os scripts DDL e DML e executa as consultas.
"""

import os
import sqlite3
from contextlib import closing

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
    with closing(conectar()) as con:
        cur = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='terreiro'")
        return cur.fetchone() is not None


def ler_script(caminho):
    with open(caminho, "r", encoding="utf-8") as arq:
        return arq.read()


def criar_tabelas():
    """Executa o script DDL de criacao das tabelas."""
    if banco_existe():
        raise RuntimeError(
            "As tabelas ja existem. Para criar de novo, use o botao "
            "'Apagar Banco' antes.")
    with closing(conectar()) as con:
        con.executescript(ler_script(SCRIPT_CRIACAO))
        con.commit()


def inserir_dados():
    """Executa o script DML de insercao dos dados.

    Roda tudo dentro de uma transacao: se qualquer INSERT falhar, nada e
    gravado (evita dados duplicados pela metade).
    """
    with closing(conectar()) as con:
        ja_tem = con.execute("SELECT COUNT(*) FROM cidade").fetchone()[0]
        if ja_tem:
            raise RuntimeError(
                "Os dados ja foram inseridos. Para inserir de novo, use o "
                "botao 'Apagar Banco' e depois crie as tabelas de novo.")
        try:
            con.executescript("BEGIN;\n" + ler_script(SCRIPT_INSERCAO)
                              + "\nCOMMIT;")
        except Exception:
            con.rollback()
            raise


def apagar_banco():
    """Apaga todas as tabelas (e os dados) do banco.

    Usa DROP TABLE em vez de apagar o arquivo, porque no Windows o arquivo
    pode estar travado (OneDrive sincronizando, outro programa aberto etc.).
    """
    if not os.path.exists(BANCO):
        return
    with closing(conectar()) as con:
        con.execute("PRAGMA foreign_keys = OFF")
        tabelas = [linha[0] for linha in con.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        for t in tabelas:
            con.execute(f'DROP TABLE IF EXISTS "{t}"')
        # zera os contadores do AUTOINCREMENT
        if con.execute("SELECT 1 FROM sqlite_master "
                       "WHERE name='sqlite_sequence'").fetchone():
            con.execute("DELETE FROM sqlite_sequence")
        con.commit()


def executar_consulta(sql, parametros=()):
    """Roda um SELECT e devolve (colunas, linhas)."""
    with closing(conectar()) as con:
        cur = con.execute(sql, parametros)
        colunas = [d[0] for d in cur.description]
        linhas = cur.fetchall()
        return colunas, linhas


def executar_comando(sql, parametros=()):
    """Roda INSERT/UPDATE/DELETE e devolve quantas linhas foram afetadas."""
    with closing(conectar()) as con:
        cur = con.execute(sql, parametros)
        con.commit()
        return cur.rowcount


def contar_registros():
    """Conta quantos registros tem em cada tabela (usado na tela inicial)."""
    tabelas = [
        "cidade", "bairro", "endereco", "distrito_sanitario", "servico_saude",
        "unidade_saude", "lideranca_religiosa", "terreiro",
        "membro_terreiro", "membro_unidade_saude",
    ]
    resultado = []
    with closing(conectar()) as con:
        for t in tabelas:
            total = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            resultado.append((t, total))
    return resultado


# ======================================================================
# CADASTRO DE TERREIROS E ATRIBUICAO DE MEMBROS
# ======================================================================
def criar_terreiro(nome, religiao, nacao, regente, ano_fundacao,
                   logradouro, id_bairro, cep, latitude, longitude,
                   id_lideranca=None, nova_lideranca=None):
    """Cria endereco (+ lideranca nova, se informada) e o terreiro.

    Tudo numa transacao so: se algo falhar nada fica gravado pela metade.
    Devolve o id do terreiro criado.
    """
    with closing(conectar()) as con:
        try:
            if nova_lideranca:
                cur = con.execute(
                    "INSERT INTO lideranca_religiosa (nome) VALUES (?)",
                    (nova_lideranca,))
                id_lideranca = cur.lastrowid
            cur = con.execute(
                """INSERT INTO endereco
                       (logradouro, id_bairro, cep, latitude, longitude)
                   VALUES (?, ?, ?, ?, ?)""",
                (logradouro, id_bairro, cep or None, latitude, longitude))
            id_endereco = cur.lastrowid
            cur = con.execute(
                """INSERT INTO terreiro
                       (nome, id_lideranca, id_endereco, religiao, nacao,
                        regente, ano_fundacao)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (nome, id_lideranca, id_endereco, religiao, nacao, regente,
                 ano_fundacao))
            con.commit()
            return cur.lastrowid
        except Exception:
            con.rollback()
            raise


def excluir_terreiro(id_terreiro):
    """Exclui um terreiro que nao tenha membros (e o endereco dele)."""
    with closing(conectar()) as con:
        qtd = con.execute(
            "SELECT COUNT(*) FROM membro_terreiro WHERE id_terreiro = ?",
            (id_terreiro,)).fetchone()[0]
        if qtd:
            raise RuntimeError(
                f"O terreiro ainda tem {qtd} membro(s). Atribua-os a outro "
                "terreiro antes de excluir.")
        linha = con.execute(
            "SELECT id_endereco FROM terreiro WHERE id_terreiro = ?",
            (id_terreiro,)).fetchone()
        con.execute("DELETE FROM terreiro WHERE id_terreiro = ?",
                    (id_terreiro,))
        if linha:
            # so apaga o endereco se mais ninguem usa
            em_uso = con.execute(
                "SELECT (SELECT COUNT(*) FROM terreiro WHERE id_endereco=?)"
                " + (SELECT COUNT(*) FROM unidade_saude WHERE id_endereco=?)",
                (linha[0], linha[0])).fetchone()[0]
            if not em_uso:
                con.execute("DELETE FROM endereco WHERE id_endereco = ?",
                            (linha[0],))
        con.commit()


def atribuir_membros(ids_membros, id_terreiro):
    """Move os membros informados para o terreiro escolhido."""
    with closing(conectar()) as con:
        con.executemany(
            "UPDATE membro_terreiro SET id_terreiro = ? WHERE id_membro = ?",
            [(id_terreiro, m) for m in ids_membros])
        con.commit()


def vincular_membro_unidade(id_membro, id_unidade):
    """Registra o membro numa unidade de saude (se ainda nao estiver)."""
    with closing(conectar()) as con:
        ja = con.execute(
            "SELECT 1 FROM membro_unidade_saude "
            "WHERE id_membro = ? AND id_unidade = ?",
            (id_membro, id_unidade)).fetchone()
        if ja:
            raise RuntimeError("Esse membro já está vinculado a essa "
                               "unidade de saúde.")
        con.execute("INSERT INTO membro_unidade_saude (id_membro, id_unidade)"
                    " VALUES (?, ?)", (id_membro, id_unidade))
        con.commit()


def remover_membro(id_membro):
    """Apaga o membro e os vinculos dele com unidades de saude."""
    with closing(conectar()) as con:
        con.execute("DELETE FROM membro_unidade_saude WHERE id_membro = ?",
                    (id_membro,))
        con.execute("DELETE FROM membro_terreiro WHERE id_membro = ?",
                    (id_membro,))
        con.commit()
