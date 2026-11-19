"""
Terreiros & Saude - versao WEB (Streamlit).

Mesmas funcoes do app desktop (app.py), agora no navegador:
  - Login sem senha com dois perfis: Terreiro e Gestor
  - Terreiro: ficha, membros, vinculo com unidades de saude, mapa
  - Gestor:   Painel (indicadores, graficos, mapa, proximidade) e
              Administracao (banco, terreiros, membros, consultas, SQL)

Para rodar localmente:  streamlit run streamlit_app.py
"""

import html
import itertools
import math
from datetime import date

import altair as alt
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

import banco
import painel
from consultas import CONSULTAS

# ---------------------------------------------------------------- cores
PRIMARIA = "#1f4d3a"
DESTAQUE = "#c8553d"
FUNDO = "#f4f1ea"
BORDA = "#e2ddd2"
TEXTO = "#1d1d1b"
TEXTO_2 = "#5b5a55"
COR_UNIDADE = "#2a78d6"
COR_TERREIRO = "#eb6834"
COR_NEUTRA = "#c9c6bd"
CENTRO_RECIFE = (-8.05, -34.92)
RELIGIOES = ["Candomblé", "Umbanda", "Jurema", "Xambá", "Quimbanda"]
RAIOS = {"1 km": 1, "2 km": 2, "3 km": 3, "5 km": 5, "Todas": None}

st.set_page_config(page_title="Terreiros & Saúde", page_icon="🌿",
                   layout="wide")

