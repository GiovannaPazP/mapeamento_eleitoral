
import pandas as pd
import folium
from html import escape
from math import sqrt


ARQUIVO_CSV = 'sete_lagoas_eleitorado.csv'

df = pd.read_csv(
    ARQUIVO_CSV,
    sep=';',
    encoding='cp1252',
    decimal=','
)

df = df[df['NR_TURNO'] == 1]

totais_candidatos = (
    df.groupby('NM_VOTAVEL')['QT_VOTOS']
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
    df.groupby('NR_LOCAL_VOTACAO')
    .agg(
        total_votos=('QT_VOTOS', 'sum'),
        latitude=('NR_LATITUDE', 'mean'),
        longitude=('NR_LONGITUDE', 'mean'),
        nome=('NM_LOCAL_VOTACAO', 'first'),
        endereco=('DS_LOCAL_VOTACAO_ENDERECO', 'first')
    )
    .reset_index()
)


votos_por_candidato = (
    df[df['NM_VOTAVEL'].isin(candidatos)]
    .groupby(['NR_LOCAL_VOTACAO', 'NM_VOTAVEL'])['QT_VOTOS']
    .sum()
    .reset_index()
)


cores_candidatos = {
    'BOLSONARO': '#0066CC',
    'LULA': '#D71920',
    'CURY': '#FFD700',
    'CAIADO': '#00843D',
    'SANTOS': '#800080'
}


maior_total = totais_locais['total_votos'].max()

centro = [
    totais_locais['latitude'].mean(),
    totais_locais['longitude'].mean()
]

maior_quantidade_votos = votos_por_candidato['QT_VOTOS'].max()

for candidato in candidatos:

    votos = votos_por_candidato[
        votos_por_candidato['NM_VOTAVEL'] == candidato
    ]

    locais = totais_locais.merge(
        votos[['NR_LOCAL_VOTACAO', 'QT_VOTOS']],
        on='NR_LOCAL_VOTACAO',
        how='left'
    )

    # Define a cor do candidato com base no dicionário de cores
    cor = next(
        (cor for nome, cor in cores_candidatos.items() if nome in candidato.upper()),
        '#808080'
    )

    mapa = folium.Map(
        location=centro,
        zoom_start=12,
        tiles='https://tile.openstreetmap.de/{z}/{x}/{y}.png',
        attr='&copy; OpenStreetMap contributors'
    )

    for _, row in locais.iterrows():

        raio = 4 + 10 * sqrt(
            row['QT_VOTOS'] / maior_quantidade_votos
        )

        nome = escape(str(row['nome']))
        endereco = escape(str(row['endereco']))

        popup_html = f"""
        <div style="width: 250px">
            <h4>{nome}</h4>
            <p><b>Endereço:</b> {endereco}</p>
            <hr>
            <p><b>Candidato:</b> {escape(candidato)}</p>
            <p><b>Votos recebidos:</b> {row['QT_VOTOS']:,.0f}</p>
        </div>
        """

        folium.CircleMarker(
            location=[
                row['latitude'],
                row['longitude']
            ],
            radius=raio,
            color=cor,
            weight=1,
            fill=True,
            fill_color=cor,
            fill_opacity=0.75,
            popup=folium.Popup(
                popup_html,
                max_width=300
            ),
            tooltip=f'{nome} — {row["QT_VOTOS"]:,.0f} votos'
        ).add_to(mapa)

    mapa.fit_bounds([
        [
            totais_locais['latitude'].min(),
            totais_locais['longitude'].min()
        ],
        [
            totais_locais['latitude'].max(),
            totais_locais['longitude'].max()
        ]
    ])

    nome_arquivo = (
        candidato.lower()
        .replace(' ', '_')
        .replace('/', '_')
    )

    mapa.save(f'mapa_{nome_arquivo}.html')

    print(f'Mapa criado: mapa_{nome_arquivo}.html')
