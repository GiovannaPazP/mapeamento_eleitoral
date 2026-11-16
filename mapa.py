
import pandas as pd
import folium
from html import escape
from math import sqrt
import branca.colormap as cm
import os

PASTA = "mapas"
os.makedirs(PASTA, exist_ok=True)

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

    mapa.save(f'mapas/mapa_{nome_arquivo}.html')

    print(os.path.join(PASTA, f'Mapa criado: mapa_{nome_arquivo}.html'))


# parte 3
df2 = pd.read_csv(
    ARQUIVO_CSV, 
    sep=";",
    encoding="cp1252",
    decimal=","
)

df2 = df2[df2["NR_TURNO"] == 2]

LULA = "LUIZ INÁCIO LULA DA SILVA"
FLAVIO = "FLAVIO NANTES BOLSONARO"

# votos por local e candidato
v2 = (
    df2[df2["NM_VOTAVEL"].isin([LULA, FLAVIO])]
    .pivot_table(
        index="NR_LOCAL_VOTACAO", 
        columns="NM_VOTAVEL",
        values="QT_VOTOS", 
        aggfunc="sum", 
        fill_value=0
    )
    .reset_index()
)

v2["validos"] = v2[LULA] + v2[FLAVIO]
v2["pct_lula"] = v2[LULA] / v2["validos"] * 100
v2["pct_flavio"] = v2[FLAVIO] / v2["validos"] * 100
v2["margem"] = v2["pct_lula"] - v2["pct_flavio"] # positivo == Lula, negativo==Flavio
v2["lider"] = v2["margem"].apply(lambda m: "Lula" if m > 0 else "Flávio Bolsonaro")

locais2 = totais_locais.merge(
    v2, 
    on="NR_LOCAL_VOTACAO", 
    how="inner"
)
print(len(locais2))

m_abs = float(locais2["margem"].abs().max())
cmap = cm.LinearColormap(
    colors=["#0066CC", "#f7f7f7", "#D71920"],
    index=[-m_abs, 0, m_abs],
    vmin=-m_abs, vmax=m_abs,
    caption="Margem no 2º turno (p.p.): azul = Flávio, vermelho = Lula",
)

# mapa base
mapa2 = folium.Map(
    location=centro, 
    zoom_start=12, 
    tiles=None
)

folium.TileLayer(
    tiles="https://tile.openstreetmap.de/{z}/{x}/{y}.png",
    attr="&copy; OpenStreetMap contributors",
    name="Mapa base",
).add_to(mapa2)

# camadas
g_ambos = folium.FeatureGroup(
    name="Os dois candidatos (margem)", 
    show=True
)
g_lula = folium.FeatureGroup(
    name="Dominância de Lula", 
    show=False
)
g_flavio = folium.FeatureGroup(
    name="Dominância de Flávio Bolsonaro", 
    show=False
)

maior_validos = locais2["validos"].max()

for _, r in locais2.iterrows():
    raio = 4 + 10 * sqrt(r["validos"] / maior_validos)
    tip = f"""
    <div style="font-family:Arial; font-size:12px">
      <b>{escape(str(r["nome"]))}</b><br>
      Líder: <b>{r["lider"]}</b><br>
      Lula: {r["pct_lula"]:.1f}% · Flávio: {r["pct_flavio"]:.1f}%<br>
      Vantagem: {abs(r["margem"]):.1f} p.p.
    </div>"""

    # camada 1: os dois juntos, cor pela margem
    folium.CircleMarker(
        location=[r["latitude"], r["longitude"]],
        radius=raio, color="#333", weight=0.8,
        fill=True, fill_color=cmap(r["margem"]), fill_opacity=0.85,
        tooltip=folium.Tooltip(tip, sticky=True),
    ).add_to(g_ambos)

    # camadas 2 e 3: só o candidato que lidera, intensidade = tamanho da vantagem
    lula_lidera = r["margem"] > 0
    cor = "#D71920" if lula_lidera else "#0066CC"
    folium.CircleMarker(
        location=[r["latitude"], r["longitude"]],
        radius=raio, color=cor, weight=1,
        fill=True, fill_color=cor,
        fill_opacity=0.35 + 0.55 * abs(r["margem"]) / m_abs,
        tooltip=folium.Tooltip(tip, sticky=True),
    ).add_to(g_lula if lula_lidera else g_flavio)

g_ambos.add_to(mapa2)
g_lula.add_to(mapa2)
g_flavio.add_to(mapa2)

cmap.add_to(mapa2)
folium.LayerControl(collapsed=False).add_to(mapa2)

mapa2.fit_bounds([[locais2["latitude"].min(), locais2["longitude"].min()],
                  [locais2["latitude"].max(), locais2["longitude"].max()]])
mapa2.save(os.path.join(PASTA, "mapa_2turno.html"))