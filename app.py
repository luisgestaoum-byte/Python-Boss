import zipfile
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
#from google.colab import drive

# 1. Ligar ao Google Drive e definir o caminho do ficheiro
#drive.mount('/content/drive')
caminho_zip = 'tennis+major+tournament+match+statistics.zip'
# 2. Extração e unificação dos 8 ficheiros CSV
lista_dfs = []

with zipfile.ZipFile(caminho_zip, 'r') as z:
    for ficheiro in z.namelist():
        if ficheiro.endswith('.csv'):
            # Extrai o Torneio e o Sexo a partir do nome (ex: 'AusOpen-men-2013.csv')
            partes = ficheiro.split('/')[-1].replace('.csv', '').split('-')
            torneio = partes[0]
            sexo = 'Masculino' if partes[1].lower() == 'men' else 'Feminino'
            
            df_temp = pd.read_csv(z.open(ficheiro))
            # Normaliza os nomes das colunas ANTES de juntar (evita o erro de labels duplicadas!)
            df_temp.columns = [col.replace(' ', '') for col in df_temp.columns]
            df_temp['Torneio'] = torneio
            df_temp['Sexo'] = sexo
            lista_dfs.append(df_temp)

# Junta todos os torneios num único DataFrame
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

# Identifica o vencedor de cada partida (substitui o .apply que dava erro)
df_total['Vencedor'] = np.where(df_total['Result'] == 1, df_total['Player1'], df_total['Player2'])

print(f"\nTotal de partidas carregadas: {len(df_total)}")
display(df_total[['Torneio', 'Sexo', 'Nome_Ronda', 'Player1', 'Player2', 'Vencedor', 'FNL1', 'FNL2']].head(10))

# 3. Tabela: Total de Jogos por Torneio, Sexo e Ronda
print("\n=== TOTAL DE PARTIDAS POR TORNEIO, SEXO E RONDA ===")
resumo_rondas = pd.pivot_table(
    df_total, 
    index=['Round', 'Nome_Ronda'], 
    columns=['Torneio', 'Sexo'], 
    values='Vencedor', 
    aggfunc='count', 
    fill_value=0
)
display(resumo_rondas)

# 4. Tabela: Campeões e Finalistas de cada Torneio
print("\n=== FINAIS E CAMPEÕES POR TORNEIO E SEXO ===")
finais = df_total[df_total['Round'] == 7][['Torneio', 'Sexo', 'Player1', 'Player2', 'Vencedor', 'FNL1', 'FNL2']]
display(finais)

# 5. Visualizações Gráficas
sns.set_theme(style="whitegrid")
fig, axes = plt.subplots(1, 2, figsize=(15, 5))

# Gráfico 1: Total de partidas registadas por Torneio e Sexo
sns.countplot(data=df_total, x='Torneio', hue='Sexo', ax=axes[0], palette='Set2')
axes[0].set_title('Número de Partidas Registadas por Torneio e Sexo')
axes[0].set_xlabel('Torneio')
axes[0].set_ylabel('Nº de Partidas')

# Gráfico 2: Média de Aces por partida (Torneio vs Sexo)
if 'ACE.1' in df_total.columns and 'ACE.2' in df_total.columns:
    df_total['Total_Aces'] = df_total['ACE.1'].fillna(0) + df_total['ACE.2'].fillna(0)
    sns.barplot(data=df_total, x='Torneio', y='Total_Aces', hue='Sexo', ax=axes[1], palette='Set1', errorbar=None)
    axes[1].set_title('Média de Aces por Partida (Torneio vs Sexo)')
    axes[1].set_xlabel('Torneio')
    axes[1].set_ylabel('Média de Aces por Jogo')

plt.tight_layout()
plt.show()

# 6. Top 10 Jogadores com mais vitórias nos 4 Grand Slams
print("\n=== TOP 10 TENISTAS COM MAIS VITÓRIAS (GERAL) ===")
top_vencedores = df_total.groupby(['Vencedor', 'Sexo']).size().reset_index(name='Vitorias')
display(top_vencedores.sort_values(by='Vitorias', ascending=False).head(10))
