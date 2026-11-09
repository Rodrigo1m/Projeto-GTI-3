"""
Mapeamento de Terreiros e Unidades de Saude do Recife
Interface grafica em Tkinter conectada ao banco SQLite.

Para rodar:  python app.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

import banco
from consultas import CONSULTAS

# cores usadas na tela
COR_FUNDO = "#f0f0f0"
COR_TITULO = "#1a4971"


class Aplicacao(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Terreiros e Unidades de Saude - Recife/PE")
        self.geometry("1100x650")
        self.configure(bg=COR_FUNDO)

        self.montar_cabecalho()

        # barra de status no rodape
        self.status = tk.Label(self, text="Pronto", anchor="w",
                               bg="#dddddd", relief="sunken")
        self.status.pack(fill="x", side="bottom")

        # abas do sistema
        self.abas = ttk.Notebook(self)
        self.abas.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        self.aba_banco()
        self.aba_consultas()
        self.aba_cadastro()
        self.aba_sql_livre()

        self.atualizar_status_banco()

    def montar_cabecalho(self):
        topo = tk.Frame(self, bg=COR_TITULO)
        topo.pack(fill="x")
        tk.Label(topo, text="Mapeamento de Terreiros e Unidades de Saude",
                 font=("Arial", 15, "bold"), bg=COR_TITULO, fg="white",
                 pady=8).pack()
        tk.Label(topo, text="Banco de Dados - SQLite", font=("Arial", 9),
                 bg=COR_TITULO, fg="#cfe3f5", pady=(0)).pack(pady=(0, 8))

    def avisar(self, texto):
        self.status.config(text=texto)

    # ==================================================================
    # ABA 1 - BANCO DE DADOS (executa os scripts DDL e DML)
    # ==================================================================
    def aba_banco(self):
        aba = tk.Frame(self.abas, bg=COR_FUNDO)
        self.abas.add(aba, text="  1. Banco de Dados  ")

        tk.Label(aba, text="Execute os scripts na ordem: primeiro criar as "
                           "tabelas, depois inserir os dados. Para comecar "
                           "de novo, apague o banco antes.",
                 bg=COR_FUNDO, font=("Arial", 10)).pack(anchor="w",
                                                        padx=15, pady=(15, 10))

        botoes = tk.Frame(aba, bg=COR_FUNDO)
        botoes.pack(anchor="w", padx=15)

        tk.Button(botoes, text="1) Criar Tabelas (DDL)", width=24,
                  command=self.acao_criar).pack(side="left", padx=(0, 8))
        tk.Button(botoes, text="2) Inserir Dados (DML)", width=24,
                  command=self.acao_inserir).pack(side="left", padx=8)
        tk.Button(botoes, text="Apagar Banco", width=24,
                  command=self.acao_apagar).pack(side="left", padx=8)

        tk.Label(aba, text="Registros por tabela:", bg=COR_FUNDO,
                 font=("Arial", 10, "bold")).pack(anchor="w", padx=15,
                                                  pady=(20, 5))

        self.tabela_status = ttk.Treeview(aba, columns=("tabela", "qtd"),
                                          show="headings", height=12)
        self.tabela_status.heading("tabela", text="Tabela")
        self.tabela_status.heading("qtd", text="Qtd. de Registros")
        self.tabela_status.column("tabela", width=250)
        self.tabela_status.column("qtd", width=150, anchor="center")
        self.tabela_status.pack(anchor="w", padx=15, pady=5)

    def acao_criar(self):
        try:
            banco.criar_tabelas()
            messagebox.showinfo("OK", "Tabelas criadas com sucesso.")
            self.avisar("Script de criacao executado.")
            self.atualizar_status_banco()
            self.carregar_terreiros_combo()
        except Exception as erro:
            messagebox.showerror("Erro ao criar tabelas", str(erro))

    def acao_inserir(self):
        try:
            banco.inserir_dados()
            messagebox.showinfo("OK", "Dados inseridos com sucesso.")
            self.avisar("Script de insercao executado.")
            self.atualizar_status_banco()
            self.carregar_terreiros_combo()
        except Exception as erro:
            messagebox.showerror("Erro ao inserir dados", str(erro))

    def acao_apagar(self):
        if not messagebox.askyesno("Confirmar",
                                   "Isso apaga todas as tabelas e dados do "
                                   "banco. Continuar?"):
            return
        try:
            banco.apagar_banco()
            messagebox.showinfo("OK", "Banco apagado. Agora use o botao "
                                      "'1) Criar Tabelas (DDL)'.")
            self.avisar("Banco apagado.")
            self.atualizar_status_banco()
            # limpa a aba de cadastro, que ainda mostrava os dados antigos
            self.terreiros = []
            self.combo_terreiro["values"] = []
            self.combo_terreiro.set("")
            self.preencher_tabela(self.tabela_membros, [], [])
        except Exception as erro:
            messagebox.showerror("Erro ao apagar banco", str(erro))

    def atualizar_status_banco(self):
        for item in self.tabela_status.get_children():
            self.tabela_status.delete(item)
        if not banco.banco_existe():
            self.avisar("Banco ainda nao foi criado. Use a aba 1.")
            return
        for tabela, qtd in banco.contar_registros():
            self.tabela_status.insert("", "end", values=(tabela, qtd))

    # ==================================================================
    # ABA 2 - CONSULTAS DQL
    # ==================================================================
    def aba_consultas(self):
        aba = tk.Frame(self.abas, bg=COR_FUNDO)
        self.abas.add(aba, text="  2. Consultas (DQL)  ")

        # lado esquerdo: lista das consultas
        esquerda = tk.Frame(aba, bg=COR_FUNDO)
        esquerda.pack(side="left", fill="y", padx=10, pady=10)

        tk.Label(esquerda, text="Consultas disponiveis:", bg=COR_FUNDO,
                 font=("Arial", 10, "bold")).pack(anchor="w")

        self.lista = tk.Listbox(esquerda, width=52, height=23,
                                font=("Arial", 9))
        self.lista.pack(pady=5, fill="y", expand=True)
        for c in CONSULTAS:
            self.lista.insert("end", c["titulo"])
        self.lista.bind("<<ListboxSelect>>", self.mostrar_sql)

        tk.Button(esquerda, text="Executar Consulta",
                  command=self.executar_consulta_selecionada).pack(fill="x")

        # lado direito: SQL em cima, resultado embaixo
        direita = tk.Frame(aba, bg=COR_FUNDO)
        direita.pack(side="left", fill="both", expand=True, padx=(0, 10),
                     pady=10)

        tk.Label(direita, text="SQL da consulta:", bg=COR_FUNDO,
                 font=("Arial", 10, "bold")).pack(anchor="w")
        self.caixa_sql = scrolledtext.ScrolledText(direita, height=11,
                                                   font=("Consolas", 9),
                                                   bg="#fbfbfb")
        self.caixa_sql.pack(fill="x", pady=(2, 8))

        tk.Label(direita, text="Resultado:", bg=COR_FUNDO,
                 font=("Arial", 10, "bold")).pack(anchor="w")

        quadro = tk.Frame(direita)
        quadro.pack(fill="both", expand=True)
        self.resultado = ttk.Treeview(quadro, show="headings")
        barra_v = ttk.Scrollbar(quadro, orient="vertical",
                                command=self.resultado.yview)
        barra_h = ttk.Scrollbar(quadro, orient="horizontal",
                                command=self.resultado.xview)
        self.resultado.configure(yscrollcommand=barra_v.set,
                                 xscrollcommand=barra_h.set)
        barra_v.pack(side="right", fill="y")
        barra_h.pack(side="bottom", fill="x")
        self.resultado.pack(fill="both", expand=True)

        self.lista.selection_set(0)
        self.mostrar_sql()

    def mostrar_sql(self, evento=None):
        selecao = self.lista.curselection()
        if not selecao:
            return
        consulta = CONSULTAS[selecao[0]]
        self.caixa_sql.delete("1.0", "end")
        self.caixa_sql.insert("1.0", consulta["sql"].strip())
        self.avisar("Requisito: " + consulta["requisito"])

    def executar_consulta_selecionada(self):
        if not banco.banco_existe():
            messagebox.showwarning("Atencao",
                                   "Crie o banco na aba 1 antes de consultar.")
            return
        sql = self.caixa_sql.get("1.0", "end").strip()
        try:
            colunas, linhas = banco.executar_consulta(sql)
        except Exception as erro:
            messagebox.showerror("Erro na consulta", str(erro))
            return
        self.preencher_tabela(self.resultado, colunas, linhas)
        self.avisar(f"{len(linhas)} registro(s) encontrado(s).")

    def preencher_tabela(self, tabela, colunas, linhas):
        """Joga o resultado da consulta dentro de um Treeview."""
        tabela.delete(*tabela.get_children())
        tabela["columns"] = colunas

        for i, col in enumerate(colunas):
            # a largura acompanha o maior texto daquela coluna
            maior = len(str(col))
            for linha in linhas:
                maior = max(maior, len(str(linha[i])))
            largura = min(300, max(70, maior * 8 + 20))
            tabela.heading(col, text=col)
            tabela.column(col, width=largura, minwidth=60, anchor="w",
                          stretch=False)

        for linha in linhas:
            tabela.insert("", "end",
                          values=["" if v is None else v for v in linha])

    # ==================================================================
    # ABA 3 - CADASTRO (persistencia de dados)
    # ==================================================================
    def aba_cadastro(self):
        aba = tk.Frame(self.abas, bg=COR_FUNDO)
        self.abas.add(aba, text="  3. Cadastrar Membro  ")

        tk.Label(aba, text="Cadastro de membro de terreiro", bg=COR_FUNDO,
                 font=("Arial", 11, "bold")).grid(row=0, column=0,
                                                  columnspan=2, sticky="w",
                                                  padx=15, pady=(15, 12))

        self.campos = {}
        rotulos = [
            ("nome", "Nome completo *"),
            ("data_nascimento", "Data de nascimento (DD/MM/AAAA)"),
            ("fone", "Telefone"),
            ("email", "E-mail"),
        ]
        linha = 1
        for chave, texto in rotulos:
            tk.Label(aba, text=texto, bg=COR_FUNDO).grid(row=linha, column=0,
                                                         sticky="e", padx=10,
                                                         pady=5)
            entrada = tk.Entry(aba, width=42)
            entrada.grid(row=linha, column=1, sticky="w", pady=5)
            self.campos[chave] = entrada
            linha += 1

        tk.Label(aba, text="Terreiro *", bg=COR_FUNDO).grid(row=linha,
                                                            column=0,
                                                            sticky="e",
                                                            padx=10, pady=5)
        self.combo_terreiro = ttk.Combobox(aba, width=39, state="readonly")
        self.combo_terreiro.grid(row=linha, column=1, sticky="w", pady=5)
        linha += 1

        tk.Button(aba, text="Salvar Membro", width=20,
                  command=self.salvar_membro).grid(row=linha, column=1,
                                                   sticky="w", pady=15)
        linha += 1

        tk.Label(aba, text="Membros cadastrados:", bg=COR_FUNDO,
                 font=("Arial", 10, "bold")).grid(row=linha, column=0,
                                                  columnspan=2, sticky="w",
                                                  padx=15, pady=(10, 5))
        linha += 1

        quadro = tk.Frame(aba)
        quadro.grid(row=linha, column=0, columnspan=2, sticky="nsew",
                    padx=15, pady=(0, 15))
        self.tabela_membros = ttk.Treeview(quadro, show="headings", height=11)
        barra = ttk.Scrollbar(quadro, orient="vertical",
                              command=self.tabela_membros.yview)
        self.tabela_membros.configure(yscrollcommand=barra.set)
        barra.pack(side="right", fill="y")
        self.tabela_membros.pack(fill="both", expand=True)
        aba.grid_rowconfigure(linha, weight=1)
        aba.grid_columnconfigure(1, weight=1)

        self.terreiros = []
        self.carregar_terreiros_combo()

    def carregar_terreiros_combo(self):
        """Busca os terreiros no banco para preencher a lista suspensa."""
        if not banco.banco_existe():
            return
        _, linhas = banco.executar_consulta(
            "SELECT id_terreiro, nome FROM terreiro ORDER BY nome")
        self.terreiros = linhas
        self.combo_terreiro["values"] = [nome for _, nome in linhas]
        self.listar_membros()

    def salvar_membro(self):
        nome = self.campos["nome"].get().strip()
        indice = self.combo_terreiro.current()

        # validacao basica antes de mandar pro banco
        if not nome:
            messagebox.showwarning("Atencao", "Informe o nome do membro.")
            return
        if indice < 0:
            messagebox.showwarning("Atencao", "Selecione o terreiro.")
            return

        id_terreiro = self.terreiros[indice][0]
        try:
            banco.executar_comando(
                """INSERT INTO membro_terreiro
                       (nome, data_nascimento, fone, email, id_terreiro)
                   VALUES (?, ?, ?, ?, ?)""",
                (nome,
                 self.campos["data_nascimento"].get().strip(),
                 self.campos["fone"].get().strip(),
                 self.campos["email"].get().strip(),
                 id_terreiro)
            )
        except Exception as erro:
            messagebox.showerror("Erro ao salvar", str(erro))
            return

        messagebox.showinfo("OK", "Membro cadastrado com sucesso.")
        for entrada in self.campos.values():
            entrada.delete(0, "end")
        self.listar_membros()
        self.atualizar_status_banco()
        self.avisar("Membro salvo no banco.")

    def listar_membros(self):
        if not banco.banco_existe():
            return
        colunas, linhas = banco.executar_consulta("""
            SELECT m.id_membro   AS id,
                   m.nome        AS membro,
                   m.data_nascimento AS nascimento,
                   t.nome        AS terreiro
            FROM membro_terreiro m
            JOIN terreiro t ON t.id_terreiro = m.id_terreiro
            ORDER BY m.id_membro DESC
        """)
        self.preencher_tabela(self.tabela_membros, colunas, linhas)

    # ==================================================================
    # ABA 4 - SQL LIVRE
    # ==================================================================
    def aba_sql_livre(self):
        aba = tk.Frame(self.abas, bg=COR_FUNDO)
        self.abas.add(aba, text="  4. SQL Livre  ")

        tk.Label(aba, text="Digite um comando SQL e execute:", bg=COR_FUNDO,
                 font=("Arial", 10, "bold")).pack(anchor="w", padx=12,
                                                  pady=(12, 4))

        self.sql_livre = scrolledtext.ScrolledText(aba, height=9,
                                                   font=("Consolas", 10))
        self.sql_livre.pack(fill="x", padx=12)
        self.sql_livre.insert("1.0", "SELECT * FROM terreiro;")

        tk.Button(aba, text="Executar", width=18,
                  command=self.executar_sql_livre).pack(anchor="w", padx=12,
                                                        pady=8)

        quadro = tk.Frame(aba)
        quadro.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.resultado_livre = ttk.Treeview(quadro, show="headings")
        barra = ttk.Scrollbar(quadro, orient="vertical",
                              command=self.resultado_livre.yview)
        self.resultado_livre.configure(yscrollcommand=barra.set)
        barra.pack(side="right", fill="y")
        self.resultado_livre.pack(fill="both", expand=True)

    def executar_sql_livre(self):
        if not banco.banco_existe():
            messagebox.showwarning("Atencao", "Crie o banco na aba 1 primeiro.")
            return
        sql = self.sql_livre.get("1.0", "end").strip()
        if not sql:
            return
        try:
            # se for SELECT mostra na tabela, senao so executa e avisa
            if sql.lower().lstrip().startswith("select"):
                colunas, linhas = banco.executar_consulta(sql)
                self.preencher_tabela(self.resultado_livre, colunas, linhas)
                self.avisar(f"{len(linhas)} registro(s) retornado(s).")
            else:
                afetadas = banco.executar_comando(sql)
                messagebox.showinfo("OK", f"Comando executado. "
                                          f"{afetadas} linha(s) afetada(s).")
                self.atualizar_status_banco()
                self.avisar("Comando executado.")
        except Exception as erro:
            messagebox.showerror("Erro no SQL", str(erro))


if __name__ == "__main__":
    Aplicacao().mainloop()
