"""
Mapeamento de Terreiros e Unidades de Saude do Recife
Interface grafica em Tkinter conectada ao banco SQLite.

Ao abrir, a tela de login (sem senha) oferece dois perfis:
  - Terreiro: ficha do proprio terreiro, cadastro de membros, vinculo com
              unidades de saude e mapa das unidades mais proximas
  - Gestor:   Painel (indicadores, graficos, mapa, proximidade) e
              Administracao (banco, terreiros, membros, consultas, SQL livre)

Para rodar:  python app.py
"""

import tkinter as tk
from datetime import date
from tkinter import ttk, messagebox, scrolledtext

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

try:
    import tkintermapview
except ImportError:          # mapa interativo e opcional
    tkintermapview = None

import banco
import painel
import tema
from consultas import CONSULTAS
from tema import (FUNDO, CARTAO, BORDA, PRIMARIA, DESTAQUE, TEXTO, TEXTO_2,
                  TEXTO_CLARO, ZEBRA, FONTE, COR_UNIDADE, COR_TERREIRO,
                  COR_NEUTRA)

CENTRO_RECIFE = (-8.05, -34.92)
RELIGIOES = ["Candomblé", "Umbanda", "Jurema", "Xambá", "Quimbanda"]

matplotlib.rcParams.update({
    "font.family": [FONTE, "DejaVu Sans"],
    "font.size": 9,
    "axes.edgecolor": BORDA,
    "axes.labelcolor": TEXTO_2,
    "xtick.color": TEXTO_2,
    "ytick.color": TEXTO,
    "axes.titlecolor": TEXTO,
})


def encurtar(texto, n=28):
    texto = str(texto)
    return texto if len(texto) <= n else texto[:n - 1] + "…"


