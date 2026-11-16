import zipfile
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

# Configuração da página do Streamlit
st.set_page_config(page_title="Dashboard de Ténis - Grand Slams", layout="wide")

st.title(" Dashboard Interativo de Estatísticas de Ténis (Grand Slams)")
st.markdown("Explore os dados dos torneios de Grand Slam de forma interativa.")

# 1. Carregamento dos dados (com cache para ser mais rápido)
@st.cache_data
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

    # Mapeia o número da ronda para texto legível
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
    
    return df_total

df_total = carregar_dados()

# 2. Barra Lateral (Sidebar) para Filtros Interativos
st.sidebar.header("Filtros do Dashboard")

torneios_disponiveis = df_total['Torneio'].unique()
torneio_selecionado = st.sidebar.multiselect("Selecionar Torneio(s):", torneios_disponiveis, default=torneios_disponiveis)

sexos_disponiveis = df_total['Sexo'].unique()
sexo_selecionado = st.sidebar.multiselect("Selecionar Género:", sexos_disponiveis, default=sexos_disponiveis)

# Aplicar filtros ao DataFrame
df_filtrado = df_total[
    (df_total['Torneio'].isin(torneio_selecionado)) & 
    (df_total['Sexo'].isin(sexo_selecionado))
]

# 3. Métricas Principais no Topo
col1, col2 = st.columns(2)
with col1:
    st.metric("Total de Partidas Filtradas", len(df_filtrado))
with col2:
    st.metric("Jogadores Únicos Envolvidos", 
              len(pd.concat([df_filtrado['Player1'], df_filtrado['Player2']]).unique()))

st.markdown("---")

# 4. Tabela Interativa de Partidas
st.subheader(" Amostra de Partidas Filtradas")
st.dataframe(df_filtrado[['Torneio', 'Sexo', 'Nome_Ronda', 'Player1', 'Player2', 'Vencedor', 'FNL1', 'FNL2']].head(50))

# 5. Gráficos Interativos
st.markdown("---")
st.subheader(" Visualizações Gráficas")

col_g1, col_g2 = st.columns(2)

with col_g1:
    st.markdown("**Número de Partidas por Torneio e Género**")
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.countplot(data=df_filtrado, x='Torneio', hue='Sexo', ax=ax, palette='Set2')
    ax.set_ylabel('Nº de Partidas')
    st.pyplot(fig)

with col_g2:
    st.markdown("**Média de Aces por Partida**")
    if 'ACE.1' in df_filtrado.columns and 'ACE.2' in df_filtrado.columns:
        df_filtrado['Total_Aces'] = df_filtrado['ACE.1'].fillna(0) + df_filtrado['ACE.2'].fillna(0)
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.barplot(data=df_filtrado, x='Torneio', y='Total_Aces', hue='Sexo', ax=ax, palette='Set1', errorbar=None)
        ax.set_ylabel('Média de Aces')
        st.pyplot(fig)

# 6. Top 10 Tenistas com Mais Vitórias
st.markdown("---")
st.subheader(" Top Tenistas com Mais Vitórias (Com base nos filtros)")
top_vencedores = df_filtrado.groupby(['Vencedor', 'Sexo']).size().reset_index(name='Vitorias')
top_10 = top_vencedores.sort_values(by='Vitorias', ascending=False).head(10)
st.table(top_10)
