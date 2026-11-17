import zipfile
import numpy as np
import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, Input, Output, dash_table

# ==========================================
# 1. CARREGAMENTO DOS DADOS
# ==========================================
def carregar_dados():
    caminho_zip = 'tennis+major+tournament+match+statistics.zip'
    lista_dfs = []

    with zipfile.ZipFile(caminho_zip, 'r') as z:
        for ficheiro in z.namelist():
            if ficheiro.endswith('.csv'):
                partes = ficheiro.split('/')[-1].replace('.csv', '').split('-')
                torneio = partes[0]
                sexo = 'Masculino' if partes[1].lower() == 'men' else 'Feminino'
                
                df_temp = pd.read_csv(z.open(ficheiro))
                df_temp.columns = [col.replace(' ', '') for col in df_temp.columns]
                df_temp['Torneio'] = torneio
                df_temp['Sexo'] = sexo
                lista_dfs.append(df_temp)

    df_total = pd.concat(lista_dfs, ignore_index=True)

    mapa_rondas = {
        1: '1ª Ronda (R128)',
        2: '2ª Ronda (R64)',
        3: '3ª Ronda (R32)',
        4: 'Oitavos de Final (R16)',
        5: 'Quartos de Final (QF)',
        6: 'Meias-Finais (SF)',
        7: 'Final (F)'
    }
    df_total['Nome_Ronda'] = df_total['Round'].map(mapa_rondas).fillna(df_total['Round'].astype(str))
    df_total['Vencedor'] = np.where(df_total['Result'] == 1, df_total['Player1'], df_total['Player2'])
    
    if 'ACE.1' in df_total.columns and 'ACE.2' in df_total.columns:
        df_total['Total_Aces'] = df_total['ACE.1'].fillna(0) + df_total['ACE.2'].fillna(0)
    else:
        df_total['Total_Aces'] = 0

    return df_total

df_total = carregar_dados()

# ==========================================
# 2. INICIALIZAÇÃO DO DASH E GUNICORN
# ==========================================
app = dash.Dash(__name__)
server = app.server  # Necessário para: gunicorn app:server

torneios_disponiveis = list(df_total['Torneio'].unique())
sexos_disponiveis = list(df_total['Sexo'].unique())

# ==========================================
# 3. LAYOUT DO DASHBOARD
# ==========================================
app.layout = html.Div([
    html.H1("Dashboard Interativo de Estatísticas de Ténis (Grand Slams)", style={'textAlign': 'center'}),
    html.Hr(),

    # Filtros
    html.Div([
        html.Div([
            html.Label("Selecionar Torneio(s):"),
            dcc.Dropdown(
                id='filtro-torneio',
                options=[{'label': t, 'value': t} for t in torneios_disponiveis],
                value=torneios_disponiveis,
                multi=True
            )
        ], style={'width': '48%', 'display': 'inline-block', 'padding': '10px'}),

        html.Div([
            html.Label("Selecionar Género:"),
            dcc.Dropdown(
                id='filtro-sexo',
                options=[{'label': s, 'value': s} for s in sexos_disponiveis],
                value=sexos_disponiveis,
                multi=True
            )
        ], style={'width': '48%', 'display': 'inline-block', 'padding': '10px'})
    ]),

    html.Hr(),

    # Métricas Principais
    html.Div([
        html.Div([
            html.H4("Total de Partidas Filtradas"),
            html.H2(id="metrica-partidas")
        ], style={'width': '48%', 'display': 'inline-block', 'textAlign': 'center', 'border': '1px solid #ddd', 'padding': '10px'}),

        html.Div([
            html.H4("Jogadores Envolvidos"),
            html.H2(id="metrica-jogadores")
        ], style={'width': '48%', 'display': 'inline-block', 'textAlign': 'center', 'border': '1px solid #ddd', 'padding': '10px'})
    ]),

    html.Hr(),

    # Gráficos
    html.H3("Visualizações Gráficas"),
    html.Div([
        html.Div(dcc.Graph(id="grafico-partidas"), style={'width': '50%', 'display': 'inline-block'}),
        html.Div(dcc.Graph(id="grafico-aces"), style={'width': '50%', 'display': 'inline-block'})
    ]),

    html.Hr(),

    # Top 10 Vencedores
    html.H3("Top 10 Tenistas com Mais Vitórias"),
    html.Div(id="tabela-top10"),

    html.Hr(),

    # Amostra de Partidas
    html.H3("Amostra de Partidas Filtradas"),
    html.Div(id="tabela-partidas")

], style={'fontFamily': 'sans-serif', 'padding': '20px', 'maxWidth': '1200px', 'margin': 'auto'})

# ==========================================
# 4. CALLBACKS (INTERATIVIDADE)
# ==========================================
@app.callback(
    [Output("metrica-partidas", "children"),
     Output("metrica-jogadores", "children"),
     Output("grafico-partidas", "figure"),
     Output("grafico-aces", "figure"),
     Output("tabela-top10", "children"),
     Output("tabela-partidas", "children")],
    [Input("filtro-torneio", "value"),
     Input("filtro-sexo", "value")]
)
def atualizar_dashboard(torneios_sel, sexos_sel):
    if not torneios_sel or not sexos_sel:
        return "0", "0", {}, {}, html.P("Sem dados."), html.P("Sem dados.")

    df_filtrado = df_total[
        (df_total['Torneio'].isin(torneios_sel)) & 
        (df_total['Sexo'].isin(sexos_sel))
    ]

    # 1. Métricas
    total_partidas = str(len(df_filtrado))
    jogadores_unicos = str(len(pd.concat([df_filtrado['Player1'], df_filtrado['Player2']]).unique()))

    # 2. Gráfico Contagem de Partidas
    contagem = df_filtrado.groupby(['Torneio', 'Sexo']).size().reset_index(name='Partidas')
    fig_partidas = px.bar(contagem, x='Torneio', y='Partidas', color='Sexo', barmode='group',
                          title="Número de Partidas por Torneio e Género")

    # 3. Gráfico Média de Aces
    media_aces = df_filtrado.groupby(['Torneio', 'Sexo'])['Total_Aces'].mean().reset_index()
    fig_aces = px.bar(media_aces, x='Torneio', y='Total_Aces', color='Sexo', barmode='group',
                      title="Média de Aces por Partida")

    # 4. Top 10 Vencedores
    top_vencedores = df_filtrado.groupby(['Vencedor', 'Sexo']).size().reset_index(name='Vitorias')
    top_10 = top_vencedores.sort_values(by='Vitorias', ascending=False).head(10)
    tabela_10 = dash_table.DataTable(
        data=top_10.to_dict('records'),
        columns=[{"name": i, "id": i} for i in top_10.columns],
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '8px'}
    )

    # 5. Amostra de Partidas
    cols_amostra = ['Torneio', 'Sexo', 'Nome_Ronda', 'Player1', 'Player2', 'Vencedor', 'FNL1', 'FNL2']
    cols_existentes = [c for c in cols_amostra if c in df_filtrado.columns]
    df_amostra = df_filtrado[cols_existentes].head(50)
    tabela_amostra = dash_table.DataTable(
        data=df_amostra.to_dict('records'),
        columns=[{"name": i, "id": i} for i in df_amostra.columns],
        page_size=10,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '8px'}
    )

    return total_partidas, jogadores_unicos, fig_partidas, fig_aces, tabela_10, tabela_amostra

if __name__ == '__main__':
    app.run(debug=True)
