import zipfile
import numpy as np
import pandas as pd
from flask import Flask

# Inicializa a aplicação Flask (o Gunicorn procura por esta variável 'app')
app = Flask(__name__)

@app.route('/')
def home():
    # 1. Caminho do ficheiro ZIP no repositório
    caminho_zip = 'tennis+major+tournament+match+statistics.zip'
    
    # 2. Extração e unificação dos ficheiros CSV
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

    # Top 10 tenistas com mais vitórias
    top_vencedores = df_total.groupby(['Vencedor', 'Sexo']).size().reset_index(name='Vitorias')
    top_10 = top_vencedores.sort_values(by='Vitorias', ascending=False).head(10)

    # 3. Gerar a página HTML de resposta
    html_content = f"""
    <html>
        <head>
            <title>Estatísticas de Ténis</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f4f4f9; color: #333; }}
                h1, h2 {{ color: #2c3e50; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 30px; background: #fff; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>Painel de Estatísticas de Ténis dos Grand Slams</h1>
            <p><b>Total de partidas carregadas:</b> {len(df_total)}</p>
            
            <h2>Top 10 Tenistas com Mais Vitórias (Geral)</h2>
            {top_10.to_html(index=False, classes='table')}
            
            <h2>Amostra de Partidas (Primeiras 10)</h2>
            {df_total[['Torneio', 'Sexo', 'Nome_Ronda', 'Player1', 'Player2', 'Vencedor']].head(10).to_html(index=False, classes='table')}
        </body>
    </html>
    """
    return html_content

if __name__ == '__main__':
    app.run(debug=True)

