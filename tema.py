"""
Tema visual da aplicacao (cores, fontes e estilos ttk).
"""

from tkinter import ttk

# ---------------------------------------------------------------- cores
FUNDO = "#f4f1ea"          # fundo geral (areia clara)
CARTAO = "#ffffff"         # fundo dos cartoes
BORDA = "#e2ddd2"
PRIMARIA = "#1f4d3a"       # verde-folha escuro (cabecalho, botoes)
PRIMARIA_HOVER = "#2b6650"
DESTAQUE = "#c8553d"       # terracota (acoes de destaque)
DESTAQUE_HOVER = "#a94532"
TEXTO = "#1d1d1b"
TEXTO_2 = "#5b5a55"
TEXTO_CLARO = "#d7e8df"
ZEBRA = "#f8f6f1"
SELECAO = "#cfe5d9"

# cores dos dados (paleta categorica validada: azul / laranja)
COR_UNIDADE = "#2a78d6"    # unidades de saude
COR_TERREIRO = "#eb6834"   # terreiros
COR_NEUTRA = "#c9c6bd"     # "sem cadastro", trilhas, grades

FONTE = "Segoe UI"


def aplicar(raiz):
    """Configura todos os estilos ttk usados na tela."""
    raiz.configure(bg=FUNDO)
    estilo = ttk.Style(raiz)
    estilo.theme_use("clam")

    estilo.configure(".", background=FUNDO, foreground=TEXTO,
                     font=(FONTE, 10))

    # ---- notebook (abas)
    estilo.configure("TNotebook", background=FUNDO, borderwidth=0,
                     tabmargins=(12, 8, 12, 0))
    estilo.configure("TNotebook.Tab", padding=(16, 8), font=(FONTE, 10),
                     background="#e6e1d6", foreground=TEXTO_2, borderwidth=0)
    estilo.map("TNotebook.Tab",
               background=[("selected", CARTAO), ("active", "#efebe2")],
               foreground=[("selected", PRIMARIA)],
               font=[("selected", (FONTE, 10, "bold"))])

    # ---- frames
    estilo.configure("TFrame", background=FUNDO)
    estilo.configure("Cartao.TFrame", background=CARTAO)
    estilo.configure("TLabelframe", background=CARTAO, bordercolor=BORDA)

    # ---- textos
    estilo.configure("TLabel", background=FUNDO, foreground=TEXTO)
    estilo.configure("Cartao.TLabel", background=CARTAO)
    estilo.configure("Titulo.TLabel", background=CARTAO, foreground=PRIMARIA,
                     font=(FONTE, 13, "bold"))
    estilo.configure("Sub.TLabel", background=CARTAO, foreground=TEXTO_2,
                     font=(FONTE, 9))
    estilo.configure("Rotulo.TLabel", background=CARTAO, foreground=TEXTO_2,
                     font=(FONTE, 9, "bold"))
    estilo.configure("KpiValor.TLabel", background=CARTAO,
                     foreground=TEXTO, font=(FONTE, 22, "bold"))
    estilo.configure("KpiNome.TLabel", background=CARTAO,
                     foreground=TEXTO_2, font=(FONTE, 9))

    # ---- botoes
    estilo.configure("TButton", padding=(14, 7), font=(FONTE, 10),
                     background="#e9e5dc", foreground=TEXTO, borderwidth=0,
                     focuscolor=FUNDO)
    estilo.map("TButton", background=[("active", "#ddd7ca")])
    estilo.configure("Primario.TButton", background=PRIMARIA,
                     foreground="white", font=(FONTE, 10, "bold"))
    estilo.map("Primario.TButton",
               background=[("active", PRIMARIA_HOVER),
                           ("disabled", "#9db3a8")])
    estilo.configure("Destaque.TButton", background=DESTAQUE,
                     foreground="white", font=(FONTE, 10, "bold"))
    estilo.map("Destaque.TButton", background=[("active", DESTAQUE_HOVER)])

    # ---- entradas
    estilo.configure("TEntry", fieldbackground="white", bordercolor=BORDA,
                     lightcolor=BORDA, darkcolor=BORDA, padding=5)
    estilo.map("TEntry", bordercolor=[("focus", PRIMARIA)],
               lightcolor=[("focus", PRIMARIA)])
    estilo.configure("TCombobox", fieldbackground="white", bordercolor=BORDA,
                     lightcolor=BORDA, darkcolor=BORDA, padding=5,
                     arrowcolor=PRIMARIA)
    estilo.map("TCombobox", fieldbackground=[("readonly", "white")],
               bordercolor=[("focus", PRIMARIA)])

    # ---- tabelas
    estilo.configure("Treeview", background=CARTAO, fieldbackground=CARTAO,
                     foreground=TEXTO, rowheight=28, borderwidth=0,
                     font=(FONTE, 9))
    estilo.configure("Treeview.Heading", background=PRIMARIA,
                     foreground="white", font=(FONTE, 9, "bold"),
                     padding=(8, 6), borderwidth=0, relief="flat")
    estilo.map("Treeview.Heading", background=[("active", PRIMARIA_HOVER)])
    estilo.map("Treeview", background=[("selected", SELECAO)],
               foreground=[("selected", TEXTO)])

    estilo.configure("Vertical.TScrollbar", background="#e0dbd0",
                     troughcolor=FUNDO, borderwidth=0, arrowcolor=TEXTO_2)
    estilo.configure("Horizontal.TScrollbar", background="#e0dbd0",
                     troughcolor=FUNDO, borderwidth=0, arrowcolor=TEXTO_2)
    return estilo