class Aplicacao(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Terreiros e Unidades de Saude - Recife/PE")
        self.geometry("1320x840")
        self.minsize(1150, 720)
        try:
            self.state("zoomed")
        except tk.TclError:
            pass
        tema.aplicar(self)

        self.perfil = None          # "gestor" ou "terreiro"
        self.modo = None
        self.corpo = None
        self.painel_desatualizado = True
        self.terreiros = []
        self.terreiro_sel = None

        # barra de status no rodape
        self.status = tk.Label(self, text="Pronto", anchor="w", bg="#e6e1d6",
                               fg=TEXTO_2, font=(FONTE, 9), padx=12, pady=4)
        self.status.pack(fill="x", side="bottom")

        self.tela_login()

    # ==================================================================
    # LOGIN (sem senha): escolhe o perfil Terreiro ou Gestor
    # ==================================================================
    def limpar_corpo(self):
        if self.corpo is not None:
            self.corpo.destroy()
        self.corpo = tk.Frame(self, bg=FUNDO)
        self.corpo.pack(fill="both", expand=True)

    def tela_login(self):
        self.perfil = None
        self.modo = None
        self.limpar_corpo()
        self.avisar("Escolha como deseja entrar.")

        fundo = tk.Frame(self.corpo, bg=PRIMARIA)
        fundo.pack(fill="both", expand=True)
        centro = tk.Frame(fundo, bg=PRIMARIA)
        centro.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(centro, text="◆", font=(FONTE, 34), bg=PRIMARIA,
                 fg="#e9c46a").pack()
        tk.Label(centro, text="Terreiros & Saúde", font=(FONTE, 26, "bold"),
                 bg=PRIMARIA, fg="white").pack()
        tk.Label(centro, text="Mapeamento de terreiros e unidades de saúde "
                              "· Recife/PE", font=(FONTE, 11),
                 bg=PRIMARIA, fg=TEXTO_CLARO).pack(pady=(2, 28))

        opcoes = tk.Frame(centro, bg=PRIMARIA)
        opcoes.pack()

        def cartao_login(coluna, cor, titulo, texto):
            externo = tk.Frame(opcoes, bg=CARTAO)
            externo.grid(row=0, column=coluna, padx=14, sticky="nsew")
            tk.Frame(externo, bg=cor, height=6).pack(fill="x")
            corpo = ttk.Frame(externo, style="Cartao.TFrame",
                              padding=(28, 22))
            corpo.pack(fill="both", expand=True)
            ttk.Label(corpo, text=titulo, style="Titulo.TLabel").pack(
                anchor="w")
            ttk.Label(corpo, text=texto, style="Sub.TLabel",
                      wraplength=300, justify="left").pack(anchor="w",
                                                           pady=(4, 16))
            return corpo

        # ---- perfil terreiro
        c = cartao_login(0, COR_TERREIRO, "Sou um terreiro",
                         "Veja seus membros, cadastre pessoas, vincule-as a "
                         "unidades de saúde e encontre os postos mais "
                         "perto de você.")
        ttk.Label(c, text="Qual é o seu terreiro?",
                  style="Rotulo.TLabel").pack(anchor="w")
        self.combo_login = ttk.Combobox(c, state="readonly", width=40)
        self.combo_login.pack(fill="x", pady=(4, 16))
        self.login_terreiros = []
        if banco.banco_existe():
            _, self.login_terreiros = banco.executar_consulta(
                "SELECT id_terreiro, nome FROM terreiro ORDER BY nome")
        self.combo_login["values"] = [n for _, n in self.login_terreiros]
        if not self.login_terreiros:
            self.combo_login.set("Nenhum terreiro cadastrado ainda")
        ttk.Button(c, text="Entrar como terreiro", style="Destaque.TButton",
                   command=self.entrar_terreiro).pack(fill="x")

        # ---- perfil gestor
        c = cartao_login(1, COR_UNIDADE, "Sou gestor(a)",
                         "Painel com indicadores e gráficos, mapa de "
                         "terreiros e unidades de saúde, cadastro de "
                         "terreiros e administração do banco.")
        ttk.Button(c, text="Entrar como gestor", style="Primario.TButton",
                   command=self.entrar_gestor).pack(fill="x", side="bottom")

        tk.Label(centro, text="Acesso sem senha — escolha o perfil para "
                              "continuar.", font=(FONTE, 9), bg=PRIMARIA,
                 fg=TEXTO_CLARO).pack(pady=(24, 0))

    def entrar_gestor(self):
        self.perfil = "gestor"
        self.terreiro_sel = None
        self.painel_desatualizado = True
        self.limpar_corpo()
        self.montar_cabecalho("Gestor(a)", com_modos=True)

        # dois conjuntos de abas: painel (gestao) e administracao (operacao)
        self.nb_operacao = ttk.Notebook(self.corpo)
        self.nb_gestao = ttk.Notebook(self.corpo)

        self.aba_painel()
        self.aba_mapa()
        self.aba_proximidade()

        self.aba_banco()
        self.aba_terreiros()
        self.aba_cadastro()
        self.aba_consultas()
        self.aba_sql_livre()

        self.nb_gestao.bind("<<NotebookTabChanged>>",
                            lambda e: self.atualizar_gestao())

        self.modo = "operacao"
        self.atualizar_tudo()
        self.mostrar_modo("gestao" if banco.banco_existe() else "operacao")
        self.avisar("Conectado como gestor(a).")

    def entrar_terreiro(self):
        indice = self.combo_login.current()
        if indice < 0:
            messagebox.showwarning(
                "Atenção", "Selecione o seu terreiro. Se a lista estiver "
                           "vazia, peça ao gestor para cadastrá-lo.")
            return
        self.perfil = "terreiro"
        self.meu_id, nome = self.login_terreiros[indice]
        self.limpar_corpo()
        self.montar_cabecalho(nome, com_modos=False)

        self.nb_terreiro = ttk.Notebook(self.corpo)
        self.nb_terreiro.pack(fill="both", expand=True, padx=14, pady=(6, 8))
        self.aba_meu_terreiro()
        self.aba_saude_perto()
        # o mapa so tem tamanho quando a aba aparece: redesenha nessa hora
        self.nb_terreiro.bind(
            "<<NotebookTabChanged>>",
            lambda _e: self.after(150, self.desenhar_saude_perto))
        self.atualizar_tudo()
        self.avisar(f"Conectado como terreiro: {nome}")

    # ==================================================================
    # ESTRUTURA GERAL
    # ==================================================================
    def montar_cabecalho(self, usuario, com_modos):
        topo = tk.Frame(self.corpo, bg=PRIMARIA)
        topo.pack(fill="x")

        marca = tk.Frame(topo, bg=PRIMARIA)
        marca.pack(side="left", padx=22, pady=12)
        tk.Label(marca, text="◆", font=(FONTE, 22), bg=PRIMARIA,
                 fg="#e9c46a").pack(side="left", padx=(0, 10))
        textos = tk.Frame(marca, bg=PRIMARIA)
        textos.pack(side="left")
        tk.Label(textos, text="Terreiros & Saúde",
                 font=(FONTE, 16, "bold"), bg=PRIMARIA,
                 fg="white").pack(anchor="w")
        tk.Label(textos, text="Mapeamento de terreiros e unidades de saúde "
                              "· Recife/PE",
                 font=(FONTE, 9), bg=PRIMARIA, fg=TEXTO_CLARO).pack(anchor="w")

        # usuario logado + sair
        sair = tk.Label(topo, text="Sair", font=(FONTE, 10, "bold"),
                        bg=PRIMARIA, fg="white", padx=14, pady=6,
                        cursor="hand2", highlightthickness=1,
                        highlightbackground=TEXTO_CLARO)
        sair.pack(side="right", padx=(8, 22))
        sair.bind("<Button-1>", lambda e: self.tela_login())
        perfil = "Gestor" if self.perfil == "gestor" else "Terreiro"
        quem = tk.Frame(topo, bg=PRIMARIA)
        quem.pack(side="right", padx=12)
        tk.Label(quem, text=perfil.upper(), font=(FONTE, 8, "bold"),
                 bg=PRIMARIA, fg="#e9c46a").pack(anchor="e")
        tk.Label(quem, text=encurtar(usuario, 40), font=(FONTE, 10),
                 bg=PRIMARIA, fg="white").pack(anchor="e")

        if not com_modos:
            return
        # seletor de modo (estilo "segmented control")
        seletor = tk.Frame(topo, bg="#163a2b", padx=4, pady=4)
        seletor.pack(side="right", padx=12)
        self.botoes_modo = {}
        for chave, texto in (("gestao", "Painel"),
                             ("operacao", "Administração")):
            b = tk.Label(seletor, text=texto, font=(FONTE, 10, "bold"),
                         padx=18, pady=7, cursor="hand2")
            b.pack(side="left", padx=2)
            b.bind("<Button-1>", lambda e, c=chave: self.mostrar_modo(c))
            self.botoes_modo[chave] = b

    def mostrar_modo(self, modo):
        self.modo = modo
        for chave, b in self.botoes_modo.items():
            ativo = chave == modo
            b.configure(bg="white" if ativo else "#163a2b",
                        fg=PRIMARIA if ativo else TEXTO_CLARO)
        if modo == "operacao":
            self.nb_gestao.pack_forget()
            self.nb_operacao.pack(fill="both", expand=True, padx=14,
                                  pady=(6, 8))
        else:
            self.nb_operacao.pack_forget()
            self.nb_gestao.pack(fill="both", expand=True, padx=14,
                                pady=(6, 8))
            self.atualizar_gestao()

    def avisar(self, texto):
        self.status.config(text=texto)

    def nova_aba(self, notebook, titulo):
        aba = ttk.Frame(notebook, style="TFrame", padding=12)
        notebook.add(aba, text=titulo)
        return aba

    def cartao(self, pai, titulo=None, subtitulo=None, padding=16):
        """Caixa branca com borda fina e titulo opcional."""
        externo = tk.Frame(pai, bg=CARTAO, highlightbackground=BORDA,
                           highlightcolor=BORDA, highlightthickness=1)
        interno = ttk.Frame(externo, style="Cartao.TFrame", padding=padding)
        interno.pack(fill="both", expand=True)
        if titulo:
            ttk.Label(interno, text=titulo, style="Titulo.TLabel").pack(
                anchor="w")
        if subtitulo:
            ttk.Label(interno, text=subtitulo, style="Sub.TLabel",
                      wraplength=900, justify="left").pack(anchor="w",
                                                           pady=(0, 8))
        return externo, interno

    def criar_tabela(self, pai, height=10, selectmode="browse",
                     horizontal=False):
        quadro = ttk.Frame(pai, style="Cartao.TFrame")
        tabela = ttk.Treeview(quadro, show="headings", height=height,
                              selectmode=selectmode)
        barra_v = ttk.Scrollbar(quadro, orient="vertical",
                                command=tabela.yview)
        tabela.configure(yscrollcommand=barra_v.set)
        barra_v.pack(side="right", fill="y")
        if horizontal:
            barra_h = ttk.Scrollbar(quadro, orient="horizontal",
                                    command=tabela.xview)
            tabela.configure(xscrollcommand=barra_h.set)
            barra_h.pack(side="bottom", fill="x")
        tabela.pack(fill="both", expand=True)
        tabela.tag_configure("zebra", background=ZEBRA)
        return quadro, tabela

    def preencher_tabela(self, tabela, colunas, linhas, larguras=None):
        """Joga o resultado da consulta dentro de um Treeview."""
        tabela.delete(*tabela.get_children())
        tabela["columns"] = colunas

        for i, col in enumerate(colunas):
            if larguras and col in larguras:
                largura = larguras[col]
            else:
                # a largura acompanha o maior texto daquela coluna
                maior = len(str(col))
                for linha in linhas:
                    maior = max(maior, len(str(linha[i])))
                largura = min(320, max(70, maior * 8 + 24))
            tabela.heading(col, text=col, anchor="w")
            tabela.column(col, width=largura, minwidth=50, anchor="w",
                          stretch=bool(larguras))

        for n, linha in enumerate(linhas):
            tabela.insert("", "end",
                          values=["" if v is None else v for v in linha],
                          tags=("zebra",) if n % 2 else ())

    def campo(self, pai, rotulo, linha, coluna, largura=1, widget=None):
        """Rotulo em cima + entrada embaixo, dentro de um grid."""
        ttk.Label(pai, text=rotulo, style="Rotulo.TLabel").grid(
            row=linha * 2, column=coluna, columnspan=largura, sticky="w",
            padx=(0, 10), pady=(8, 2))
        w = widget or ttk.Entry(pai)
        w.grid(row=linha * 2 + 1, column=coluna, columnspan=largura,
               sticky="ew", padx=(0, 10))
        return w

    def atualizar_tudo(self):
        """Recarrega tudo que depende do banco depois de qualquer mudanca."""
        if self.perfil == "terreiro":
            self.carregar_meu_terreiro()
            return
        self.atualizar_status_banco()
        self.carregar_terreiros_combo()
        self.carregar_aba_terreiros()
        self.painel_desatualizado = True
        if self.modo == "gestao":
            self.atualizar_gestao()

    # ==================================================================
    # OPERACAO 1 - BANCO DE DADOS (executa os scripts DDL e DML)
    # ==================================================================
    def aba_banco(self):
        aba = self.nova_aba(self.nb_operacao, "Banco de Dados")

        externo, card = self.cartao(
            aba, "Scripts do banco",
            "Execute os scripts na ordem: primeiro criar as tabelas, depois "
            "inserir os dados. Para começar de novo, apague o banco antes.")
        externo.pack(fill="x")

        botoes = ttk.Frame(card, style="Cartao.TFrame")
        botoes.pack(anchor="w", pady=(4, 0))
        ttk.Button(botoes, text="1 · Criar Tabelas (DDL)",
                   style="Primario.TButton",
                   command=self.acao_criar).pack(side="left", padx=(0, 8))
        ttk.Button(botoes, text="2 · Inserir Dados (DML)",
                   style="Primario.TButton",
                   command=self.acao_inserir).pack(side="left", padx=8)
        ttk.Button(botoes, text="Apagar Banco", style="Destaque.TButton",
                   command=self.acao_apagar).pack(side="left", padx=8)

        externo, card = self.cartao(aba, "Registros por tabela")
        externo.pack(fill="both", expand=True, pady=(12, 0))
        quadro, self.tabela_status = self.criar_tabela(card, height=10)
        quadro.pack(fill="both", expand=True, pady=(8, 0))
        self.tabela_status["columns"] = ("tabela", "qtd")
        self.tabela_status.heading("tabela", text="Tabela", anchor="w")
        self.tabela_status.heading("qtd", text="Qtd. de Registros")
        self.tabela_status.column("tabela", width=300)
        self.tabela_status.column("qtd", width=150, anchor="center")

    def acao_criar(self):
        try:
            banco.criar_tabelas()
            messagebox.showinfo("OK", "Tabelas criadas com sucesso.")
            self.avisar("Script de criação executado.")
            self.atualizar_tudo()
        except Exception as erro:
            messagebox.showerror("Erro ao criar tabelas", str(erro))

    def acao_inserir(self):
        try:
            banco.inserir_dados()
            messagebox.showinfo("OK", "Dados inseridos com sucesso.")
            self.avisar("Script de inserção executado.")
            self.atualizar_tudo()
        except Exception as erro:
            messagebox.showerror("Erro ao inserir dados", str(erro))

    def acao_apagar(self):
        if not messagebox.askyesno("Confirmar",
                                   "Isso apaga todas as tabelas e dados do "
                                   "banco. Continuar?"):
            return
        try:
            banco.apagar_banco()
            messagebox.showinfo("OK", "Banco apagado. Agora use o botão "
                                      "'1 · Criar Tabelas (DDL)'.")
            self.avisar("Banco apagado.")
            self.atualizar_tudo()
        except Exception as erro:
            messagebox.showerror("Erro ao apagar banco", str(erro))

    def atualizar_status_banco(self):
        self.tabela_status.delete(*self.tabela_status.get_children())
        if not banco.banco_existe():
            self.avisar("Banco ainda não foi criado. Use a aba "
                        "Banco de Dados.")
            return
        for n, (tabela, qtd) in enumerate(banco.contar_registros()):
            self.tabela_status.insert("", "end", values=(tabela, qtd),
                                      tags=("zebra",) if n % 2 else ())

    # ==================================================================
    # OPERACAO 2 - TERREIROS (cadastro + atribuicao de pessoas)
    # ==================================================================
    def aba_terreiros(self):
        aba = self.nova_aba(self.nb_operacao, "Terreiros")
        aba.grid_columnconfigure(1, weight=1)
        aba.grid_rowconfigure(0, weight=2)
        aba.grid_rowconfigure(1, weight=3)

        # ---------- formulario de novo terreiro
        externo, form = self.cartao(aba, "Novo terreiro",
                                    "Campos com * são obrigatórios.")
        externo.grid(row=0, column=0, rowspan=2, sticky="nsew",
                     padx=(0, 12))
        grade = ttk.Frame(form, style="Cartao.TFrame")
        grade.pack(fill="x")
        grade.grid_columnconfigure(0, weight=1, minsize=170)
        grade.grid_columnconfigure(1, weight=1, minsize=170)

        self.ft = {}
        self.ft["nome"] = self.campo(grade, "Nome do terreiro *", 0, 0, 2)
        self.ft["religiao"] = self.campo(
            grade, "Religião *", 1, 0,
            widget=ttk.Combobox(grade, values=RELIGIOES))
        self.ft["nacao"] = self.campo(grade, "Nação *", 1, 1)
        self.ft["regente"] = self.campo(grade, "Regente (orixá) *", 2, 0)
        self.ft["ano"] = self.campo(grade, "Ano de fundação *", 2, 1)
        self.ft["lideranca"] = self.campo(
            grade, "Liderança (escolha ou digite um nome novo) *", 3, 0, 2,
            widget=ttk.Combobox(grade))
        self.ft["logradouro"] = self.campo(grade, "Endereço *", 4, 0, 2)
        self.ft["bairro"] = self.campo(
            grade, "Bairro *", 5, 0,
            widget=ttk.Combobox(grade, state="readonly"))
        self.ft["cep"] = self.campo(grade, "CEP", 5, 1)
        self.ft["lat"] = self.campo(grade, "Latitude *", 6, 0)
        self.ft["lon"] = self.campo(grade, "Longitude *", 6, 1)

        botoes = ttk.Frame(form, style="Cartao.TFrame")
        botoes.pack(fill="x", pady=(16, 0))
        ttk.Button(botoes, text="Escolher no mapa",
                   command=self.escolher_no_mapa).pack(side="left")
        ttk.Button(botoes, text="Salvar terreiro", style="Primario.TButton",
                   command=self.salvar_terreiro).pack(side="right")

        # ---------- lista de terreiros
        externo, lista = self.cartao(
            aba, "Terreiros cadastrados",
            "Selecione um terreiro para ver e atribuir pessoas a ele.")
        externo.grid(row=0, column=1, sticky="nsew", pady=(0, 12))
        quadro, self.tv_terreiros = self.criar_tabela(lista, height=6)
        quadro.pack(fill="both", expand=True)
        self.tv_terreiros.bind("<<TreeviewSelect>>",
                               self.selecionar_terreiro)
        ttk.Button(lista, text="Excluir terreiro selecionado",
                   command=self.excluir_terreiro).pack(anchor="e",
                                                       pady=(8, 0))

        # ---------- atribuicao de pessoas
        externo, atrib = self.cartao(aba, "Pessoas do terreiro")
        externo.grid(row=1, column=1, sticky="nsew")
        self.lbl_atrib = ttk.Label(atrib, style="Sub.TLabel",
                                   text="Nenhum terreiro selecionado.")
        self.lbl_atrib.pack(anchor="w", pady=(0, 8))

        colunas = ttk.Frame(atrib, style="Cartao.TFrame")
        colunas.pack(fill="both", expand=True)
        colunas.grid_columnconfigure(0, weight=1, uniform="c")
        colunas.grid_columnconfigure(2, weight=1, uniform="c")
        colunas.grid_rowconfigure(1, weight=1)

        ttk.Label(colunas, text="Membros deste terreiro",
                  style="Rotulo.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(colunas, text="Pessoas de outros terreiros "
                                "(selecione uma ou várias)",
                  style="Rotulo.TLabel").grid(row=0, column=2, sticky="w")
        q1, self.tv_membros_do = self.criar_tabela(colunas, height=5)
        q1.grid(row=1, column=0, sticky="nsew", pady=4)
        q2, self.tv_outros = self.criar_tabela(colunas, height=5,
                                               selectmode="extended")
        q2.grid(row=1, column=2, sticky="nsew", pady=4)

        meio = ttk.Frame(colunas, style="Cartao.TFrame")
        meio.grid(row=1, column=1, padx=10)
        ttk.Button(meio, text="◀  Atribuir", style="Primario.TButton",
                   command=self.atribuir_selecionados).pack()

        rapido = ttk.Frame(atrib, style="Cartao.TFrame")
        rapido.pack(fill="x", pady=(8, 0))
        ttk.Label(rapido, text="Adicionar pessoa nova a este terreiro:",
                  style="Rotulo.TLabel").pack(side="left")
        self.nova_pessoa = ttk.Entry(rapido, width=34)
        self.nova_pessoa.pack(side="left", padx=8)
        self.nova_pessoa.bind("<Return>", lambda e: self.adicionar_pessoa())
        ttk.Button(rapido, text="Adicionar", style="Destaque.TButton",
                   command=self.adicionar_pessoa).pack(side="left")

    def carregar_aba_terreiros(self):
        for tv in (self.tv_terreiros, self.tv_membros_do, self.tv_outros):
            tv.delete(*tv.get_children())
        if not banco.banco_existe():
            self.terreiro_sel = None
            self.lbl_atrib.config(text="Crie o banco primeiro.")
            return

        _, lid = banco.executar_consulta(
            "SELECT id_lideranca, nome FROM lideranca_religiosa "
            "ORDER BY nome")
        self.liderancas = lid
        self.ft["lideranca"]["values"] = [n for _, n in lid]

        _, bai = banco.executar_consulta(
            "SELECT b.id_bairro, b.nome || ' — ' || c.nome FROM bairro b "
            "JOIN cidade c ON c.id_cidade = b.id_cidade "
            "ORDER BY c.id_cidade, b.nome")
        self.bairros = bai
        self.ft["bairro"]["values"] = [n for _, n in bai]

        lista = painel.terreiros()
        self.preencher_tabela(
            self.tv_terreiros,
            ["id", "Terreiro", "Nação", "Bairro", "Liderança", "Membros"],
            [(t["id"], t["nome"], t["nacao"], t["bairro"], t["lideranca"],
              t["membros"]) for t in lista],
            larguras={"id": 40, "Terreiro": 260, "Nação": 170, "Bairro": 150,
                      "Liderança": 200, "Membros": 70})

        ids = [t["id"] for t in lista]
        if self.terreiro_sel in ids:
            item = self.tv_terreiros.get_children()[ids.index(
                self.terreiro_sel)]
            self.tv_terreiros.selection_set(item)
            self.tv_terreiros.see(item)
        else:
            self.terreiro_sel = None
        self.carregar_atribuicao()

    def selecionar_terreiro(self, evento=None):
        sel = self.tv_terreiros.selection()
        if not sel:
            return
        novo = int(self.tv_terreiros.item(sel[0], "values")[0])
        if novo != self.terreiro_sel:
            self.terreiro_sel = novo
            self.carregar_atribuicao()

    def carregar_atribuicao(self):
        if self.terreiro_sel is None:
            self.lbl_atrib.config(text="Selecione um terreiro na lista "
                                       "acima.")
            self.preencher_tabela(self.tv_membros_do, [], [])
            self.preencher_tabela(self.tv_outros, [], [])
            return
        _, [(nome,)] = banco.executar_consulta(
            "SELECT nome FROM terreiro WHERE id_terreiro = ?",
            (self.terreiro_sel,))
        self.lbl_atrib.config(text=f"Terreiro selecionado: {nome}")

        _, linhas = banco.executar_consulta(
            "SELECT id_membro, nome, data_nascimento FROM membro_terreiro "
            "WHERE id_terreiro = ? ORDER BY nome", (self.terreiro_sel,))
        self.preencher_tabela(self.tv_membros_do,
                              ["id", "Nome", "Nascimento"], linhas,
                              larguras={"id": 40, "Nome": 230,
                                        "Nascimento": 95})
        _, linhas = banco.executar_consulta(
            "SELECT m.id_membro, m.nome, t.nome FROM membro_terreiro m "
            "JOIN terreiro t ON t.id_terreiro = m.id_terreiro "
            "WHERE m.id_terreiro <> ? ORDER BY t.nome, m.nome",
            (self.terreiro_sel,))
        self.preencher_tabela(self.tv_outros,
                              ["id", "Nome", "Terreiro atual"], linhas,
                              larguras={"id": 40, "Nome": 210,
                                        "Terreiro atual": 220})

    def atribuir_selecionados(self):
        if self.terreiro_sel is None:
            messagebox.showwarning("Atenção", "Selecione um terreiro.")
            return
        ids = [int(self.tv_outros.item(i, "values")[0])
               for i in self.tv_outros.selection()]
        if not ids:
            messagebox.showwarning("Atenção", "Selecione pelo menos uma "
                                              "pessoa na lista da direita.")
            return
        try:
            banco.atribuir_membros(ids, self.terreiro_sel)
        except Exception as erro:
            messagebox.showerror("Erro ao atribuir", str(erro))
            return
        self.avisar(f"{len(ids)} pessoa(s) atribuída(s) ao terreiro.")
        self.atualizar_tudo()

    def adicionar_pessoa(self):
        nome = self.nova_pessoa.get().strip()
        if self.terreiro_sel is None:
            messagebox.showwarning("Atenção", "Selecione um terreiro.")
            return
        if not nome:
            messagebox.showwarning("Atenção", "Digite o nome da pessoa.")
            return
        try:
            banco.executar_comando(
                "INSERT INTO membro_terreiro (nome, id_terreiro) "
                "VALUES (?, ?)", (nome, self.terreiro_sel))
        except Exception as erro:
            messagebox.showerror("Erro ao salvar", str(erro))
            return
        self.nova_pessoa.delete(0, "end")
        self.avisar(f"{nome} adicionado(a) ao terreiro.")
        self.atualizar_tudo()

    def salvar_terreiro(self):
        if not banco.banco_existe():
            messagebox.showwarning("Atenção", "Crie o banco primeiro.")
            return
        v = {k: w.get().strip() for k, w in self.ft.items()}
        faltando = [k for k in ("nome", "religiao", "nacao", "regente", "ano",
                                "lideranca", "logradouro", "bairro", "lat",
                                "lon") if not v[k]]
        if faltando:
            messagebox.showwarning("Atenção", "Preencha todos os campos "
                                              "obrigatórios (*).")
            return
        try:
            ano = int(v["ano"])
            assert 1500 < ano <= date.today().year
        except (ValueError, AssertionError):
            messagebox.showwarning("Atenção", "Ano de fundação inválido.")
            return
        try:
            lat = float(v["lat"].replace(",", "."))
            lon = float(v["lon"].replace(",", "."))
            assert -90 <= lat <= 90 and -180 <= lon <= 180
        except (ValueError, AssertionError):
            messagebox.showwarning("Atenção", "Latitude/longitude inválidas. "
                                              "Use 'Escolher no mapa'.")
            return

        id_bairro = self.bairros[self.ft["bairro"].current()][0]
        id_lid, nova_lid = None, None
        nomes = {n: i for i, n in self.liderancas}
        if v["lideranca"] in nomes:
            id_lid = nomes[v["lideranca"]]
        else:
            nova_lid = v["lideranca"]

        try:
            novo_id = banco.criar_terreiro(
                v["nome"], v["religiao"], v["nacao"], v["regente"], ano,
                v["logradouro"], id_bairro, v["cep"], lat, lon,
                id_lideranca=id_lid, nova_lideranca=nova_lid)
        except Exception as erro:
            messagebox.showerror("Erro ao salvar terreiro", str(erro))
            return

        for k, w in self.ft.items():
            if k == "bairro":
                w.set("")
            else:
                w.delete(0, "end")
        self.terreiro_sel = novo_id
        messagebox.showinfo("OK", f"Terreiro '{v['nome']}' cadastrado. "
                                  "Agora você já pode atribuir pessoas a ele.")
        self.avisar("Terreiro salvo no banco.")
        self.atualizar_tudo()

    def excluir_terreiro(self):
        if self.terreiro_sel is None:
            messagebox.showwarning("Atenção", "Selecione um terreiro.")
            return
        if not messagebox.askyesno("Confirmar", "Excluir o terreiro "
                                                "selecionado?"):
            return
        try:
            banco.excluir_terreiro(self.terreiro_sel)
        except Exception as erro:
            messagebox.showerror("Não foi possível excluir", str(erro))
            return
        self.terreiro_sel = None
        self.avisar("Terreiro excluído.")
        self.atualizar_tudo()

    def escolher_no_mapa(self):
        if tkintermapview is None:
            messagebox.showinfo(
                "Mapa indisponível",
                "Instale o mapa com:  pip install tkintermapview\n"
                "ou digite a latitude/longitude manualmente.")
            return
        janela = tk.Toplevel(self)
        janela.title("Clique no mapa para marcar o terreiro")
        janela.geometry("820x600")
        janela.configure(bg=FUNDO)
        janela.transient(self)

        info = tk.Label(janela, text="Clique no local do terreiro e depois "
                                     "em Confirmar.", bg=FUNDO, fg=TEXTO_2,
                        font=(FONTE, 10))
        info.pack(fill="x", pady=6)
        mapa = tkintermapview.TkinterMapView(janela, corner_radius=0)
        mapa.pack(fill="both", expand=True, padx=8)
        mapa.set_position(*CENTRO_RECIFE)
        mapa.set_zoom(12)
        escolhido = {}

        def clique(coords):
            mapa.delete_all_marker()
            mapa.set_marker(*coords, marker_color_circle="white",
                            marker_color_outside=COR_TERREIRO)
            escolhido["c"] = coords
            info.config(text=f"Local: {coords[0]:.6f}, {coords[1]:.6f}")

        def confirmar():
            if "c" in escolhido:
                for chave, valor in zip(("lat", "lon"), escolhido["c"]):
                    self.ft[chave].delete(0, "end")
                    self.ft[chave].insert(0, f"{valor:.7f}")
            janela.destroy()

        mapa.add_left_click_map_command(clique)
        ttk.Button(janela, text="Confirmar", style="Primario.TButton",
                   command=confirmar).pack(pady=8)

    # ==================================================================
    # OPERACAO 3 - CADASTRO DE MEMBRO
    # ==================================================================
    def aba_cadastro(self):
        aba = self.nova_aba(self.nb_operacao, "Membros")
        aba.grid_columnconfigure(1, weight=1)
        aba.grid_rowconfigure(0, weight=1)

        externo, form = self.cartao(aba, "Cadastro de membro",
                                    "Campos com * são obrigatórios.")
        externo.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        grade = ttk.Frame(form, style="Cartao.TFrame")
        grade.pack(fill="x")
        grade.grid_columnconfigure(0, weight=1, minsize=320)

        self.campos = {}
        rotulos = [
            ("nome", "Nome completo *"),
            ("data_nascimento", "Data de nascimento (DD/MM/AAAA)"),
            ("fone", "Telefone"),
            ("email", "E-mail"),
        ]
        for i, (chave, texto) in enumerate(rotulos):
            self.campos[chave] = self.campo(grade, texto, i, 0)
        self.combo_terreiro = self.campo(
            grade, "Terreiro *", len(rotulos), 0,
            widget=ttk.Combobox(grade, state="readonly"))

        ttk.Button(form, text="Salvar membro", style="Primario.TButton",
                   command=self.salvar_membro).pack(anchor="e", pady=(18, 0))

        externo, lista = self.cartao(aba, "Membros cadastrados")
        externo.grid(row=0, column=1, sticky="nsew")
        quadro, self.tabela_membros = self.criar_tabela(lista, height=14)
        quadro.pack(fill="both", expand=True)

    def carregar_terreiros_combo(self):
        """Busca os terreiros no banco para preencher a lista suspensa."""
        if not banco.banco_existe():
            self.terreiros = []
            self.combo_terreiro["values"] = []
            self.combo_terreiro.set("")
            self.preencher_tabela(self.tabela_membros, [], [])
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
            messagebox.showwarning("Atenção", "Informe o nome do membro.")
            return
        if indice < 0:
            messagebox.showwarning("Atenção", "Selecione o terreiro.")
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
        self.avisar("Membro salvo no banco.")
        self.atualizar_tudo()

    def listar_membros(self):
        colunas, linhas = banco.executar_consulta("""
            SELECT m.id_membro   AS id,
                   m.nome        AS membro,
                   m.data_nascimento AS nascimento,
                   t.nome        AS terreiro
            FROM membro_terreiro m
            JOIN terreiro t ON t.id_terreiro = m.id_terreiro
            ORDER BY m.id_membro DESC
        """)
        self.preencher_tabela(self.tabela_membros, colunas, linhas,
                              larguras={"id": 50, "membro": 260,
                                        "nascimento": 110, "terreiro": 280})

    # ==================================================================
    # OPERACAO 4 - CONSULTAS DQL
    # ==================================================================
    def aba_consultas(self):
        aba = self.nova_aba(self.nb_operacao, "Consultas (DQL)")

        externo, esquerda = self.cartao(aba, "Consultas disponíveis")
        externo.pack(side="left", fill="y", padx=(0, 12))

        self.lista = tk.Listbox(esquerda, width=50, height=23,
                                font=(FONTE, 9), bd=0, highlightthickness=0,
                                activestyle="none", selectbackground=PRIMARIA,
                                selectforeground="white", bg=CARTAO,
                                fg=TEXTO)
        self.lista.pack(pady=8, fill="y", expand=True)
        for c in CONSULTAS:
            self.lista.insert("end", "  " + c["titulo"])
        self.lista.bind("<<ListboxSelect>>", self.mostrar_sql)

        ttk.Button(esquerda, text="Executar consulta",
                   style="Primario.TButton",
                   command=self.executar_consulta_selecionada).pack(fill="x")

        externo, direita = self.cartao(aba, "SQL da consulta")
        externo.pack(side="left", fill="both", expand=True)

        self.caixa_sql = scrolledtext.ScrolledText(
            direita, height=11, font=("Consolas", 10), bg="#fbfaf7",
            relief="flat", highlightthickness=1, highlightbackground=BORDA)
        self.caixa_sql.pack(fill="x", pady=(6, 12))

        ttk.Label(direita, text="Resultado", style="Titulo.TLabel").pack(
            anchor="w", pady=(0, 6))
        quadro, self.resultado = self.criar_tabela(direita, horizontal=True)
        quadro.pack(fill="both", expand=True)

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
            messagebox.showwarning("Atenção",
                                   "Crie o banco antes de consultar.")
            return
        sql = self.caixa_sql.get("1.0", "end").strip()
        try:
            colunas, linhas = banco.executar_consulta(sql)
        except Exception as erro:
            messagebox.showerror("Erro na consulta", str(erro))
            return
        self.preencher_tabela(self.resultado, colunas, linhas)
        self.avisar(f"{len(linhas)} registro(s) encontrado(s).")

    # ==================================================================
    # OPERACAO 5 - SQL LIVRE
    # ==================================================================
    def aba_sql_livre(self):
        aba = self.nova_aba(self.nb_operacao, "SQL Livre")
        externo, card = self.cartao(aba, "Digite um comando SQL e execute")
        externo.pack(fill="both", expand=True)

        self.sql_livre = scrolledtext.ScrolledText(
            card, height=9, font=("Consolas", 10), bg="#fbfaf7",
            relief="flat", highlightthickness=1, highlightbackground=BORDA)
        self.sql_livre.pack(fill="x", pady=(8, 0))
        self.sql_livre.insert("1.0", "SELECT * FROM terreiro;")

        ttk.Button(card, text="Executar", style="Primario.TButton",
                   command=self.executar_sql_livre).pack(anchor="w", pady=10)

        quadro, self.resultado_livre = self.criar_tabela(card,
                                                         horizontal=True)
        quadro.pack(fill="both", expand=True)

    def executar_sql_livre(self):
        if not banco.banco_existe():
            messagebox.showwarning("Atenção", "Crie o banco primeiro.")
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
                self.avisar("Comando executado.")
                self.atualizar_tudo()
        except Exception as erro:
            messagebox.showerror("Erro no SQL", str(erro))

    # ==================================================================
    # GESTAO 1 - VISAO GERAL (indicadores + graficos)
    # ==================================================================
    def aba_painel(self):
        aba = self.nova_aba(self.nb_gestao, "Visão Geral")

        # cartoes de indicadores
        linha_kpi = ttk.Frame(aba)
        linha_kpi.pack(fill="x")
        self.kpis = {}
        definicoes = [
            ("terreiros", "Terreiros mapeados", COR_TERREIRO),
            ("membros", "Membros cadastrados", PRIMARIA),
            ("unidades", "Unidades de saúde", COR_UNIDADE),
            ("cobertura", "Membros com cadastro em unidade", PRIMARIA),
            ("dist_media", "Distância média até a unidade mais próxima",
             PRIMARIA),
        ]
        for i, (chave, nome, cor) in enumerate(definicoes):
            linha_kpi.grid_columnconfigure(i, weight=1, uniform="kpi")
            externo = tk.Frame(linha_kpi, bg=CARTAO,
                               highlightbackground=BORDA,
                               highlightthickness=1)
            externo.grid(row=0, column=i, sticky="nsew",
                         padx=(0 if i == 0 else 10, 0))
            tk.Frame(externo, bg=cor, width=5).pack(side="left", fill="y")
            corpo = ttk.Frame(externo, style="Cartao.TFrame",
                              padding=(14, 10))
            corpo.pack(side="left", fill="both", expand=True)
            ttk.Label(corpo, text=nome, style="KpiNome.TLabel",
                      wraplength=210).pack(anchor="w")
            valor = ttk.Label(corpo, text="–", style="KpiValor.TLabel")
            valor.pack(anchor="w")
            self.kpis[chave] = valor

        # grade 2x2 de graficos
        grade = ttk.Frame(aba)
        grade.pack(fill="both", expand=True, pady=(12, 0))
        grade.grid_columnconfigure(0, weight=1, uniform="g")
        grade.grid_columnconfigure(1, weight=1, uniform="g")
        grade.grid_rowconfigure(0, weight=1, uniform="r")
        grade.grid_rowconfigure(1, weight=1, uniform="r")

        titulos = [
            ("cobertura", "Membros por terreiro",
             "Quantos já têm cadastro em alguma unidade de saúde"),
            ("distancia", "Distância até a unidade de saúde mais próxima",
             "Em linha reta, por terreiro (km)"),
            ("idade", "Faixa etária dos membros",
             "Pessoas por faixa de idade"),
            ("atendidos", "Membros vinculados por unidade de saúde",
             "Carga de atendimento de membros de terreiros"),
        ]
        self.graficos = {}
        for n, (chave, titulo, sub) in enumerate(titulos):
            externo, card = self.cartao(grade, titulo, sub, padding=12)
            externo.grid(row=n // 2, column=n % 2, sticky="nsew",
                         padx=(0 if n % 2 == 0 else 10, 0),
                         pady=(0 if n < 2 else 10, 0))
            fig = Figure(figsize=(5, 2.6), dpi=100, facecolor=CARTAO)
            canvas = FigureCanvasTkAgg(fig, master=card)
            canvas.get_tk_widget().configure(bg=CARTAO, highlightthickness=0)
            canvas.get_tk_widget().pack(fill="both", expand=True)
            fig.dicas = []
            canvas.mpl_connect("motion_notify_event",
                               lambda e, f=fig: self._dica_grafico(e, f))
            self.graficos[chave] = (fig, canvas)

    def atualizar_gestao(self):
        """Redesenha o painel do gestor se os dados mudaram."""
        if self.modo != "gestao" or not self.painel_desatualizado:
            return
        if not banco.banco_existe():
            for v in self.kpis.values():
                v.config(text="–")
            for fig, canvas in self.graficos.values():
                fig.clear()
                fig.text(0.5, 0.5, "Crie o banco para ver os dados",
                         ha="center", color=TEXTO_2)
                canvas.draw_idle()
            self.avisar("Banco ainda não foi criado.")
            return
        self.painel_desatualizado = False
        self.lista_t = painel.terreiros()
        self.lista_u = painel.unidades()
        self.desenhar_painel()
        self.carregar_mapa()
        self.carregar_proximidade()

    def _eixo(self, fig, horizontal=True):
        fig.clear()
        ax = fig.add_subplot(111)
        ax.set_facecolor(CARTAO)
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)
        ax.spines["left" if horizontal else "bottom"].set_color(BORDA)
        ax.spines["bottom" if horizontal else "left"].set_visible(False)
        ax.grid(axis="x" if horizontal else "y", color="#eeeae2",
                linewidth=0.8)
        ax.set_axisbelow(True)
        ax.tick_params(length=0)
        fig.dicas = []
        return ax

    def _registrar_dicas(self, fig, ax, barras, textos):
        dica = ax.annotate("", xy=(0, 0), xytext=(12, 12),
                           textcoords="offset points", fontsize=8,
                           color="white", zorder=10,
                           bbox=dict(boxstyle="round,pad=0.5", fc=TEXTO,
                                     ec="none", alpha=0.92),
                           annotation_clip=False)
        dica.set_visible(False)
        fig.dicas.append((ax, list(barras), textos, dica))

    def _dica_grafico(self, evento, fig):
        mudou = False
        for ax, barras, textos, dica in fig.dicas:
            achou = False
            if evento.inaxes == ax:
                for barra, texto in zip(barras, textos):
                    if barra.contains(evento)[0]:
                        dica.xy = (evento.xdata, evento.ydata)
                        dica.set_text(texto)
                        # perto da borda direita a dica abre para a esquerda
                        x0, x1 = ax.get_xlim()
                        esquerda = (evento.xdata - x0) / (x1 - x0) > 0.6
                        dica.set_position((-12 if esquerda else 12, 12))
                        dica.set_horizontalalignment(
                            "right" if esquerda else "left")
                        achou = True
                        break
            if dica.get_visible() != achou or achou:
                dica.set_visible(achou)
                mudou = True
        if mudou:
            fig.canvas.draw_idle()

    def desenhar_painel(self):
        ind = painel.indicadores()
        self.kpis["terreiros"].config(text=str(ind["terreiros"]))
        self.kpis["membros"].config(text=str(ind["membros"]))
        self.kpis["unidades"].config(text=str(ind["unidades"]))
        self.kpis["cobertura"].config(text=f"{ind['cobertura']:.0f}%")
        self.kpis["dist_media"].config(
            text="–" if ind["dist_media"] is None
            else f"{ind['dist_media']:.1f} km".replace(".", ","))

        self._grafico_cobertura()
        self._grafico_distancia()
        self._grafico_idade()
        self._grafico_atendidos()
        for fig, canvas in self.graficos.values():
            fig.tight_layout(pad=0.6)
            canvas.draw_idle()

    def _grafico_cobertura(self):
        fig, _ = self.graficos["cobertura"]
        ax = self._eixo(fig)
        dados = list(reversed(painel.cobertura_por_terreiro()))
        if not dados:
            return
        nomes = [encurtar(n, 26) for n, _, _ in dados]
        com = [c for _, _, c in dados]
        sem = [t - c for _, t, c in dados]
        b1 = ax.barh(nomes, com, color=COR_UNIDADE, height=0.62,
                     edgecolor=CARTAO, linewidth=2, label="Com cadastro")
        b2 = ax.barh(nomes, sem, left=com, color=COR_NEUTRA, height=0.62,
                     edgecolor=CARTAO, linewidth=2, label="Sem cadastro")
        maximo = max(t for _, t, _ in dados) or 1
        for i, (_, t, _) in enumerate(dados):
            ax.text(t + maximo * 0.02, i, str(t), va="center", fontsize=8,
                    color=TEXTO_2)
        ax.set_xlim(0, maximo * 1.12)
        ax.xaxis.get_major_locator().set_params(integer=True)
        ax.legend(loc="lower right", frameon=False, fontsize=8, ncol=2,
                  bbox_to_anchor=(1, 1), borderaxespad=0.2)
        textos = [f"{n}\n{c} de {t} com cadastro" for n, t, c in dados]
        self._registrar_dicas(fig, ax, b1, textos)
        self._registrar_dicas(fig, ax, b2, textos)

    def _grafico_distancia(self):
        fig, _ = self.graficos["distancia"]
        ax = self._eixo(fig)
        if not self.lista_t or not self.lista_u:
            return
        dados = []
        for t in self.lista_t:
            d, u = painel.proximas(t, self.lista_u, 1)[0]
            dados.append((t["nome"], d, u["nome"]))
        dados.sort(key=lambda x: x[1])
        nomes = [encurtar(n, 26) for n, _, _ in dados]
        dist = [d for _, d, _ in dados]
        barras = ax.barh(nomes, dist, color=COR_TERREIRO, height=0.62)
        maximo = max(dist) or 1
        for i, d in enumerate(dist):
            ax.text(d + maximo * 0.02, i, f"{d:.1f}".replace(".", ","),
                    va="center", fontsize=8, color=TEXTO_2)
        ax.set_xlim(0, maximo * 1.15)
        ax.axvline(1, color=TEXTO_2, linewidth=1, linestyle=(0, (3, 3)))
        ax.text(1, len(dados) - 0.4, " 1 km", fontsize=8, color=TEXTO_2,
                va="bottom")
        self._registrar_dicas(
            fig, ax, barras,
            [f"{n}\nMais próxima: {encurtar(u, 40)}\n"
             f"{d:.2f} km".replace(".", ",") for n, d, u in dados])

    def _grafico_idade(self):
        fig, _ = self.graficos["idade"]
        ax = self._eixo(fig, horizontal=False)
        faixas, sem_data = painel.faixas_etarias()
        nomes = [f for f, _ in faixas]
        qtd = [q for _, q in faixas]
        barras = ax.bar(nomes, qtd, color=COR_UNIDADE, width=0.6)
        maximo = max(qtd) if qtd and max(qtd) else 1
        for i, q in enumerate(qtd):
            ax.text(i, q + maximo * 0.02, str(q), ha="center",
                    va="bottom", fontsize=8, color=TEXTO_2)
        ax.set_ylim(0, maximo * 1.18)
        ax.yaxis.get_major_locator().set_params(integer=True)
        ax.tick_params(axis="x", colors=TEXTO)
        if sem_data:
            ax.set_title(f"{sem_data} pessoa(s) sem data de nascimento",
                         loc="right", fontsize=8, color=TEXTO_2)
        self._registrar_dicas(fig, ax, barras,
                              [f"{f} anos: {q} pessoa(s)"
                               for f, q in faixas])

    def _grafico_atendidos(self):
        fig, _ = self.graficos["atendidos"]
        ax = self._eixo(fig)
        dados = sorted(self.lista_u, key=lambda u: u["atendidos"])
        if not dados:
            return
        nomes = [encurtar(f"{u['sigla']} · {u['nome']}", 30) for u in dados]
        qtd = [u["atendidos"] for u in dados]
        barras = ax.barh(nomes, qtd, color=COR_UNIDADE, height=0.62)
        maximo = max(qtd) or 1
        for i, q in enumerate(qtd):
            ax.text(q + maximo * 0.02, i, str(q), va="center", fontsize=8,
                    color=TEXTO_2)
        ax.set_xlim(0, maximo * 1.15)
        ax.xaxis.get_major_locator().set_params(integer=True)
        self._registrar_dicas(
            fig, ax, barras,
            [f"{u['nome']}\n{u['bairro']} · {u['atendidos']} membro(s)"
             for u in dados])

    # ==================================================================
    # GESTAO 2 - MAPA
    # ==================================================================
    def aba_mapa(self):
        aba = self.nova_aba(self.nb_gestao, "Mapa")
        aba.grid_columnconfigure(1, weight=1)
        aba.grid_rowconfigure(0, weight=1)

        lateral = ttk.Frame(aba, width=470)
        lateral.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        lateral.pack_propagate(False)

        externo, card = self.cartao(lateral, "Terreiros",
                                    "Clique para ver as unidades de saúde "
                                    "mais próximas.")
        externo.pack(fill="both", expand=True)
        quadro, self.tv_mapa_t = self.criar_tabela(card, height=8)
        quadro.pack(fill="both", expand=True)
        self.tv_mapa_t.bind("<<TreeviewSelect>>", self.focar_terreiro_mapa)

        externo, card = self.cartao(lateral, "Unidades próximas")
        externo.pack(fill="both", expand=True, pady=(12, 0))
        raio = ttk.Frame(card, style="Cartao.TFrame")
        raio.pack(fill="x", pady=(4, 8))
        ttk.Label(raio, text="Mostrar até:", style="Rotulo.TLabel").pack(
            side="left")
        self.combo_raio = ttk.Combobox(raio, state="readonly", width=12,
                                       values=["1 km", "2 km", "3 km",
                                               "5 km", "Todas"])
        self.combo_raio.set("3 km")
        self.combo_raio.pack(side="left", padx=8)
        self.combo_raio.bind("<<ComboboxSelected>>",
                             lambda e: self.focar_terreiro_mapa())
        quadro, self.tv_mapa_u = self.criar_tabela(card, height=7)
        quadro.pack(fill="both", expand=True)

        # legenda + mapa
        externo, card = self.cartao(aba, padding=8)
        externo.grid(row=0, column=1, sticky="nsew")
        legenda = ttk.Frame(card, style="Cartao.TFrame")
        legenda.pack(fill="x", pady=(0, 6))
        for cor, texto in ((COR_TERREIRO, "Terreiro"),
                           (COR_UNIDADE, "Unidade de saúde")):
            tk.Label(legenda, text="●", fg=cor, bg=CARTAO,
                     font=(FONTE, 13)).pack(side="left")
            tk.Label(legenda, text=texto, fg=TEXTO, bg=CARTAO,
                     font=(FONTE, 9)).pack(side="left", padx=(2, 14))
        tk.Label(legenda, text="Clique num marcador para ver o nome",
                 fg=TEXTO_2, bg=CARTAO, font=(FONTE, 9)).pack(side="right")

        if tkintermapview is not None:
            self.mapa = tkintermapview.TkinterMapView(card, corner_radius=0)
            self.mapa.pack(fill="both", expand=True)
            self.mapa.set_position(*CENTRO_RECIFE)
            self.mapa.set_zoom(12)
        else:
            self.mapa = None
            self.fig_mapa = Figure(figsize=(6, 5), dpi=100,
                                   facecolor=CARTAO)
            self.canvas_mapa = FigureCanvasTkAgg(self.fig_mapa, master=card)
            self.canvas_mapa.get_tk_widget().pack(fill="both", expand=True)
            tk.Label(card, text="Para um mapa com ruas instale: "
                                "pip install tkintermapview",
                     fg=TEXTO_2, bg=CARTAO, font=(FONTE, 8)).pack()
        self.marcadores_t = {}
        self.caminhos = []

    def raio_km(self):
        valor = self.combo_raio.get()
        return None if valor == "Todas" else float(valor.split()[0])

    def carregar_mapa(self):
        self.preencher_tabela(
            self.tv_mapa_t, ["id", "Terreiro", "Bairro", "Mais próxima"],
            [(t["id"], t["nome"], t["bairro"],
              f"{painel.proximas(t, self.lista_u, 1)[0][0]:.1f} km".replace(
                  ".", ",")
              if self.lista_u else "–") for t in self.lista_t],
            larguras={"id": 34, "Terreiro": 200, "Bairro": 110,
                      "Mais próxima": 80})
        self.preencher_tabela(self.tv_mapa_u, [], [])

        if self.mapa is None:
            self._mapa_estatico()
            return

        self.mapa.delete_all_marker()
        self.mapa.delete_all_path()
        self.caminhos = []
        self.marcadores_t = {}

        def alternar_nome(marcador):
            marcador.set_text("" if marcador.text else marcador.data)

        for u in self.lista_u:
            m = self.mapa.set_marker(
                u["lat"], u["lon"], text="", data=f"{u['sigla']} · "
                f"{encurtar(u['nome'], 30)}",
                marker_color_circle="white",
                marker_color_outside=COR_UNIDADE, text_color=COR_UNIDADE,
                font=(FONTE, 9, "bold"), command=alternar_nome)
        for t in self.lista_t:
            m = self.mapa.set_marker(
                t["lat"], t["lon"], text="", data=encurtar(t["nome"], 30),
                marker_color_circle="white",
                marker_color_outside=COR_TERREIRO, text_color="#9a3b14",
                font=(FONTE, 9, "bold"), command=alternar_nome)
            self.marcadores_t[t["id"]] = m

        pontos = [(p["lat"], p["lon"]) for p in self.lista_t + self.lista_u]
        if len(pontos) >= 2:
            lats = [p[0] for p in pontos]
            lons = [p[1] for p in pontos]
            folga = 0.01
            self.mapa.fit_bounding_box(
                (max(lats) + folga, min(lons) - folga),
                (min(lats) - folga, max(lons) + folga))

    def _mapa_estatico(self, destaque=None, proximas=()):
        """Mapa simples (sem ruas) usado quando nao ha tkintermapview."""
        ax = self._eixo(self.fig_mapa, horizontal=False)
        ax.grid(color="#eeeae2")
        ax.spines["bottom"].set_visible(False)
        ax.spines["left"].set_visible(False)
        for _, u in proximas:
            ax.plot([destaque["lon"], u["lon"]], [destaque["lat"], u["lat"]],
                    color=COR_UNIDADE, linewidth=1.5, alpha=0.6)
        ax.scatter([u["lon"] for u in self.lista_u],
                   [u["lat"] for u in self.lista_u], s=60, c=COR_UNIDADE,
                   edgecolors=CARTAO, linewidths=2, label="Unidade de saúde",
                   zorder=3)
        ax.scatter([t["lon"] for t in self.lista_t],
                   [t["lat"] for t in self.lista_t], s=80, c=COR_TERREIRO,
                   edgecolors=CARTAO, linewidths=2, label="Terreiro",
                   zorder=4)
        if destaque:
            ax.annotate(destaque["nome"], (destaque["lon"], destaque["lat"]),
                        xytext=(8, 8), textcoords="offset points",
                        fontsize=9, color=TEXTO, weight="bold")
        ax.set_aspect("equal", adjustable="datalim")
        ax.set_xlabel("longitude")
        self.fig_mapa.tight_layout()
        self.canvas_mapa.draw_idle()

    def focar_terreiro_mapa(self, evento=None):
        sel = self.tv_mapa_t.selection()
        if not sel or not self.lista_u:
            return
        id_t = int(self.tv_mapa_t.item(sel[0], "values")[0])
        t = next(x for x in self.lista_t if x["id"] == id_t)
        raio = self.raio_km()
        todas = painel.proximas(t, self.lista_u)
        perto = [(d, u) for d, u in todas if raio is None or d <= raio]

        linhas = [(f"{d:.2f}".replace(".", ","), u["sigla"], u["nome"],
                   u["fone"]) for d, u in perto]
        if not linhas:
            d, u = todas[0]
            linhas = [(f"{d:.2f}".replace(".", ","), u["sigla"],
                       u["nome"] + "  (fora do raio — a mais próxima)",
                       u["fone"])]
            perto = [todas[0]]
        self.preencher_tabela(self.tv_mapa_u,
                              ["km", "Tipo", "Unidade", "Telefone"], linhas,
                              larguras={"km": 50, "Tipo": 50,
                                        "Unidade": 230, "Telefone": 100})
        self.avisar(f"{t['nome']}: {len(perto)} unidade(s) listada(s).")

        if self.mapa is None:
            self._mapa_estatico(t, perto)
            return

        for c in self.caminhos:
            c.delete()
        self.caminhos = []
        for m in self.marcadores_t.values():
            m.set_text("")
        for _, u in perto:
            self.caminhos.append(self.mapa.set_path(
                [(t["lat"], t["lon"]), (u["lat"], u["lon"])],
                color=COR_UNIDADE, width=3))
        marcador = self.marcadores_t.get(id_t)
        if marcador:
            marcador.set_text(marcador.data)
        self.mapa.set_position(t["lat"], t["lon"])
        self.mapa.set_zoom(14)

    # ==================================================================
    # GESTAO 3 - PROXIMIDADE (tabela-resumo)
    # ==================================================================
    def aba_proximidade(self):
        aba = self.nova_aba(self.nb_gestao, "Proximidade")
        externo, card = self.cartao(
            aba, "Terreiros × unidades de saúde",
            "Para cada terreiro: as duas unidades mais próximas e quantas "
            "existem num raio de 2 km. Distâncias em linha reta. Em "
            "vermelho: terreiros sem nenhuma unidade de saúde a até 2 km.")
        externo.pack(fill="both", expand=True)
        quadro, self.tv_prox = self.criar_tabela(card, horizontal=True)
        quadro.pack(fill="both", expand=True, pady=(4, 0))
        self.tv_prox.tag_configure("longe", foreground=DESTAQUE)

    def carregar_proximidade(self):
        linhas = []
        for t in self.lista_t:
            p = painel.proximas(t, self.lista_u)
            def fmt(i):
                if i >= len(p):
                    return "–", "–"
                d, u = p[i]
                return f"{u['sigla']} · {u['nome']}", \
                       f"{d:.2f} km".replace(".", ",")
            u1, d1 = fmt(0)
            u2, d2 = fmt(1)
            em_2km = sum(1 for d, _ in p if d <= 2)
            linhas.append((t["nome"], t["bairro"], t["membros"], u1, d1, u2,
                           d2, em_2km))
        self.preencher_tabela(
            self.tv_prox,
            ["Terreiro", "Bairro", "Membros", "Mais próxima", "Distância",
             "2ª mais próxima", "Distância 2", "Unidades em 2 km"],
            linhas,
            larguras={"Terreiro": 250, "Bairro": 140, "Membros": 70,
                      "Mais próxima": 280, "Distância": 85,
                      "2ª mais próxima": 280, "Distância 2": 85,
                      "Unidades em 2 km": 110})
        # destaca terreiros sem nenhuma unidade num raio de 2 km
        for item, linha in zip(self.tv_prox.get_children(), linhas):
            if linha[-1] == 0:
                self.tv_prox.item(item, tags=("longe",))

    # ==================================================================
    # PERFIL TERREIRO 1 - MEU TERREIRO
    # ==================================================================
    def aba_meu_terreiro(self):
        aba = self.nova_aba(self.nb_terreiro, "Meu Terreiro")
        aba.grid_columnconfigure(1, weight=1)
        aba.grid_rowconfigure(1, weight=1)

        # ---------- ficha do terreiro (linha de cartoes)
        self.ficha = ttk.Frame(aba)
        self.ficha.grid(row=0, column=0, columnspan=2, sticky="ew",
                        pady=(0, 12))

        # ---------- novo membro
        externo, form = self.cartao(aba, "Cadastrar pessoa",
                                    "A pessoa entra direto no seu terreiro.")
        externo.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        grade = ttk.Frame(form, style="Cartao.TFrame")
        grade.pack(fill="x")
        grade.grid_columnconfigure(0, weight=1, minsize=300)
        self.campos_t = {}
        for i, (chave, texto) in enumerate([
                ("nome", "Nome completo *"),
                ("data_nascimento", "Data de nascimento (DD/MM/AAAA)"),
                ("fone", "Telefone"),
                ("email", "E-mail")]):
            self.campos_t[chave] = self.campo(grade, texto, i, 0)
        ttk.Button(form, text="Salvar pessoa", style="Primario.TButton",
                   command=self.salvar_membro_terreiro).pack(anchor="e",
                                                             pady=(18, 0))

        # ---------- lista de membros + vinculo com unidade de saude
        externo, lista = self.cartao(
            aba, "Membros do terreiro",
            "Selecione um membro para vinculá-lo a uma unidade de saúde "
            "ou removê-lo.")
        externo.grid(row=1, column=1, sticky="nsew")
        quadro, self.tv_meus = self.criar_tabela(lista, height=10)
        quadro.pack(fill="both", expand=True)
        self.tv_meus.tag_configure("sem", foreground=DESTAQUE)

        acoes = ttk.Frame(lista, style="Cartao.TFrame")
        acoes.pack(fill="x", pady=(10, 0))
        ttk.Label(acoes, text="Vincular à unidade:",
                  style="Rotulo.TLabel").pack(side="left")
        self.combo_vinculo = ttk.Combobox(acoes, state="readonly", width=48)
        self.combo_vinculo.pack(side="left", padx=8)
        ttk.Button(acoes, text="Vincular", style="Primario.TButton",
                   command=self.vincular_unidade).pack(side="left")
        ttk.Button(acoes, text="Remover membro",
                   command=self.remover_meu_membro).pack(side="right")
        ttk.Label(lista, style="Sub.TLabel",
                  text="Em vermelho: membros ainda sem cadastro em "
                       "unidade de saúde.").pack(anchor="w", pady=(8, 0))

    def carregar_meu_terreiro(self):
        t = next((x for x in painel.terreiros() if x["id"] == self.meu_id),
                 None)
        if t is None:
            messagebox.showwarning("Atenção", "Seu terreiro não foi "
                                              "encontrado no banco.")
            self.tela_login()
            return
        self.meu_t = t
        self.lista_u = painel.unidades()
        self.perto = painel.proximas(t, self.lista_u)

        # ficha
        for w in self.ficha.winfo_children():
            w.destroy()
        _, [(religiao, regente, ano)] = banco.executar_consulta(
            "SELECT religiao, regente, ano_fundacao FROM terreiro "
            "WHERE id_terreiro = ?", (self.meu_id,))
        _, [(com_cadastro,)] = banco.executar_consulta(
            "SELECT COUNT(DISTINCT mu.id_membro) FROM membro_unidade_saude mu"
            " JOIN membro_terreiro m ON m.id_membro = mu.id_membro "
            "WHERE m.id_terreiro = ?", (self.meu_id,))
        mais_perto = (f"{self.perto[0][0]:.1f} km".replace(".", ",")
                      if self.perto else "–")
        itens = [
            ("Membros", str(t["membros"]), COR_TERREIRO),
            ("Com cadastro em unidade de saúde",
             f"{com_cadastro} de {t['membros']}", COR_UNIDADE),
            ("Unidade de saúde mais próxima", mais_perto, COR_UNIDADE),
            ("Religião · Nação", f"{religiao} · {t['nacao']}", PRIMARIA),
            ("Regente · Fundação", f"{regente} · {ano}", PRIMARIA),
            ("Liderança", t["lideranca"], PRIMARIA),
        ]
        for i, (nome, valor, cor) in enumerate(itens):
            self.ficha.grid_columnconfigure(i, weight=1, uniform="f")
            externo = tk.Frame(self.ficha, bg=CARTAO,
                               highlightbackground=BORDA,
                               highlightthickness=1)
            externo.grid(row=0, column=i, sticky="nsew",
                         padx=(0 if i == 0 else 10, 0))
            tk.Frame(externo, bg=cor, width=5).pack(side="left", fill="y")
            corpo = ttk.Frame(externo, style="Cartao.TFrame",
                              padding=(12, 8))
            corpo.pack(side="left", fill="both", expand=True)
            ttk.Label(corpo, text=nome, style="KpiNome.TLabel",
                      wraplength=180).pack(anchor="w")
            grande = i < 3
            if grande:
                rotulo = ttk.Label(corpo, text=valor,
                                   style="KpiValor.TLabel")
            else:
                rotulo = ttk.Label(corpo, text=encurtar(valor, 40),
                                   style="Cartao.TLabel", wraplength=200,
                                   font=(FONTE, 10, "bold"))
            rotulo.pack(anchor="w", pady=(2, 0))

        # membros
        _, linhas = banco.executar_consulta("""
            SELECT m.id_membro, m.nome, m.data_nascimento, m.fone,
                   GROUP_CONCAT(s.sigla || ' · ' || u.nome, '  |  ')
            FROM membro_terreiro m
            LEFT JOIN membro_unidade_saude mu ON mu.id_membro = m.id_membro
            LEFT JOIN unidade_saude u ON u.id_unidade = mu.id_unidade
            LEFT JOIN servico_saude s ON s.id_servico = u.id_servico
            WHERE m.id_terreiro = ?
            GROUP BY m.id_membro
            ORDER BY m.nome
        """, (self.meu_id,))
        self.preencher_tabela(
            self.tv_meus,
            ["id", "Nome", "Nascimento", "Telefone", "Unidades de saúde"],
            [l[:4] + (l[4] or "sem cadastro",) for l in linhas],
            larguras={"id": 40, "Nome": 220, "Nascimento": 95,
                      "Telefone": 110, "Unidades de saúde": 360})
        for item, l in zip(self.tv_meus.get_children(), linhas):
            if not l[4]:
                self.tv_meus.item(item, tags=("sem",))

        # unidades no combo, da mais perto para a mais longe
        self.combo_vinculo["values"] = [
            f"{d:.1f} km — {u['sigla']} · {u['nome']}".replace(".", ",", 1)
            for d, u in self.perto]
        if self.perto:
            self.combo_vinculo.current(0)

        self.carregar_saude_perto()

    def _membro_selecionado(self):
        sel = self.tv_meus.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um membro na "
                                              "lista.")
            return None
        valores = self.tv_meus.item(sel[0], "values")
        return int(valores[0]), valores[1]

    def salvar_membro_terreiro(self):
        nome = self.campos_t["nome"].get().strip()
        if not nome:
            messagebox.showwarning("Atenção", "Informe o nome da pessoa.")
            return
        try:
            banco.executar_comando(
                """INSERT INTO membro_terreiro
                       (nome, data_nascimento, fone, email, id_terreiro)
                   VALUES (?, ?, ?, ?, ?)""",
                (nome,
                 self.campos_t["data_nascimento"].get().strip(),
                 self.campos_t["fone"].get().strip(),
                 self.campos_t["email"].get().strip(),
                 self.meu_id))
        except Exception as erro:
            messagebox.showerror("Erro ao salvar", str(erro))
            return
        for entrada in self.campos_t.values():
            entrada.delete(0, "end")
        self.avisar(f"{nome} cadastrado(a) no terreiro.")
        self.atualizar_tudo()

    def vincular_unidade(self):
        membro = self._membro_selecionado()
        indice = self.combo_vinculo.current()
        if membro is None or indice < 0:
            return
        unidade = self.perto[indice][1]
        try:
            banco.vincular_membro_unidade(membro[0], unidade["id"])
        except Exception as erro:
            messagebox.showwarning("Atenção", str(erro))
            return
        self.avisar(f"{membro[1]} vinculado(a) a {unidade['nome']}.")
        self.atualizar_tudo()

    def remover_meu_membro(self):
        membro = self._membro_selecionado()
        if membro is None:
            return
        if not messagebox.askyesno("Confirmar",
                                   f"Remover {membro[1]} do terreiro?"):
            return
        try:
            banco.remover_membro(membro[0])
        except Exception as erro:
            messagebox.showerror("Erro ao remover", str(erro))
            return
        self.avisar(f"{membro[1]} removido(a).")
        self.atualizar_tudo()

    # ==================================================================
    # PERFIL TERREIRO 2 - SAUDE PERTO DE MIM
    # ==================================================================
    def aba_saude_perto(self):
        aba = self.nova_aba(self.nb_terreiro, "Saúde perto de mim")
        aba.grid_columnconfigure(1, weight=1)
        aba.grid_rowconfigure(0, weight=1)

        lateral = ttk.Frame(aba, width=500)
        lateral.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        lateral.pack_propagate(False)
        externo, card = self.cartao(
            lateral, "Unidades de saúde",
            "Da mais perto para a mais longe (distância em linha reta).")
        externo.pack(fill="both", expand=True)
        raio = ttk.Frame(card, style="Cartao.TFrame")
        raio.pack(fill="x", pady=(4, 8))
        ttk.Label(raio, text="Ligar no mapa as unidades até:",
                  style="Rotulo.TLabel").pack(side="left")
        self.combo_raio_t = ttk.Combobox(raio, state="readonly", width=10,
                                         values=["1 km", "2 km", "3 km",
                                                 "5 km", "Todas"])
        self.combo_raio_t.set("3 km")
        self.combo_raio_t.pack(side="left", padx=8)
        self.combo_raio_t.bind("<<ComboboxSelected>>",
                               lambda e: self.desenhar_saude_perto())
        quadro, self.tv_perto = self.criar_tabela(card, height=12)
        quadro.pack(fill="both", expand=True)
        self.tv_perto.bind("<<TreeviewSelect>>", self.focar_unidade_perto)

        externo, card = self.cartao(aba, padding=8)
        externo.grid(row=0, column=1, sticky="nsew")
        legenda = ttk.Frame(card, style="Cartao.TFrame")
        legenda.pack(fill="x", pady=(0, 6))
        for cor, texto in ((COR_TERREIRO, "Meu terreiro"),
                           (COR_UNIDADE, "Unidade de saúde")):
            tk.Label(legenda, text="●", fg=cor, bg=CARTAO,
                     font=(FONTE, 13)).pack(side="left")
            tk.Label(legenda, text=texto, fg=TEXTO, bg=CARTAO,
                     font=(FONTE, 9)).pack(side="left", padx=(2, 14))
        if tkintermapview is not None:
            self.mapa_t = tkintermapview.TkinterMapView(card,
                                                        corner_radius=0)
            self.mapa_t.pack(fill="both", expand=True)
        else:
            self.mapa_t = None
            tk.Label(card, text="Para ver o mapa instale: "
                                "pip install tkintermapview",
                     fg=TEXTO_2, bg=CARTAO, font=(FONTE, 10)).pack(
                expand=True)

    def carregar_saude_perto(self):
        self.preencher_tabela(
            self.tv_perto, ["km", "Tipo", "Unidade", "Bairro", "Telefone",
                            "Horário"],
            [(f"{d:.2f}".replace(".", ","), u["sigla"], u["nome"],
              u["bairro"], u["fone"], u["horario"]) for d, u in self.perto],
            larguras={"km": 50, "Tipo": 50, "Unidade": 230, "Bairro": 120,
                      "Telefone": 110, "Horário": 200})
        self.desenhar_saude_perto()

    def desenhar_saude_perto(self, tentativas=20):
        if self.mapa_t is None or not self.mapa_t.winfo_exists():
            return
        # so desenha com a aba visivel e o mapa ja com tamanho real
        if self.nb_terreiro.index("current") != 1:
            return
        self.update_idletasks()
        if self.mapa_t.winfo_width() < 100 and tentativas:
            self.after(100, lambda: self.desenhar_saude_perto(tentativas - 1))
            return
        t = self.meu_t
        valor = self.combo_raio_t.get()
        raio = None if valor == "Todas" else float(valor.split()[0])
        self.mapa_t.delete_all_marker()
        self.mapa_t.delete_all_path()
        self.marcadores_perto = []
        for d, u in self.perto:
            if raio is None or d <= raio:
                self.mapa_t.set_path([(t["lat"], t["lon"]),
                                      (u["lat"], u["lon"])],
                                     color=COR_UNIDADE, width=3)
            m = self.mapa_t.set_marker(
                u["lat"], u["lon"], text="",
                data=f"{u['sigla']} · {encurtar(u['nome'], 30)}",
                marker_color_circle="white",
                marker_color_outside=COR_UNIDADE, text_color=COR_UNIDADE,
                font=(FONTE, 9, "bold"),
                command=lambda mk: mk.set_text("" if mk.text else mk.data))
            self.marcadores_perto.append(m)
        self.mapa_t.set_marker(
            t["lat"], t["lon"], text=encurtar(t["nome"], 30),
            marker_color_circle="white", marker_color_outside=COR_TERREIRO,
            text_color="#9a3b14", font=(FONTE, 10, "bold"))
        self.mapa_t.set_position(t["lat"], t["lon"])
        self.mapa_t.set_zoom(14 if raio and raio <= 2 else 13)

    def focar_unidade_perto(self, evento=None):
        sel = self.tv_perto.selection()
        if not sel or self.mapa_t is None:
            return
        i = self.tv_perto.index(sel[0])
        for n, m in enumerate(self.marcadores_perto):
            m.set_text(m.data if n == i else "")
        u = self.perto[i][1]
        self.mapa_t.set_position(u["lat"], u["lon"])


if __name__ == "__main__":
    Aplicacao().mainloop()
