import zipfile
import numpy as np
import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, Input, Output, dash_table

# ==========================================
# 1. LOAD DATA
# ==========================================
def load_data():
    zip_path = 'tennis+major+tournament+match+statistics.zip'
    dfs_list = []

    with zipfile.ZipFile(zip_path, 'r') as z:
        for file_name in z.namelist():
            if file_name.endswith('.csv'):
                parts = file_name.split('/')[-1].replace('.csv', '').split('-')
                tournament = parts[0]
                gender = 'Men' if parts[1].lower() == 'men' else 'Women'
                
                df_temp = pd.read_csv(z.open(file_name))
                df_temp.columns = [col.replace(' ', '') for col in df_temp.columns]
                df_temp['Tournament'] = tournament
                df_temp['Gender'] = gender
                dfs_list.append(df_temp)

    df_total = pd.concat(dfs_list, ignore_index=True)

    rounds_map = {
        1: '1st Round (R128)',
        2: '2nd Round (R64)',
        3: '3rd Round (R32)',
        4: 'Round of 16 (R16)',
        5: 'Quarterfinals (QF)',
        6: 'Semifinals (SF)',
        7: 'Final (F)'
    }
    df_total['Round_Name'] = df_total['Round'].map(rounds_map).fillna(df_total['Round'].astype(str))
    df_total['Winner'] = np.where(df_total['Result'] == 1, df_total['Player1'], df_total['Player2'])
    
    if 'ACE.1' in df_total.columns and 'ACE.2' in df_total.columns:
        df_total['Total_Aces'] = df_total['ACE.1'].fillna(0) + df_total['ACE.2'].fillna(0)
    else:
        df_total['Total_Aces'] = 0

    return df_total

df_total = load_data()

# ==========================================
# 2. INITIALIZE DASH & GUNICORN SERVER
# ==========================================
app = dash.Dash(__name__)
server = app.server  # Required for: gunicorn app:server

tournaments_available = list(df_total['Tournament'].unique())
genders_available = list(df_total['Gender'].unique())
rounds_available = list(df_total['Round_Name'].unique())

# ==========================================
# 3. DASHBOARD LAYOUT
# ==========================================
app.layout = html.Div([
    html.H1("Interactive Tennis Statistics Dashboard (Grand Slams)", style={'textAlign': 'center'}),
    html.Hr(),

    # Filters (Tournament, Gender, and Round)
    html.Div([
        html.Div([
            html.Label("Select Tournament(s):"),
            dcc.Dropdown(
                id='filter-tournament',
                options=[{'label': t, 'value': t} for t in tournaments_available],
                value=tournaments_available,
                multi=True
            )
        ], style={'width': '32%', 'display': 'inline-block', 'padding': '5px'}),

        html.Div([
            html.Label("Select Gender:"),
            dcc.Dropdown(
                id='filter-gender',
                options=[{'label': g, 'value': g} for g in genders_available],
                value=genders_available,
                multi=True
            )
        ], style={'width': '32%', 'display': 'inline-block', 'padding': '5px'}),
            
    ]),

    html.Hr(),

    # Main Metrics
    html.Div([
        html.Div([
            html.H4("Total Filtered Matches"),
            html.H2(id="metric-matches")
        ], style={'width': '48%', 'display': 'inline-block', 'textAlign': 'center', 'border': '1px solid #ddd', 'padding': '10px'}),

        html.Div([
            html.H4("Unique Players Involved"),
            html.H2(id="metric-players")
        ], style={'width': '48%', 'display': 'inline-block', 'textAlign': 'center', 'border': '1px solid #ddd', 'padding': '10px'})
    ]),

    html.Hr(),

    # Charts
    html.H3("Graphical Visualizations"),
    html.Div([
        html.Div(dcc.Graph(id="chart-matches"), style={'width': '50%', 'display': 'inline-block'}),
        html.Div(dcc.Graph(id="chart-aces"), style={'width': '50%', 'display': 'inline-block'})
    ]),

    html.Hr(),

    # Top 10 Winners
    html.H3("Top Tennis Players with Most Wins (Based on filters)"),
    html.Div(id="table-top10"),

    html.Hr(),

    # Matches Sample Table
    html.H3("Filtered Matches Sample"),
    html.Div(id="table-matches")

], style={'fontFamily': 'sans-serif', 'padding': '20px', 'maxWidth': '1200px', 'margin': 'auto'})

# ==========================================
# 4. CALLBACKS (INTERACTIVITY)
# ==========================================
@app.callback(
    [Output("metric-matches", "children"),
     Output("metric-players", "children"),
     Output("chart-matches", "figure"),
     Output("chart-aces", "figure"),
     Output("table-top10", "children"),
     Output("table-matches", "children")],
    [Input("filter-tournament", "value"),
     Input("filter-gender", "value"),
     Input("filter-round", "value")]
)
def update_dashboard(selected_tournaments, selected_genders, selected_rounds):
    if not selected_tournaments or not selected_genders or not selected_rounds:
        return "0", "0", {}, {}, html.P("Please select at least one option in each filter."), html.P("Please select at least one option in each filter.")

    # Filter dataframe based on selections
    df_filtered = df_total[
        (df_total['Tournament'].isin(selected_tournaments)) & 
        (df_total['Gender'].isin(selected_genders)) &
        (df_total['Round_Name'].isin(selected_rounds))
    ]

    # 1. Metrics
    total_matches = str(len(df_filtered))
    unique_players = str(len(pd.concat([df_filtered['Player1'], df_filtered['Player2']]).unique()))

    # 2. Matches Count Chart
    count_df = df_filtered.groupby(['Tournament', 'Gender']).size().reset_index(name='Matches')
    fig_matches = px.bar(count_df, x='Tournament', y='Matches', color='Gender', barmode='group',
                         title="Number of Matches by Tournament and Gender")

    # 3. Average Aces Chart
    avg_aces = df_filtered.groupby(['Tournament', 'Gender'])['Total_Aces'].mean().reset_index()
    fig_aces = px.bar(avg_aces, x='Tournament', y='Total_Aces', color='Gender', barmode='group',
                      title="Average Aces per Match")

    # 4. Top 10 Winners Table
    top_winners = df_filtered.groupby(['Winner', 'Gender']).size().reset_index(name='Wins')
    top_10 = top_winners.sort_values(by='Wins', ascending=False).head(10)
    table_10 = dash_table.DataTable(
        data=top_10.to_dict('records'),
        columns=[{"name": i, "id": i} for i in top_10.columns],
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '8px'}
    )

    # 5. Matches Sample Table
    cols_sample = ['Tournament', 'Gender', 'Round_Name', 'Player1', 'Player2', 'Winner', 'FNL1', 'FNL2']
    cols_existing = [c for c in cols_sample if c in df_filtered.columns]
    df_sample = df_filtered[cols_existing].head(50)
    table_sample = dash_table.DataTable(
        data=df_sample.to_dict('records'),
        columns=[{"name": i, "id": i} for i in df_sample.columns],
        page_size=10,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '8px'}
    )

    return total_matches, unique_players, fig_matches, fig_aces, table_10, table_sample

if __name__ == '__main__':
    app.run(debug=True)
