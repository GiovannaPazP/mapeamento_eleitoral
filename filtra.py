import pandas as pd

ARQ_BRUTO = "votacao_secao_2026_BR/votacao_secao_2026_BR.csv"
MUNICIPIO = "SETE LAGOAS"
ARQ_FONTE = "sete_lagoas.csv"
ARQ_ELEITORADO = "eleitorado_local_votacao_MG_2026/eleitorado_local_votacao_2026_MG.csv"



# lendo o dataframe e filtrando para o municipio de interesse
primeiro = True
total = 0

for chunk in pd.read_csv(
    ARQ_BRUTO,
    sep=";",
    encoding="latin-1",
    chunksize=100_000
):
    filtrado = chunk[
        chunk["NM_MUNICIPIO"].str.strip().str.upper() == MUNICIPIO
    ]

    if not filtrado.empty:
        filtrado.to_csv(
            "sete_lagoas.csv",
            sep=";",
            encoding="latin-1",
            index=False,
            mode="w" if primeiro else "a",
            header=primeiro
        )

        primeiro = False
        total += len(filtrado)

print(f"Total de registros: {total}")


# lendo o arquivo do municipio de interesse
df = pd.read_csv(
    ARQ_FONTE, 
    sep=";", 
    encoding="latin-1"
)

# conferindo 
print("Colunas")
print(df.columns.tolist())
print()

print("Total de registros: ", len(df))
print("Zonas eleitorais: ", df["NR_ZONA"].nunique())
print("Seções eleitorais: ", df["NR_SECAO"].nunique())

print(
    "Combinações zona/seção:",
    df[["NR_ZONA", "NR_SECAO"]].drop_duplicates().shape[0]
)


# eleitorado por local de votação

#lendo arquivo do eleitorado
df_eleitorado = pd.read_csv(
    ARQ_ELEITORADO,
    sep=";", 
    encoding="latin-1"
)

#filtrando para o municipio de interesse
df_eleitorado = df_eleitorado[
    df_eleitorado["NM_MUNICIPIO"].str.strip().str.upper() == MUNICIPIO
].copy()

# conferindo
print("\n\nDATAFRAME ELEITORADO")
print("shape:", df_eleitorado.shape)
print("Municipios: ", df_eleitorado["NM_MUNICIPIO"].unique())
print("Colunas:\n", df_eleitorado.columns.tolist())

# iniciando a junção
print("\n\nIniciando a junção")

chaves = ["NR_ZONA", "NR_SECAO", "NR_TURNO"]
print("Chaves para a junção: ", chaves)

print("Combinações únicas:",
      df_eleitorado[chaves].drop_duplicates().shape[0])

print("Duplicatas:",
      df_eleitorado.duplicated(subset=chaves).sum())

# atualizando o df para apenas as colunas de interesse
df_eleitorado = df_eleitorado[
    chaves + ["NR_LATITUDE", "NR_LONGITUDE"]
].copy()

df_final = df.merge(
    df_eleitorado,
    on=chaves,
    how="left",
    validate="many_to_one"
)

print("Registros antes:", len(df))
print("Registros depois:", len(df_final))

print("Combinações sem latitude:", df_final["NR_LATITUDE"].isna().sum())
print("Combinações sem longitude:", df_final["NR_LONGITUDE"].isna().sum())

df_final.to_csv(
    "sete_lagoas_eleitorado.csv",
    sep=";",
    encoding="latin-1",
    index=False
)