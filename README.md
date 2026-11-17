<div align="center">

# 🌿 Mapeamento de Terreiros e Unidades de Saúde
### Recife / PE

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3.39+-003B57?logo=sqlite&logoColor=white)
![Tkinter](https://img.shields.io/badge/Interface-Tkinter-1a4971)
![Status](https://img.shields.io/badge/status-acad%C3%AAmico-success)

*Trabalho da disciplina de Banco de Dados — entregas SR1 + SR2*

</div>

---

## 📖 Sobre o projeto

Os **terreiros de religiões de matriz africana** são espaços de acolhimento e
cuidado para muitas comunidades da Região Metropolitana do Recife. Saber onde
eles ficam, quem são seus membros e qual unidade de saúde está mais próxima
ajuda a aproximar essas comunidades da rede pública de saúde.

Este trabalho propõe um **banco de dados que conecta esses dois mundos**:
ele registra os terreiros, suas lideranças e seus membros, e cruza essas
informações com as **unidades de saúde** (UBS, USF, policlínicas…) e os
**distritos sanitários** da cidade. Com isso é possível responder perguntas como:

- 📍 Quais unidades de saúde ficam no mesmo bairro de um terreiro?
- 🩺 Quais membros de terreiro já estão cadastrados em alguma unidade — e quais ainda não?
- 🏘️ Quais bairros têm terreiros mas nenhuma unidade de saúde (e vice-versa)?
- 📊 Quantos membros cada terreiro possui e qual a idade média deles?

Os endereços guardam **latitude e longitude**, deixando a base pronta para ser
usada em mapas e análises geográficas no futuro.

O sistema é composto por:

1. **Modelagem e scripts SQL** — criação das tabelas (DDL) e carga de dados (DML);
2. **12 consultas (DQL)** que cobrem todos os requisitos pedidos na disciplina;
3. **Uma aplicação desktop em Python + Tkinter** para criar o banco, rodar as
   consultas, cadastrar membros e executar SQL livre.

---

## 🗂️ Modelo de dados

O banco possui **10 tabelas** organizadas em três grupos: localização, saúde e terreiros.

```mermaid
erDiagram
    CIDADE ||--o{ BAIRRO : possui
    BAIRRO ||--o{ ENDERECO : contem
    ENDERECO ||--o{ TERREIRO : localiza
    ENDERECO ||--o{ UNIDADE_SAUDE : localiza
    DISTRITO_SANITARIO ||--o{ UNIDADE_SAUDE : agrupa
    SERVICO_SAUDE ||--o{ UNIDADE_SAUDE : classifica
    LIDERANCA_RELIGIOSA ||--o{ TERREIRO : lidera
    TERREIRO ||--o{ MEMBRO_TERREIRO : tem
    MEMBRO_TERREIRO ||--o{ MEMBRO_UNIDADE_SAUDE : "cadastrado em"
    UNIDADE_SAUDE ||--o{ MEMBRO_UNIDADE_SAUDE : atende
```

| Grupo | Tabela | Descrição |
|---|---|---|
| 📍 Localização | `cidade` | Municípios da RMR e interior de PE |
| | `bairro` | Bairros de cada cidade |
| | `endereco` | Logradouro, CEP, latitude e longitude |
| 🏥 Saúde | `distrito_sanitario` | Distritos sanitários e sua RPA |
| | `servico_saude` | Tipo de serviço (sigla única, ex.: UBS, USF) |
| | `unidade_saude` | Unidades com telefone, horário e distrito |
| 🌿 Terreiros | `lideranca_religiosa` | Pais e mães de santo responsáveis |
| | `terreiro` | Nome, religião, nação, regente e ano de fundação |
| | `membro_terreiro` | Membros vinculados a cada terreiro |
| 🔗 Ligação | `membro_unidade_saude` | Associação N:N entre membros e unidades de saúde |

**Regras de integridade** aplicadas: chaves primárias com `AUTOINCREMENT`,
chaves estrangeiras (com `PRAGMA foreign_keys = ON`), `UNIQUE` em telefones,
e-mails e siglas, e `CHECK` em `ano_fundacao > 1500` e `regiao_rpa > 0`.

---

## 🚀 Como executar

> **Pré-requisitos:** **Python 3** (Tkinter e SQLite já vêm incluídos) e as
> bibliotecas de gráficos e mapa:

```bash
pip install -r requirements.txt
python app.py
```

> Sem o `tkintermapview` o app continua funcionando: o mapa vira um gráfico
> simples de pontos (sem ruas). O mapa com ruas precisa de internet.

Na primeira execução, vá até a aba **1. Banco de Dados** e clique nos botões na ordem:

| Passo | Botão | O que acontece |
|:---:|---|---|
| 1 | `1) Criar Tabelas (DDL)` | Executa `scripts/criacao_tabelas.sql` |
| 2 | `2) Inserir Dados (DML)` | Executa `scripts/inserir_dados_tabelas.sql` |

O banco é salvo em `terreiros_saude.db`, na própria pasta do projeto.
O botão **Apagar Banco** remove todas as tabelas e dados. Depois disso, é só
repetir os passos 1 e 2 para montar o banco de novo.

> [!IMPORTANT]
> As consultas `b3` e `b4` usam `RIGHT OUTER JOIN` e `FULL OUTER JOIN`, suportados
> pelo SQLite apenas a partir da versão **3.39** (já incluída no Python 3.12+).
> Para conferir a sua versão:
>
> ```bash
> python -c "import sqlite3; print(sqlite3.sqlite_version)"
> ```

---

## 🖥️ Funcionalidades da aplicação

Ao abrir o app aparece uma **tela de login sem senha** com dois perfis.
O botão **Sair** no cabeçalho volta para essa tela.

### 🌿 Perfil Terreiro

O terreiro escolhe o próprio nome na lista e vê só os seus dados.

| Aba | Para que serve |
|---|---|
| **Meu Terreiro** | Ficha do terreiro (membros, quantos têm cadastro em unidade de saúde, unidade mais próxima, religião, regente, liderança), cadastro de pessoas, **vínculo de um membro a uma unidade de saúde** (as unidades aparecem da mais perto para a mais longe) e remoção de membros. Em vermelho, os membros sem cadastro em unidade |
| **Saúde perto de mim** | Lista das unidades de saúde com distância, telefone e horário, e mapa ligando o terreiro às unidades dentro do raio escolhido |

### 📊 Perfil Gestor

O gestor tem dois modos no cabeçalho: **Painel** e **Administração**.

**Administração**

| Aba | Para que serve |
|---|---|
| **Banco de Dados** | Executa os scripts DDL/DML e mostra quantos registros há em cada tabela |
| **Terreiros** | Cadastra terreiros (com liderança, endereço e local escolhido no mapa), exclui terreiros sem membros e **atribui pessoas** a um terreiro — movendo membros de outros terreiros ou adicionando pessoas novas |
| **Membros** | Formulário completo de cadastro de membro |
| **Consultas (DQL)** | Lista as consultas do trabalho; o SQL pode ser alterado antes de rodar |
| **SQL Livre** | Campo para digitar e executar qualquer comando SQL |

**Painel**

| Aba | Para que serve |
|---|---|
| **Visão Geral** | Indicadores (terreiros, membros, unidades, % de membros com cadastro em unidade, distância média) e gráficos: membros por terreiro com/sem cadastro, distância até a unidade mais próxima, faixa etária e membros vinculados por unidade. Passe o mouse nas barras para ver detalhes |
| **Mapa** | Mapa com terreiros (laranja) e unidades de saúde (azul). Ao escolher um terreiro, lista e liga no mapa as unidades dentro do raio escolhido |
| **Proximidade** | Tabela com as 2 unidades mais próximas de cada terreiro e quantas existem em até 2 km (em vermelho os terreiros sem nenhuma) |

---

## 🔎 Consultas implementadas (requisito DQL)

| Item | Recurso SQL | O que a consulta mostra |
|:---:|---|---|
| **a** | `WHERE` | Terreiros fundados a partir de 2000 |
| **b1** | `INNER JOIN` | Terreiros com sua liderança e endereço |
| **b2** | `LEFT OUTER JOIN` | Membros e suas unidades de saúde (inclui quem não tem cadastro) |
| **b3** | `RIGHT OUTER JOIN` | Todas as cidades e seus terreiros |
| **b4** | `FULL OUTER JOIN` | Bairros com terreiros e/ou unidades de saúde |
| **c** | `GROUP BY` | Quantidade de membros por terreiro |
| **d** | `HAVING` | Unidades que atendem mais de 1 membro |
| **e** | `ORDER BY` | Terreiros do mais antigo ao mais novo |
| **f** | Funções numéricas | `COUNT`, `MIN`, `MAX`, `AVG`, `ROUND`, `ABS`, `SUM` por nação |
| **g** | Funções de texto | `UPPER`, `LOWER`, `SUBSTR`, `LENGTH`, `REPLACE`, `TRIM`, `INSTR` |
| **h** | Funções de data | `STRFTIME`, `JULIANDAY`, `DATE` — idade dos membros |
| **i** | `UNION` | Mapa geral reunindo terreiros e unidades de saúde |

---

## 📁 Estrutura do projeto

```
Projeto-GTI-3/
├── app.py                          # Interface gráfica (Tkinter)
├── banco.py                        # Conexão com o SQLite, scripts e cadastro de terreiros
├── painel.py                       # Dados do Painel do Gestor (indicadores e distâncias)
├── tema.py                         # Cores e estilos da interface
├── requirements.txt                # matplotlib e tkintermapview
├── consultas.py                    # As 12 consultas DQL do trabalho
├── terreiros_saude.db              # Banco gerado pela aplicação
└── scripts/
    ├── criacao_tabelas.sql         # DDL — tabelas e constraints
    └── inserir_dados_tabelas.sql   # DML — carga de dados
```

---

<div align="center">

Feito com 💚 para a disciplina de Banco de Dados — CESAR School

</div>
