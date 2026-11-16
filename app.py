import streamlit as st
import pandas as pd

def exibir_mapa(caminho, altura=550):

    with open(caminho, 'r', encoding='utf-8') as arquivo:
        html = arquivo.read()

    st.iframe(
        html,
        height=altura,
    )

st.set_page_config(
    page_title="Mapeamento Eleitoral e Visualização Geospacial | Sete Lagoas",
    layout="wide"
)

ARQUIVO_CSV = 'sete_lagoas_eleitorado.csv'

cores_candidatos = {
    'BOLSONARO': '#0066CC',
    'LULA': '#D71920',
    'CURY': '#FFD700',
    'CAIADO': '#00843D',
    'SANTOS': '#800080'
}

@st.cache_data
def carregar_dados():

    df = pd.read_csv(
        ARQUIVO_CSV,
        sep=';',
        encoding='cp1252',
        decimal=','
    )

    return df

df = carregar_dados()

st.title("Mapeamento Eleitoral e Visualização Geospacial")

st.markdown("Giovanna Aparecida da Paz e Leonardo Torres Gonçalves e Silva")

st.markdown("### Selecione o turno")

turnos = sorted(
    df['NR_TURNO'].unique()
)

turno = st.radio(
    "Turno",
    turnos,
    format_func=lambda x: f"{x}º Turno",
    horizontal=True,
    label_visibility="collapsed"
)

df_turno = df[df['NR_TURNO'] == turno]

totais_candidatos = (
    df_turno.groupby('NM_VOTAVEL')['QT_VOTOS']
    .sum()
    .sort_values(ascending=False)
)

totais_candidatos = totais_candidatos[
    ~totais_candidatos.index.str.contains(
        r'BRANCO|NULO',
        case=False,
        na=False
    )
]

candidatos = totais_candidatos.head(5).index.tolist()


totais_locais = (
    df_turno.groupby('NR_LOCAL_VOTACAO')
    .agg(
        total_votos=('QT_VOTOS', 'sum'),
        latitude=('NR_LATITUDE', 'mean'),
        longitude=('NR_LONGITUDE', 'mean'),
        nome=('NM_LOCAL_VOTACAO', 'first'),
        endereco=('DS_LOCAL_VOTACAO_ENDERECO', 'first')
    )
    .reset_index()
)

st.markdown("### Visão geral")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Votos registrados",
        f"{totais_locais['total_votos'].sum():,.0f}"
    )

with col2:
    st.metric(
        "Locais de votação",
        f"{totais_locais['NR_LOCAL_VOTACAO'].nunique()}"
    )

with col3:
    st.metric(
        "Candidatos analisados",
        len(candidatos)
    )


st.divider()

st.markdown("## Mapas")

for i, candidato in enumerate(candidatos):

    votos_candidato = totais_candidatos[candidato]

    # Define a cor do candidato com base no dicionário de cores
    cor = next(
        (cor for nome, cor in cores_candidatos.items() if nome in candidato.upper()),
        '#808080'
    )

    with st.container(border=True):

        col_info, col_total = st.columns([3, 1]) 

        with col_info:
            st.markdown(f"### {candidato}")

        with col_total:
            st.metric("Total de votos", f"{votos_candidato:,.0f}")

        exibir_mapa(f"mapas/mapa_{candidato.lower().replace(' ', '_')}.html")

if turno == 2:
    with st.container(border=True):
        st.markdown(f"### Mapa de comparação do segundo turno")

        exibir_mapa("mapas/mapa_2turno.html")