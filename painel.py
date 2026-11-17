"""
Dados do Painel do Gestor: indicadores, localizacao e proximidade entre
terreiros e unidades de saude.
"""

import math
from datetime import date, datetime

import banco


def distancia_km(lat1, lon1, lat2, lon2):
    """Distancia em linha reta entre dois pontos (formula de Haversine)."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = (math.sin(dp / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2)
    return 2 * r * math.asin(math.sqrt(a))


def terreiros():
    """Lista de dicts com os terreiros, coordenadas e qtd. de membros."""
    _, linhas = banco.executar_consulta("""
        SELECT t.id_terreiro, t.nome, t.nacao, t.religiao, b.nome,
               e.logradouro, e.latitude, e.longitude, l.nome,
               (SELECT COUNT(*) FROM membro_terreiro m
                 WHERE m.id_terreiro = t.id_terreiro)
        FROM terreiro t
        JOIN endereco e ON e.id_endereco = t.id_endereco
        JOIN bairro   b ON b.id_bairro   = e.id_bairro
        JOIN lideranca_religiosa l ON l.id_lideranca = t.id_lideranca
        ORDER BY t.nome
    """)
    chaves = ("id", "nome", "nacao", "religiao", "bairro", "logradouro",
              "lat", "lon", "lideranca", "membros")
    return [dict(zip(chaves, l)) for l in linhas]


def unidades():
    """Lista de dicts com as unidades de saude e coordenadas."""
    _, linhas = banco.executar_consulta("""
        SELECT u.id_unidade, u.nome, s.sigla, b.nome, e.logradouro,
               e.latitude, e.longitude, u.fone, u.horario_atendimento,
               (SELECT COUNT(*) FROM membro_unidade_saude mu
                 WHERE mu.id_unidade = u.id_unidade)
        FROM unidade_saude u
        JOIN endereco e      ON e.id_endereco = u.id_endereco
        JOIN bairro b        ON b.id_bairro   = e.id_bairro
        JOIN servico_saude s ON s.id_servico  = u.id_servico
        ORDER BY u.nome
    """)
    chaves = ("id", "nome", "sigla", "bairro", "logradouro", "lat", "lon",
              "fone", "horario", "atendidos")
    return [dict(zip(chaves, l)) for l in linhas]


def proximas(terreiro, lista_unidades, k=None):
    """Unidades ordenadas da mais perto para a mais longe do terreiro."""
    resultado = []
    for u in lista_unidades:
        d = distancia_km(terreiro["lat"], terreiro["lon"], u["lat"], u["lon"])
        resultado.append((d, u))
    resultado.sort(key=lambda par: par[0])
    return resultado[:k] if k else resultado


def cobertura_por_terreiro():
    """[(terreiro, total_membros, membros_com_cadastro_em_unidade)]"""
    _, linhas = banco.executar_consulta("""
        SELECT t.nome,
               COUNT(m.id_membro),
               COUNT(DISTINCT CASE WHEN mu.id_membro IS NOT NULL
                                   THEN m.id_membro END)
        FROM terreiro t
        LEFT JOIN membro_terreiro m       ON m.id_terreiro = t.id_terreiro
        LEFT JOIN membro_unidade_saude mu ON mu.id_membro  = m.id_membro
        GROUP BY t.id_terreiro
        ORDER BY COUNT(m.id_membro) DESC, t.nome
    """)
    return linhas


def _idade(texto):
    for formato in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            nasc = datetime.strptime(texto.strip(), formato).date()
            break
        except (ValueError, AttributeError):
            continue
    else:
        return None
    hoje = date.today()
    return hoje.year - nasc.year - ((hoje.month, hoje.day)
                                    < (nasc.month, nasc.day))


FAIXAS = [("0-17", 0, 17), ("18-29", 18, 29), ("30-44", 30, 44),
          ("45-59", 45, 59), ("60+", 60, 200)]


def faixas_etarias():
    """[(faixa, quantidade)] + quantidade sem data valida."""
    _, linhas = banco.executar_consulta(
        "SELECT data_nascimento FROM membro_terreiro")
    contagem = {f[0]: 0 for f in FAIXAS}
    sem_data = 0
    for (texto,) in linhas:
        idade = _idade(texto) if texto else None
        if idade is None:
            sem_data += 1
            continue
        for nome, ini, fim in FAIXAS:
            if ini <= idade <= fim:
                contagem[nome] += 1
                break
    return list(contagem.items()), sem_data


def unidades_por_servico():
    _, linhas = banco.executar_consulta("""
        SELECT s.sigla, COUNT(u.id_unidade)
        FROM servico_saude s
        LEFT JOIN unidade_saude u ON u.id_servico = s.id_servico
        GROUP BY s.id_servico
        ORDER BY COUNT(u.id_unidade) DESC
    """)
    return linhas


def indicadores():
    """Numeros principais exibidos nos cartoes do painel."""
    lista_t = terreiros()
    lista_u = unidades()
    _, [(membros,)] = banco.executar_consulta(
        "SELECT COUNT(*) FROM membro_terreiro")
    _, [(com_cadastro,)] = banco.executar_consulta(
        "SELECT COUNT(DISTINCT id_membro) FROM membro_unidade_saude")
    distancias = [proximas(t, lista_u, 1)[0][0]
                  for t in lista_t if lista_u]
    return {
        "terreiros": len(lista_t),
        "membros": membros,
        "unidades": len(lista_u),
        "cobertura": (100 * com_cadastro / membros) if membros else 0,
        "dist_media": (sum(distancias) / len(distancias))
                      if distancias else None,
    }
