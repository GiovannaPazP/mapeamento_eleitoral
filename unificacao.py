import pandas as pd
import os

ARQ = "sete_lagoas_eleitorado.csv"
CHAVES = ["NR_TURNO", "NR_ZONA", "NR_SECAO"]
COLS_LOCAL = ["NR_LATITUDE", "NR_LONGITUDE", "NM_LOCAL_VOTACAO", "DS_LOCAL_VOTACAO_ENDERECO"]


df = pd.read_csv(
    ARQ,
    sep=";",
    encoding="latin-1"
)

print(df.shape)
print(df.head(5))
print(df.columns.tolist())


print("Valores duplicados (CHAVES): ", df.duplicated(CHAVES + ["NM_VOTAVEL"]).sum())

# padroniza coordenadas
for c in ["NR_LATITUDE", "NR_LONGITUDE"]:
    df[c] = pd.to_numeric(df[c].astype(str).str.replace(",", "."), errors="coerce")

print(df[["NR_LATITUDE", "NR_LONGITUDE"]].describe())
print("\nLocais unicos: ", df[["NR_LATITUDE", "NR_LONGITUDE"]].drop_duplicates().shape[0])


def pivotar(df, turno):
    d = df[df["NR_TURNO"] == turno]

    chaves_secao = [c for c in CHAVES if c != "NR_TURNO"] #turno é constante

    largo = d.pivot(
        index= chaves_secao + COLS_LOCAL,
        columns="NM_VOTAVEL",
        values="QT_VOTOS",
    ).fillna(0).reset_index()

    largo.columns.name = None  # remove o nome "NM_VOTAVEL" do eixo das colunas
    return largo


df_primeiro = pivotar(df, 1)
df_segundo = pivotar(df, 2)

print("\n\n tamanhos 1º turno e 2º turno (respectivamente):")
print(df_primeiro.shape, df_segundo.shape)
print("\nLista de colunas 1º turno", df_primeiro.columns.tolist())
print("\nLista de colunas 2º turno", df_segundo.columns.tolist())

# separando os votos em branco/anulados e os candidatos
nao_cand = ["VOTO BRANCO", "VOTO NULO"]
cands1 = [c for c in df_primeiro.columns if c in df.loc[df["NR_TURNO"]==1, "NM_VOTAVEL"].unique() and c not in nao_cand]
cands2 = [c for c in df_segundo.columns if c in df.loc[df["NR_TURNO"]==2, "NM_VOTAVEL"].unique() and c not in nao_cand]

print("\nQuantidade de candidatos no 1º turno:", len(cands1))
print("\nQuantidade de candidatos no 2º turno:", len(cands2))


principais = [
    "FLAVIO NANTES BOLSONARO",
    "LUIZ INÁCIO LULA DA SILVA",
    "AUGUSTO JORGE CURY",
    "RONALDO RAMOS CAIADO",
    "RENAN ANTONIO FERREIRA DOS SANTOS",
]

def agregar_locais(secoes, cands):
    colunas_soma = cands + nao_cand
    return secoes.groupby(["NR_LATITUDE", "NR_LONGITUDE"], as_index=False).agg(
        **{c: (c, "sum") for c in colunas_soma},
        NM_LOCAL_VOTACAO=("NM_LOCAL_VOTACAO", "first"),
        DS_LOCAL_VOTACAO_ENDERECO=("DS_LOCAL_VOTACAO_ENDERECO", "first"),
        n_zonas=("NR_ZONA", "nunique"),   # quantas zonas votam neste local
        n_secoes=("NR_SECAO", "count"),   # quantas seções votam neste local
    )


locais1 = agregar_locais(df_primeiro, cands1)
locais2 = agregar_locais(df_segundo, cands2)

print("Locais:", locais1.shape[0], locais2.shape[0])          # esperado: 78 e 78
print("Seções:", locais1["n_secoes"].sum(), locais2["n_secoes"].sum())  # esperado: 535 e 535

# primeiro turno
locais1["validos"] = locais1[cands1].sum(axis=1)
locais1["lider"] = locais1[cands1].idxmax(axis=1)
locais1["outros"] = locais1["validos"] - locais1[principais].sum(axis=1)
for c in principais:
    locais1[f"pct_{c}"] = locais1[c] / locais1["validos"] * 100

# segundo turno
locais2["validos"] = locais2[cands2].sum(axis=1)
locais2["lider"] = locais2[cands2].idxmax(axis=1)
for c in cands2:
    locais2[f"pct_{c}"] = locais2[c] / locais2["validos"] * 100


# filtrando para os principais cands
info = ["NR_LATITUDE", "NR_LONGITUDE", "NM_LOCAL_VOTACAO", "DS_LOCAL_VOTACAO_ENDERECO", "n_zonas", "n_secoes"]
locais1 = locais1[info + principais + ["outros", "validos", "lider"] + [f"pct_{c}" for c in principais]].copy()
locais2 = locais2[info + cands2 + nao_cand + ["validos", "lider"] + [f"pct_{c}" for c in cands2]].copy()

# checagem: deve ser 0
print((locais1[principais].sum(axis=1) + locais1["outros"] - locais1["validos"]).abs().max())

# salvando
os.makedirs("dados_processados", exist_ok=True)

locais1.to_csv(
    "dados_processados/locais_1turno.csv", 
    sep=";",
    index=False, 
    encoding="utf-8"
)

locais2.to_csv(
    "dados_processados/locais_2turno.csv", 
    sep=";",
    index=False, 
    encoding="utf-8"
)