CSS = f"""
<style>
.block-container {{ padding-top: 3.2rem; padding-bottom: 2rem; }}
.topo {{
    background: {PRIMARIA}; color: white; border-radius: 14px;
    padding: 18px 24px; margin-bottom: 18px;
    display: flex; align-items: center; justify-content: space-between;
}}
.topo .marca {{ display: flex; align-items: center; gap: 14px; }}
.topo .losango {{ color: #e9c46a; font-size: 30px; line-height: 1; }}
.topo h1 {{ color: white; font-size: 1.5rem; margin: 0; padding: 0; }}
.topo p {{ color: #d7e8df; margin: 0; font-size: .85rem; }}
.topo .quem {{ text-align: right; }}
.topo .quem small {{ color: #e9c46a; font-weight: 700;
                     letter-spacing: .08em; font-size: .7rem; }}
.topo .quem div {{ color: white; font-size: .95rem; }}
.kpi {{
    background: white; border: 1px solid {BORDA}; border-radius: 12px;
    padding: 12px 16px; border-left: 6px solid var(--cor); height: 100%;
}}
.kpi .nome {{ color: {TEXTO_2}; font-size: .8rem; }}
.kpi .valor {{ color: {TEXTO}; font-size: 1.9rem; font-weight: 700;
               line-height: 1.25; }}
.kpi .valor.peq {{ font-size: 1rem; padding-top: 6px; }}
.hero {{ text-align: center; padding: 30px 0 10px; }}
.hero .losango {{ color: #e9c46a; font-size: 42px; }}
.hero h1 {{ color: {PRIMARIA}; font-size: 2.4rem; margin-bottom: 0; }}
.hero p {{ color: {TEXTO_2}; }}
.faixa {{ height: 6px; border-radius: 6px; margin-bottom: 10px; }}
.legenda span {{ margin-right: 16px; font-size: .85rem; color: {TEXTO}; }}
.legenda b {{ font-size: 1.1rem; }}
div[class*="st-key-cartao_"] {{ background: white; border-radius: 12px; }}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ======================================================================
# UTILITARIOS
# ======================================================================
_cartoes = itertools.count()


def cartao():
    """Container com borda e fundo branco (a chave gera a classe CSS)."""
    return st.container(border=True, key=f"cartao_{next(_cartoes)}")

def km(valor, casas=1):
    return f"{valor:.{casas}f} km".replace(".", ",")


def kpi(coluna, nome, valor, cor, pequeno=False):
    coluna.markdown(
        f'<div class="kpi" style="--cor:{cor}">'
        f'<div class="nome">{html.escape(nome)}</div>'
        f'<div class="valor{" peq" if pequeno else ""}">'
        f'{html.escape(str(valor))}</div></div>',
        unsafe_allow_html=True)


def cabecalho(perfil, usuario):
    st.markdown(
        f'<div class="topo"><div class="marca"><div class="losango">◆</div>'
        f'<div><h1>Terreiros &amp; Saúde</h1>'
        f'<p>Mapeamento de terreiros e unidades de saúde · Recife/PE</p>'
        f'</div></div><div class="quem"><small>{perfil.upper()}</small>'
        f'<div>{html.escape(usuario)}</div></div></div>',
        unsafe_allow_html=True)


def avisar(texto, tipo="success"):
    """Mensagem que sobrevive ao st.rerun()."""
    st.session_state["aviso"] = (texto, tipo)


def mostrar_aviso():
    if "aviso" in st.session_state:
        texto, tipo = st.session_state.pop("aviso")
        getattr(st, tipo)(texto)


def limpar(*chaves):
    for c in chaves:
        st.session_state.pop(c, None)


def garantir_banco():
    """Na nuvem o banco pode nao existir: cria e carrega os dados."""
    if not banco.banco_existe():
        banco.criar_tabelas()
        banco.inserir_dados()


def mapa_base(pontos, zoom=12):
    """Mapa OpenStreetMap centrado nos pontos.

    O enquadramento e calculado aqui (e nao com fit_bounds no navegador),
    porque mapas dentro de abas escondidas calculam o zoom errado.
    """
    centro = CENTRO_RECIFE
    if pontos:
        lats = [p[0] for p in pontos]
        lons = [p[1] for p in pontos]
        centro = ((min(lats) + max(lats)) / 2, (min(lons) + max(lons)) / 2)
        extensao = max(max(lats) - min(lats), max(lons) - min(lons))
        if extensao > 0:
            # ~550 px de mapa: 256 px cobrem 360 graus no zoom 0
            zoom = int(math.log2(550 * 360 / (256 * extensao * 1.3)))
        zoom = max(10, min(zoom, 16))
    return folium.Map(location=centro, zoom_start=zoom,
                      tiles="OpenStreetMap", control_scale=True)


def marcador(m, lat, lon, cor, titulo, detalhe="", raio=9):
    folium.CircleMarker(
        location=(lat, lon), radius=raio, color="white", weight=2,
        fill=True, fill_color=cor, fill_opacity=1,
        tooltip=titulo,
        popup=folium.Popup(f"<b>{html.escape(titulo)}</b><br>"
                           f"{html.escape(detalhe)}", max_width=280),
    ).add_to(m)


def ligacao(m, origem, destino, distancia):
    folium.PolyLine([origem, destino], color=COR_UNIDADE, weight=3,
                    opacity=.75, dash_array="6 6",
                    tooltip=km(distancia, 2)).add_to(m)


def legenda(itens):
    partes = "".join(f'<span><b style="color:{c}">●</b> {html.escape(t)}'
                     f'</span>' for c, t in itens)
    st.markdown(f'<div class="legenda">{partes}</div>',
                unsafe_allow_html=True)


def barras_horizontais(df, x, y, cor, titulo_x, tooltip, regra=None):
    base = alt.Chart(df).encode(
        y=alt.Y(f"{y}:N", sort="-x", title=None,
                scale=alt.Scale(paddingInner=0.35),
                axis=alt.Axis(labelLimit=220)),
        x=alt.X(f"{x}:Q", title=titulo_x),
        tooltip=tooltip)
    barras = base.mark_bar(color=cor, cornerRadiusEnd=4)
    rotulos = base.mark_text(align="left", dx=4, color=TEXTO_2,
                             fontSize=11).encode(
        text=alt.Text(f"{x}:Q", format=".1f" if regra else "d"))
    grafico = barras + rotulos
    if regra:
        linha = alt.Chart(pd.DataFrame({"x": [regra]})).mark_rule(
            strokeDash=[4, 4], color=TEXTO_2).encode(x="x:Q")
        grafico = grafico + linha
    return grafico.properties(height=max(200, 30 * len(df))) \
        .configure(background="white") \
        .configure_view(stroke=None) \
        .configure_axis(grid=True, gridColor="#eeeae2", domain=False)


# ======================================================================
# LOGIN
# ======================================================================
def tela_login():
    st.markdown(
        '<style>section[data-testid="stSidebar"]{display:none}</style>'
        '<div class="hero"><div class="losango">◆</div>'
        '<h1>Terreiros &amp; Saúde</h1>'
        '<p>Mapeamento de terreiros e unidades de saúde · Recife/PE</p>'
        '</div>', unsafe_allow_html=True)

    _, c1, c2, _ = st.columns([1, 2, 2, 1], gap="large")
    with c1:
        with cartao():
            st.markdown(f'<div class="faixa" style="background:'
                        f'{COR_TERREIRO}"></div>', unsafe_allow_html=True)
            st.subheader("Sou um terreiro")
            st.caption("Veja seus membros, cadastre pessoas, vincule-as a "
                       "unidades de saúde e encontre os postos mais perto.")
            _, lista = banco.executar_consulta(
                "SELECT id_terreiro, nome FROM terreiro ORDER BY nome")
            nomes = {i: n for i, n in lista}
            escolhido = st.selectbox("Qual é o seu terreiro?",
                                     list(nomes), format_func=nomes.get,
                                     index=None,
                                     placeholder="Selecione...")
            if st.button("Entrar como terreiro", type="primary",
                         width="stretch", disabled=escolhido is None):
                st.session_state.update(perfil="terreiro", meu_id=escolhido)
                st.rerun()
    with c2:
        with cartao():
            st.markdown(f'<div class="faixa" style="background:'
                        f'{COR_UNIDADE}"></div>', unsafe_allow_html=True)
            st.subheader("Sou gestor(a)")
            st.caption("Painel com indicadores e gráficos, mapa de "
                       "terreiros e unidades de saúde, cadastro de "
                       "terreiros e administração do banco.")
            st.write("")
            st.write("")
            st.write("")
            if st.button("Entrar como gestor", type="primary",
                         width="stretch"):
                st.session_state.update(perfil="gestor")
                st.rerun()
    st.markdown(f'<p style="text-align:center;color:{TEXTO_2};'
                f'font-size:.85rem;margin-top:18px">Acesso sem senha — '
                f'escolha o perfil para continuar.</p>',
                unsafe_allow_html=True)


def barra_lateral(texto):
    with st.sidebar:
        st.markdown(f"### 🌿 Terreiros & Saúde")
        st.caption(texto)
        if st.button("Sair", width="stretch"):
            for c in list(st.session_state):
                del st.session_state[c]
            st.rerun()


# ======================================================================
# PERFIL TERREIRO
# ======================================================================
def acao_salvar_pessoa(id_terreiro, prefixo):
    nome = st.session_state.get(f"{prefixo}nome", "").strip()
    if not nome:
        avisar("Informe o nome da pessoa.", "warning")
        return
    try:
        banco.executar_comando(
            "INSERT INTO membro_terreiro "
            "(nome, data_nascimento, fone, email, id_terreiro) "
            "VALUES (?, ?, ?, ?, ?)",
            (nome,
             st.session_state.get(f"{prefixo}nasc", "").strip(),
             st.session_state.get(f"{prefixo}fone", "").strip(),
             st.session_state.get(f"{prefixo}email", "").strip(),
             id_terreiro))
    except Exception as erro:
        avisar(f"Erro ao salvar: {erro}", "error")
        return
    limpar(*(prefixo + c for c in ("nome", "nasc", "fone", "email")))
    avisar(f"{nome} cadastrado(a) no terreiro.")


def campos_pessoa(prefixo):
    st.text_input("Nome completo *", key=f"{prefixo}nome")
    st.text_input("Data de nascimento (DD/MM/AAAA)", key=f"{prefixo}nasc")
    c1, c2 = st.columns(2)
    c1.text_input("Telefone", key=f"{prefixo}fone")
    c2.text_input("E-mail", key=f"{prefixo}email")


def pagina_terreiro():
    id_t = st.session_state["meu_id"]
    t = next((x for x in painel.terreiros() if x["id"] == id_t), None)
    if t is None:
        st.error("Seu terreiro não foi encontrado no banco.")
        barra_lateral("")
        return
    barra_lateral(f"Conectado como terreiro:\n\n**{t['nome']}**")
    cabecalho("Terreiro", t["nome"])
    mostrar_aviso()

    unidades = painel.unidades()
    perto = painel.proximas(t, unidades)
    _, [(religiao, regente, ano)] = banco.executar_consulta(
        "SELECT religiao, regente, ano_fundacao FROM terreiro "
        "WHERE id_terreiro = ?", (id_t,))
    _, [(com_cadastro,)] = banco.executar_consulta(
        "SELECT COUNT(DISTINCT mu.id_membro) FROM membro_unidade_saude mu "
        "JOIN membro_terreiro m ON m.id_membro = mu.id_membro "
        "WHERE m.id_terreiro = ?", (id_t,))

    aba1, aba2 = st.tabs(["Meu Terreiro", "Saúde perto de mim"])

    with aba1:
        cols = st.columns(6)
        kpi(cols[0], "Membros", t["membros"], COR_TERREIRO)
        kpi(cols[1], "Com cadastro em unidade de saúde",
            f"{com_cadastro} de {t['membros']}", COR_UNIDADE)
        kpi(cols[2], "Unidade de saúde mais próxima",
            km(perto[0][0]) if perto else "–", COR_UNIDADE)
        kpi(cols[3], "Religião · Nação", f"{religiao} · {t['nacao']}",
            PRIMARIA, pequeno=True)
        kpi(cols[4], "Regente · Fundação", f"{regente} · {ano}", PRIMARIA,
            pequeno=True)
        kpi(cols[5], "Liderança", t["lideranca"], PRIMARIA, pequeno=True)
        st.write("")

        esq, dir_ = st.columns([1, 2], gap="medium")
        with esq:
            with cartao():
                st.subheader("Cadastrar pessoa")
                st.caption("A pessoa entra direto no seu terreiro.")
                campos_pessoa("t_")
                st.button("Salvar pessoa", type="primary", width="stretch",
                          on_click=acao_salvar_pessoa, args=(id_t, "t_"))

        with dir_:
            with cartao():
                st.subheader("Membros do terreiro")
                _, linhas = banco.executar_consulta("""
                    SELECT m.id_membro, m.nome, m.data_nascimento, m.fone,
                           GROUP_CONCAT(s.sigla || ' · ' || u.nome, '  |  ')
                    FROM membro_terreiro m
                    LEFT JOIN membro_unidade_saude mu
                           ON mu.id_membro = m.id_membro
                    LEFT JOIN unidade_saude u ON u.id_unidade = mu.id_unidade
                    LEFT JOIN servico_saude s ON s.id_servico = u.id_servico
                    WHERE m.id_terreiro = ?
                    GROUP BY m.id_membro ORDER BY m.nome
                """, (id_t,))
                df = pd.DataFrame(linhas, columns=[
                    "id", "Nome", "Nascimento", "Telefone",
                    "Unidades de saúde"])
                df["Unidades de saúde"] = df["Unidades de saúde"].fillna(
                    "sem cadastro")

                def pintar(linha):
                    cor = (f"color:{DESTAQUE}"
                           if linha["Unidades de saúde"] == "sem cadastro"
                           else "")
                    return [cor] * len(linha)

                st.dataframe(df.style.apply(pintar, axis=1), hide_index=True,
                             width="stretch")
                st.caption("Em vermelho: membros ainda sem cadastro em "
                           "unidade de saúde.")

                membros = {i: n for i, n, *_ in linhas}
                if membros:
                    st.markdown("**Vincular membro a uma unidade de saúde**")
                    c1, c2, c3 = st.columns([2, 3, 1],
                                            vertical_alignment="bottom")
                    membro = c1.selectbox("Membro", list(membros),
                                          format_func=membros.get,
                                          key="v_membro")
                    opcoes = list(range(len(perto)))
                    idx = c2.selectbox(
                        "Unidade (da mais perto para a mais longe)", opcoes,
                        format_func=lambda i: f"{km(perto[i][0])} — "
                        f"{perto[i][1]['sigla']} · {perto[i][1]['nome']}",
                        key="v_unidade")
                    if c3.button("Vincular", type="primary",
                                 width="stretch") and idx is not None:
                        try:
                            banco.vincular_membro_unidade(
                                membro, perto[idx][1]["id"])
                            avisar(f"{membros[membro]} vinculado(a) a "
                                   f"{perto[idx][1]['nome']}.")
                        except Exception as erro:
                            avisar(str(erro), "warning")
                        st.rerun()

                    with st.expander("Remover membro"):
                        alvo = st.selectbox("Membro a remover",
                                            list(membros),
                                            format_func=membros.get,
                                            key="r_membro")
                        certeza = st.checkbox("Confirmo que quero remover "
                                              "esta pessoa")
                        if st.button("Remover", disabled=not certeza):
                            banco.remover_membro(alvo)
                            avisar(f"{membros[alvo]} removido(a).")
                            st.rerun()

    with aba2:
        esq, dir_ = st.columns([2, 3], gap="medium")
        with esq:
            with cartao():
                st.subheader("Unidades de saúde")
                st.caption("Da mais perto para a mais longe "
                           "(distância em linha reta).")
                raio_txt = st.segmented_control(
                    "Ligar no mapa as unidades até", list(RAIOS),
                    default="3 km", key="raio_t")
                raio = RAIOS.get(raio_txt or "3 km")
                st.dataframe(pd.DataFrame(
                    [(round(d, 2), u["sigla"], u["nome"], u["bairro"],
                      u["fone"], u["horario"]) for d, u in perto],
                    columns=["km", "Tipo", "Unidade", "Bairro", "Telefone",
                             "Horário"]),
                    hide_index=True, width="stretch", height=420,
                    column_config={"km": st.column_config.NumberColumn(
                        format="%.2f")})
        with dir_:
            with cartao():
                legenda([(COR_TERREIRO, "Meu terreiro"),
                         (COR_UNIDADE, "Unidade de saúde")])
                dentro = [(d, u) for d, u in perto
                          if raio is None or d <= raio]
                pontos = [(t["lat"], t["lon"])] + [
                    (u["lat"], u["lon"]) for _, u in dentro]
                m = mapa_base(pontos, zoom=14)
                for d, u in dentro:
                    ligacao(m, (t["lat"], t["lon"]), (u["lat"], u["lon"]), d)
                for d, u in perto:
                    marcador(m, u["lat"], u["lon"], COR_UNIDADE,
                             f"{u['sigla']} · {u['nome']}",
                             f"{km(d, 2)} · {u['fone']} · {u['horario']}")
                marcador(m, t["lat"], t["lon"], COR_TERREIRO, t["nome"],
                         t["logradouro"], raio=11)
                st_folium(m, height=520, use_container_width=True,
                          returned_objects=[], key="mapa_terreiro")


# ======================================================================
# PERFIL GESTOR - PAINEL
# ======================================================================
def gestor_visao_geral(lista_t, lista_u):
    ind = painel.indicadores()
    cols = st.columns(5)
    kpi(cols[0], "Terreiros mapeados", ind["terreiros"], COR_TERREIRO)
    kpi(cols[1], "Membros cadastrados", ind["membros"], PRIMARIA)
    kpi(cols[2], "Unidades de saúde", ind["unidades"], COR_UNIDADE)
    kpi(cols[3], "Membros com cadastro em unidade",
        f"{ind['cobertura']:.0f}%", PRIMARIA)
    kpi(cols[4], "Distância média até a unidade mais próxima",
        "–" if ind["dist_media"] is None else km(ind["dist_media"]),
        PRIMARIA)
    st.write("")

    c1, c2 = st.columns(2, gap="medium")
    with c1, cartao():
        st.subheader("Membros por terreiro")
        st.caption("Quantos já têm cadastro em alguma unidade de saúde")
        linhas = []
        for nome, total, com in painel.cobertura_por_terreiro():
            linhas.append((nome, "Com cadastro", com, total))
            linhas.append((nome, "Sem cadastro", total - com, total))
        df = pd.DataFrame(linhas, columns=["Terreiro", "Situação", "Membros",
                                           "Total"])
        if not df.empty:
            ordem = (df.drop_duplicates("Terreiro")
                     .sort_values("Total", ascending=False)["Terreiro"]
                     .tolist())
            grafico = alt.Chart(df).mark_bar(cornerRadius=3).encode(
                y=alt.Y("Terreiro:N", sort=ordem, title=None,
                        scale=alt.Scale(paddingInner=0.35),
                        axis=alt.Axis(labelLimit=220)),
                x=alt.X("Membros:Q", title="membros",
                        axis=alt.Axis(tickMinStep=1)),
                color=alt.Color("Situação:N", scale=alt.Scale(
                    domain=["Com cadastro", "Sem cadastro"],
                    range=[COR_UNIDADE, COR_NEUTRA]),
                    legend=alt.Legend(orient="top", title=None)),
                order=alt.Order("Situação:N"),
                tooltip=["Terreiro", "Situação", "Membros", "Total"],
            ).properties(height=34 * len(ordem) + 40) \
                .configure(background="white") \
                .configure_view(stroke=None) \
                .configure_axis(gridColor="#eeeae2", domain=False)
            st.altair_chart(grafico, width="stretch")

    with c2, cartao():
        st.subheader("Distância até a unidade de saúde mais próxima")
        st.caption("Em linha reta, por terreiro (km). Linha tracejada: 1 km")
        if lista_t and lista_u:
            dados = []
            for t in lista_t:
                d, u = painel.proximas(t, lista_u, 1)[0]
                dados.append((t["nome"], round(d, 2), u["nome"]))
            df = pd.DataFrame(dados, columns=["Terreiro", "km",
                                              "Unidade mais próxima"])
            st.altair_chart(barras_horizontais(
                df, "km", "Terreiro", COR_TERREIRO, "km",
                ["Terreiro", "Unidade mais próxima", "km"], regra=1),
                width="stretch")

    c1, c2 = st.columns(2, gap="medium")
    with c1, cartao():
        st.subheader("Faixa etária dos membros")
        faixas, sem_data = painel.faixas_etarias()
        st.caption("Pessoas por faixa de idade" + (
            f" · {sem_data} sem data de nascimento" if sem_data else ""))
        df = pd.DataFrame(faixas, columns=["Faixa", "Pessoas"])
        base = alt.Chart(df).encode(
            x=alt.X("Faixa:N", sort=None, title="anos",
                    axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Pessoas:Q", title=None, axis=alt.Axis(tickMinStep=1)),
            tooltip=["Faixa", "Pessoas"])
        grafico = (base.mark_bar(color=COR_UNIDADE, cornerRadiusEnd=4,
                                 width=46)
                   + base.mark_text(dy=-8, color=TEXTO_2).encode(
                       text="Pessoas:Q"))
        st.altair_chart(grafico.properties(height=260)
                        .configure(background="white")
                        .configure_view(stroke=None)
                        .configure_axis(gridColor="#eeeae2", domain=False),
                        width="stretch")

    with c2, cartao():
        st.subheader("Membros vinculados por unidade de saúde")
        st.caption("Carga de atendimento de membros de terreiros")
        df = pd.DataFrame(
            [(f"{u['sigla']} · {u['nome']}", u["atendidos"], u["bairro"])
             for u in lista_u], columns=["Unidade", "Membros", "Bairro"])
        if not df.empty:
            st.altair_chart(barras_horizontais(
                df, "Membros", "Unidade", COR_UNIDADE, "membros",
                ["Unidade", "Bairro", "Membros"]), width="stretch")


def gestor_mapa(lista_t, lista_u):
    esq, dir_ = st.columns([2, 3], gap="medium")
    with esq:
        with cartao():
            st.subheader("Terreiros")
            nomes = {t["id"]: t["nome"] for t in lista_t}
            escolhido = st.selectbox(
                "Escolha um terreiro para ver as unidades próximas",
                [None] + list(nomes),
                format_func=lambda i: "Todos (visão geral)" if i is None
                else nomes[i], key="g_mapa_t")
            raio_txt = st.segmented_control("Mostrar unidades até",
                                            list(RAIOS), default="3 km",
                                            key="g_raio")
            raio = RAIOS.get(raio_txt or "3 km")
            if escolhido is None:
                st.dataframe(pd.DataFrame(
                    [(t["nome"], t["bairro"],
                      round(painel.proximas(t, lista_u, 1)[0][0], 2)
                      if lista_u else None) for t in lista_t],
                    columns=["Terreiro", "Bairro", "Mais próxima (km)"]),
                    hide_index=True, width="stretch", height=380)
            else:
                t = next(x for x in lista_t if x["id"] == escolhido)
                todas = painel.proximas(t, lista_u)
                perto = [(d, u) for d, u in todas
                         if raio is None or d <= raio] or todas[:1]
                st.dataframe(pd.DataFrame(
                    [(round(d, 2), u["sigla"], u["nome"], u["fone"])
                     for d, u in perto],
                    columns=["km", "Tipo", "Unidade", "Telefone"]),
                    hide_index=True, width="stretch")
                if perto and raio and perto[0][0] > raio:
                    st.info("Nenhuma unidade no raio escolhido — mostrando "
                            "a mais próxima.")
    with dir_:
        with cartao():
            legenda([(COR_TERREIRO, "Terreiro"),
                     (COR_UNIDADE, "Unidade de saúde")])
            if escolhido is None:
                pontos = [(p["lat"], p["lon"]) for p in lista_t + lista_u]
                m = mapa_base(pontos)
            else:
                pontos = [(t["lat"], t["lon"])] + [
                    (u["lat"], u["lon"]) for _, u in perto]
                m = mapa_base(pontos, zoom=14)
                for d, u in perto:
                    ligacao(m, (t["lat"], t["lon"]), (u["lat"], u["lon"]), d)
            for u in lista_u:
                marcador(m, u["lat"], u["lon"], COR_UNIDADE,
                         f"{u['sigla']} · {u['nome']}",
                         f"{u['bairro']} · {u['fone']}")
            for x in lista_t:
                marcador(m, x["lat"], x["lon"], COR_TERREIRO, x["nome"],
                         f"{x['bairro']} · {x['membros']} membro(s)",
                         raio=11 if x["id"] == escolhido else 9)
            st_folium(m, height=560, use_container_width=True,
                      returned_objects=[], key="mapa_gestor")


def gestor_proximidade(lista_t, lista_u):
    with cartao():
        st.subheader("Terreiros × unidades de saúde")
        st.caption("Para cada terreiro: as duas unidades mais próximas e "
                   "quantas existem num raio de 2 km. Em vermelho: terreiros "
                   "sem nenhuma unidade de saúde a até 2 km.")
        linhas = []
        for t in lista_t:
            p = painel.proximas(t, lista_u)

            def item(i):
                if i >= len(p):
                    return "–", None
                d, u = p[i]
                return f"{u['sigla']} · {u['nome']}", round(d, 2)
            u1, d1 = item(0)
            u2, d2 = item(1)
            linhas.append((t["nome"], t["bairro"], t["membros"], u1, d1, u2,
                           d2, sum(1 for d, _ in p if d <= 2)))
        df = pd.DataFrame(linhas, columns=[
            "Terreiro", "Bairro", "Membros", "Mais próxima", "km",
            "2ª mais próxima", "km (2ª)", "Unidades em 2 km"])

        def pintar(linha):
            cor = f"color:{DESTAQUE}" if linha["Unidades em 2 km"] == 0 \
                else ""
            return [cor] * len(linha)

        st.dataframe(df.style.apply(pintar, axis=1).format(
            {"km": "{:.2f}", "km (2ª)": "{:.2f}"}, na_rep="–"),
            hide_index=True, width="stretch")


# ======================================================================
# PERFIL GESTOR - ADMINISTRACAO
# ======================================================================
def admin_banco():
    with cartao():
        st.subheader("Scripts do banco")
        st.caption("Execute na ordem: criar as tabelas, depois inserir os "
                   "dados. Para começar de novo, apague o banco antes.")
        c1, c2, c3 = st.columns(3)
        try:
            if c1.button("1 · Criar Tabelas (DDL)", type="primary",
                         width="stretch"):
                banco.criar_tabelas()
                avisar("Tabelas criadas com sucesso.")
                st.rerun()
            if c2.button("2 · Inserir Dados (DML)", type="primary",
                         width="stretch"):
                banco.inserir_dados()
                avisar("Dados inseridos com sucesso.")
                st.rerun()
        except Exception as erro:
            st.error(str(erro))
        with c3.popover("Apagar Banco", width="stretch"):
            st.warning("Isso apaga todas as tabelas e dados.")
            if st.button("Sim, apagar tudo", type="primary"):
                banco.apagar_banco()
                avisar("Banco apagado. Agora use '1 · Criar Tabelas'.")
                st.rerun()

    with cartao():
        st.subheader("Registros por tabela")
        if banco.banco_existe():
            st.dataframe(pd.DataFrame(banco.contar_registros(),
                                      columns=["Tabela", "Registros"]),
                         hide_index=True, width="stretch")
        else:
            st.info("O banco ainda não foi criado.")


def acao_salvar_terreiro(bairros, liderancas):
    s = st.session_state
    obrig = {"f_nome": "Nome", "f_religiao": "Religião", "f_nacao": "Nação",
             "f_regente": "Regente", "f_logradouro": "Endereço"}
    faltando = [r for k, r in obrig.items() if not str(s.get(k) or "").strip()]
    lid = s.get("f_lideranca")
    nova_lid = (s.get("f_nova_lid") or "").strip()
    if lid == "nova" and not nova_lid:
        faltando.append("Nome da nova liderança")
    if s.get("f_bairro") is None:
        faltando.append("Bairro")
    if s.get("f_lat") is None or s.get("f_lon") is None:
        faltando.append("Localização (clique no mapa)")
    if faltando:
        avisar("Preencha: " + ", ".join(faltando), "warning")
        return
    try:
        novo = banco.criar_terreiro(
            s["f_nome"].strip(), s["f_religiao"].strip(),
            s["f_nacao"].strip(), s["f_regente"].strip(), int(s["f_ano"]),
            s["f_logradouro"].strip(), s["f_bairro"],
            (s.get("f_cep") or "").strip(), float(s["f_lat"]),
            float(s["f_lon"]),
            id_lideranca=None if lid == "nova" else lid,
            nova_lideranca=nova_lid if lid == "nova" else None)
    except Exception as erro:
        avisar(f"Erro ao salvar terreiro: {erro}", "error")
        return
    avisar(f"Terreiro '{s['f_nome'].strip()}' cadastrado. Agora você já "
           "pode atribuir pessoas a ele.")
    s["a_terreiro"] = novo
    limpar("f_nome", "f_religiao", "f_nacao", "f_regente", "f_ano",
           "f_lideranca", "f_nova_lid", "f_logradouro", "f_bairro", "f_cep",
           "f_lat", "f_lon")


def admin_terreiros():
    _, bairros = banco.executar_consulta(
        "SELECT b.id_bairro, b.nome || ' — ' || c.nome FROM bairro b "
        "JOIN cidade c ON c.id_cidade = b.id_cidade "
        "ORDER BY c.id_cidade, b.nome")
    bairros = dict(bairros)
    _, lids = banco.executar_consulta(
        "SELECT id_lideranca, nome FROM lideranca_religiosa ORDER BY nome")
    lids = dict(lids)
    lista_t = painel.terreiros()

    esq, dir_ = st.columns([1, 1], gap="medium")
    with esq, cartao():
        st.subheader("Novo terreiro")
        st.caption("Campos com * são obrigatórios. Clique no mapa para "
                   "marcar o local.")
        st.text_input("Nome do terreiro *", key="f_nome")
        c1, c2 = st.columns(2)
        c1.selectbox("Religião *", RELIGIOES, index=None,
                     accept_new_options=True, placeholder="Escolha ou digite",
                     key="f_religiao")
        c2.text_input("Nação *", key="f_nacao")
        c1, c2 = st.columns(2)
        c1.text_input("Regente (orixá) *", key="f_regente")
        c2.number_input("Ano de fundação *", min_value=1501,
                        max_value=date.today().year, value=2000, step=1,
                        key="f_ano")
        opcoes = ["nova"] + list(lids)
        st.selectbox("Liderança *", opcoes, index=None,
                     format_func=lambda i: "➕ Nova liderança" if i == "nova"
                     else lids[i], placeholder="Selecione...",
                     key="f_lideranca")
        if st.session_state.get("f_lideranca") == "nova":
            st.text_input("Nome da nova liderança *", key="f_nova_lid")
        st.text_input("Endereço *", key="f_logradouro")
        c1, c2 = st.columns([2, 1])
        c1.selectbox("Bairro *", list(bairros), index=None,
                     format_func=bairros.get, placeholder="Selecione...",
                     key="f_bairro")
        c2.text_input("CEP", key="f_cep")

        m = mapa_base([(t["lat"], t["lon"]) for t in lista_t])
        for t in lista_t:
            marcador(m, t["lat"], t["lon"], COR_NEUTRA, t["nome"], raio=6)
        if (st.session_state.get("f_lat") is not None
                and st.session_state.get("f_lon") is not None):
            marcador(m, st.session_state["f_lat"], st.session_state["f_lon"],
                     COR_TERREIRO, "Novo terreiro", raio=11)
        clique = st_folium(m, height=300, use_container_width=True,
                           returned_objects=["last_clicked"],
                           key="mapa_escolha")
        ponto = (clique or {}).get("last_clicked")
        if ponto and (ponto["lat"], ponto["lng"]) != st.session_state.get(
                "f_ultimo_clique"):
            st.session_state["f_ultimo_clique"] = (ponto["lat"],
                                                   ponto["lng"])
            st.session_state["f_lat"] = round(ponto["lat"], 7)
            st.session_state["f_lon"] = round(ponto["lng"], 7)
            st.rerun()
        for chave in ("f_lat", "f_lon"):
            st.session_state.setdefault(chave, None)
        c1, c2 = st.columns(2)
        c1.number_input("Latitude *", format="%.7f", key="f_lat",
                        min_value=-90.0, max_value=90.0)
        c2.number_input("Longitude *", format="%.7f", key="f_lon",
                        min_value=-180.0, max_value=180.0)
        st.button("Salvar terreiro", type="primary", width="stretch",
                  on_click=acao_salvar_terreiro, args=(bairros, lids))

    with dir_:
        with cartao():
            st.subheader("Terreiros cadastrados")
            st.dataframe(pd.DataFrame(
                [(t["id"], t["nome"], t["nacao"], t["bairro"],
                  t["lideranca"], t["membros"]) for t in lista_t],
                columns=["id", "Terreiro", "Nação", "Bairro", "Liderança",
                         "Membros"]), hide_index=True, width="stretch")

        with cartao():
            st.subheader("Pessoas do terreiro")
            nomes = {t["id"]: t["nome"] for t in lista_t}
            if not nomes:
                st.info("Nenhum terreiro cadastrado.")
                return
            if st.session_state.get("a_terreiro") not in nomes:
                st.session_state["a_terreiro"] = next(iter(nomes))
            id_sel = st.selectbox("Terreiro", list(nomes),
                                  format_func=nomes.get, key="a_terreiro")
            _, deste = banco.executar_consulta(
                "SELECT id_membro, nome, data_nascimento FROM "
                "membro_terreiro WHERE id_terreiro = ? ORDER BY nome",
                (id_sel,))
            st.dataframe(pd.DataFrame(deste, columns=["id", "Nome",
                                                      "Nascimento"]),
                         hide_index=True, width="stretch")

            _, outros = banco.executar_consulta(
                "SELECT m.id_membro, m.nome, t.nome FROM membro_terreiro m "
                "JOIN terreiro t ON t.id_terreiro = m.id_terreiro "
                "WHERE m.id_terreiro <> ? ORDER BY t.nome, m.nome",
                (id_sel,))
            rotulos = {i: f"{n}  ({t})" for i, n, t in outros}
            escolhidos = st.multiselect(
                "Atribuir pessoas de outros terreiros a este",
                list(rotulos), format_func=rotulos.get, key="a_pessoas")
            c1, c2 = st.columns(2)
            if c1.button("Atribuir selecionados", type="primary",
                         width="stretch", disabled=not escolhidos):
                banco.atribuir_membros(escolhidos, id_sel)
                avisar(f"{len(escolhidos)} pessoa(s) atribuída(s) a "
                       f"{nomes[id_sel]}.")
                limpar("a_pessoas")
                st.rerun()
            with c2.popover("Excluir este terreiro", width="stretch"):
                st.caption("Só é possível excluir terreiros sem membros.")
                if st.button("Confirmar exclusão"):
                    try:
                        banco.excluir_terreiro(id_sel)
                        avisar("Terreiro excluído.")
                        limpar("a_terreiro")
                    except Exception as erro:
                        avisar(str(erro), "warning")
                    st.rerun()

            st.markdown("**Adicionar pessoa nova a este terreiro**")
            c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
            c1.text_input("Nome", key="a_nova", label_visibility="collapsed",
                          placeholder="Nome da pessoa")

            def adicionar():
                nome = st.session_state.get("a_nova", "").strip()
                if not nome:
                    avisar("Digite o nome da pessoa.", "warning")
                    return
                banco.executar_comando(
                    "INSERT INTO membro_terreiro (nome, id_terreiro) "
                    "VALUES (?, ?)", (nome, st.session_state["a_terreiro"]))
                avisar(f"{nome} adicionado(a) ao terreiro.")
                limpar("a_nova")

            c2.button("Adicionar", width="stretch", on_click=adicionar)


def admin_membros():
    _, lista = banco.executar_consulta(
        "SELECT id_terreiro, nome FROM terreiro ORDER BY nome")
    nomes = dict(lista)
    esq, dir_ = st.columns([1, 2], gap="medium")
    with esq, cartao():
        st.subheader("Cadastro de membro")
        campos_pessoa("m_")
        st.selectbox("Terreiro *", list(nomes), format_func=nomes.get,
                     index=None, placeholder="Selecione...",
                     key="m_terreiro")

        def salvar():
            if st.session_state.get("m_terreiro") is None:
                avisar("Selecione o terreiro.", "warning")
                return
            acao_salvar_pessoa(st.session_state["m_terreiro"], "m_")

        st.button("Salvar membro", type="primary", width="stretch",
                  on_click=salvar)
    with dir_, cartao():
        st.subheader("Membros cadastrados")
        colunas, linhas = banco.executar_consulta("""
            SELECT m.id_membro AS id, m.nome AS membro,
                   m.data_nascimento AS nascimento, t.nome AS terreiro
            FROM membro_terreiro m
            JOIN terreiro t ON t.id_terreiro = m.id_terreiro
            ORDER BY m.id_membro DESC""")
        st.dataframe(pd.DataFrame(linhas, columns=colunas), hide_index=True,
                     width="stretch", height=480)


def admin_consultas():
    esq, dir_ = st.columns([1, 2], gap="medium")
    with esq, cartao():
        st.subheader("Consultas disponíveis")
        i = st.radio("Consulta", range(len(CONSULTAS)),
                     format_func=lambda k: CONSULTAS[k]["titulo"],
                     label_visibility="collapsed")
    with dir_, cartao():
        st.subheader("SQL da consulta")
        st.caption("Requisito: " + CONSULTAS[i]["requisito"])
        sql = st.text_area("SQL", CONSULTAS[i]["sql"].strip(), height=240,
                           key=f"sql_{i}", label_visibility="collapsed")
        if st.button("Executar consulta", type="primary"):
            try:
                colunas, linhas = banco.executar_consulta(sql)
                st.caption(f"{len(linhas)} registro(s) encontrado(s).")
                st.dataframe(pd.DataFrame(linhas, columns=colunas),
                             hide_index=True, width="stretch")
            except Exception as erro:
                st.error(f"Erro na consulta: {erro}")


def admin_sql_livre():
    with cartao():
        st.subheader("Digite um comando SQL e execute")
        sql = st.text_area("SQL", "SELECT * FROM terreiro;", height=180,
                           label_visibility="collapsed", key="sql_livre")
        if st.button("Executar", type="primary"):
            try:
                if sql.lower().lstrip().startswith("select"):
                    colunas, linhas = banco.executar_consulta(sql)
                    st.caption(f"{len(linhas)} registro(s) retornado(s).")
                    st.dataframe(pd.DataFrame(linhas, columns=colunas),
                                 hide_index=True, width="stretch")
                else:
                    afetadas = banco.executar_comando(sql)
                    st.success(f"Comando executado. {afetadas} linha(s) "
                               "afetada(s).")
            except Exception as erro:
                st.error(f"Erro no SQL: {erro}")


def pagina_gestor():
    barra_lateral("Conectado como **gestor(a)**.")
    with st.sidebar:
        modo = st.radio("Área", ["Painel", "Administração"],
                        key="g_modo")
    cabecalho("Gestor", "Gestor(a)")
    mostrar_aviso()

    if not banco.banco_existe():
        st.warning("O banco ainda não foi criado.")
        admin_banco()
        return

    if modo == "Painel":
        lista_t = painel.terreiros()
        lista_u = painel.unidades()
        a1, a2, a3 = st.tabs(["Visão Geral", "Mapa", "Proximidade"])
        with a1:
            gestor_visao_geral(lista_t, lista_u)
        with a2:
            gestor_mapa(lista_t, lista_u)
        with a3:
            gestor_proximidade(lista_t, lista_u)
    else:
        abas = st.tabs(["Banco de Dados", "Terreiros", "Membros",
                        "Consultas (DQL)", "SQL Livre"])
        with abas[0]:
            admin_banco()
        with abas[1]:
            admin_terreiros()
        with abas[2]:
            admin_membros()
        with abas[3]:
            admin_consultas()
        with abas[4]:
            admin_sql_livre()


# ======================================================================
# INICIO
# ======================================================================
def main():
    perfil = st.session_state.get("perfil")
    if perfil != "gestor":
        try:
            garantir_banco()
        except Exception as erro:
            st.error(f"Não foi possível preparar o banco: {erro}")
            return
    if perfil == "terreiro":
        pagina_terreiro()
    elif perfil == "gestor":
        pagina_gestor()
    else:
        tela_login()


main()
