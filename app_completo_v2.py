
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import networkx as nx
import plotly.graph_objects as go

# Carregar grafo
G = nx.read_gexf("Grafo_Para_App_Dash.gexf")
pos = nx.spring_layout(G, seed=42, k=0.5, weight='weight')
nodes = list(G.nodes(data=True))
edges = list(G.edges(data=True))



nomes = sorted(set(d['nome'] for _, d in nodes))
tipos = sorted({t.strip() for _, d in nodes for t in d.get('Tipos', '').split(';') if t.strip()})
projetos = sorted({p.strip() for _, d in nodes for p in d.get('Projetos', '').split(';') if p.strip()})
inter_values = [float(d.get("intermediacao", 0)) for _, d in nodes]
inter_min, inter_max = min(inter_values), max(inter_values)

def normalizar_inter(v, vmin, vmax):
    return 8 + ((v - vmin) / (vmax - vmin)) * (30 - 8) if vmax > vmin else 8

app = dash.Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://fonts.googleapis.com/css2?family=Overpass:wght@400;700&display=swap"
])
app.title = "Rede de Líderes Cariocas"

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H2("Rede de Líderes Cariocas", className="my-3 text-primary fw-bold",
                        style={"fontFamily": "Overpass", "fontSize": "2.4rem"}), width=6),
        dbc.Col(html.Div([
            html.Img(src="/assets/logo_fjg_lideres.png", style={"height": "48px"})
        ], style={"display": "flex", "justifyContent": "flex-end", "alignItems": "center"}), width=6)
    ]),
    dbc.Row([
        dbc.Col([
            html.Label("Líder Carioca"),
            dcc.Dropdown([{"label": n, "value": n} for n in nomes], id="nome", multi=True),
            html.Label("Lógica dos filtros"),
            dcc.RadioItems(
                id="logica_filtros",
                options=[{"label": "AND", "value": "AND"}, {"label": "OR", "value": "OR"}],
                value="AND",
                labelStyle={"display": "inline-block", "margin-right": "10px"}
            ),
            html.Label("Projeto"),
            dcc.Dropdown([{"label": p, "value": p} for p in projetos], id="projeto_nome", multi=True),
            html.Label("Rede"),
            dcc.Dropdown([{"label": t, "value": t} for t in tipos], id="tipo", multi=True),
            html.Div(id="painel-conexoes", className="mt-4")
        ], width=3),
        dbc.Col([
            dcc.Graph(id="grafo", style={'height': '100%'})
        ], width=9, style={'height': '100%'})
    ], style={'height': '100%'})
], fluid=True, style={'height': '100vh'})

@app.callback(
    Output("grafo", "figure"),
    Output("painel-conexoes", "children"),
    Input("nome", "value"),
    Input("projeto_nome", "value"),
    Input("tipo", "value"),
    Input("logica_filtros", "value")
)
def atualizar_grafo(nome, projeto_nome, tipo, logica_filtros):
    todos_nos_validos = []
    for node, data in G.nodes(data=True):
        cond_tipo = not tipo or any(t in data.get("Tipos", "") for t in tipo)
        if logica_filtros == "AND":
            if cond_tipo:
                todos_nos_validos.append(node)
        else:
            if cond_tipo:
                todos_nos_validos.append(node)

    cor_niveis = {}
    destaque_projetos = set()

    def marcar_niveis(pessoa, cores):
        if not pessoa: return
        n1 = set(G.neighbors(pessoa))
        n2 = set().union(*(G.neighbors(n) for n in n1)) - n1 - {pessoa}
        n3 = set().union(*(G.neighbors(n) for n in n2)) - n2 - n1 - {pessoa}
        cor_niveis[pessoa] = cores[0]
        for n in n1: cor_niveis[n] = cor_niveis.get(n, cores[1])
        for n in n2: cor_niveis[n] = cor_niveis.get(n, cores[2])
        for n in n3: cor_niveis[n] = cor_niveis.get(n, cores[3])

    if nome:
        pessoa1 = next((n for n, d in G.nodes(data=True) if d["nome"] == nome[0]), None)
        marcar_niveis(pessoa1, ["#FF7F0E", "#FFB04D", "#FFE0B2", "#FFEDE0"])
        if len(nome) > 1:
            pessoa2 = next((n for n, d in G.nodes(data=True) if d["nome"] == nome[1]), None)
            marcar_niveis(pessoa2, ["#9467BD", "#BFA5D8", "#E5DFF1", "#F4F1F7"])

    if projeto_nome:
        for node, data in G.nodes(data=True):
            projetos_participados = data.get("Projetos", "")
            if any(p in projetos_participados for p in projeto_nome):
                destaque_projetos.add(node)

    node_x, node_y, size, text, color, customdata = [], [], [], [], [], []
    edge_x, edge_y = [], []
    for u, v, _ in edges:
        if u in todos_nos_validos and v in todos_nos_validos:
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]

    for node in todos_nos_validos:
        x, y = pos[node]
        d = G.nodes[node]
        grau = float(d.get("grau_ponderado", 0))
        inter = float(d.get("intermediacao", 0))
        size.append(normalizar_inter(inter, inter_min, inter_max))
        node_x.append(x)
        node_y.append(y)
        text.append(f"{d['nome']}<br>Código: {node}<br>Grau: {grau:.1f} (Rank {d['ranking_grau']})<br>Intermediação: {inter:.4f} (Rank {d['ranking_intermediacao']})")
        color.append("orange" if node in destaque_projetos else cor_niveis.get(node, "#73A5D5"))
        customdata.append(node)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y, mode="lines", hoverinfo="none", line=dict(width=0.5, color="#999")
    ))
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y, mode="markers", text=text, hoverinfo="text",
        marker=dict(size=size, color=color, line=dict(width=0.5, color='black')),
        customdata=customdata
    ))
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=10),
                      xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                      yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                      hovermode="closest")

    painel = html.Div()
    if nome and len(nome) == 1:
        pessoa = next((n for n, d in G.nodes(data=True) if d['nome'] == nome[0]), None)
        if pessoa:
            n1 = set(G.neighbors(pessoa))
            n2 = set().union(*(G.neighbors(n) for n in n1)) - n1 - {pessoa}
            n3 = set().union(*(G.neighbors(n) for n in n2)) - n2 - n1 - {pessoa}
            painel = dbc.Card([
                dbc.CardHeader("📋 Resumo da Pessoa Selecionada", className="fw-bold text-primary"),
                dbc.CardBody([
                    html.Div([
                        html.P(["📂 Projetos: ", html.Span(f"{len(G.nodes[pessoa].get('Projetos', '').split(';'))}", className="badge bg-info text-dark")]),
                        html.P(["📊 Centralidade de Grau: ", html.Span(f"#{G.nodes[pessoa].get('ranking_grau', 'N/A')}", className="badge bg-secondary")]),
                        html.P(["🧭 Intermediação: ", html.Span(f"#{G.nodes[pessoa].get('ranking_intermediacao', 'N/A')}", className="badge bg-secondary")])
                    ], className="mb-3"),
                    html.Div([
                        html.P(["🔁 Até 1º grau: ", html.Span(f"{len(n1)}", className="badge bg-success")]),
                        html.P(["🔁 Até 2º grau: ", html.Span(f"{len(n1 | n2)}", className="badge bg-success")]),
                        html.P(["🔁 Até 3º grau: ", html.Span(f"{len(n1 | n2 | n3)}", className="badge bg-success")])
                    ])
                ])
            ], className="mt-3 shadow-sm")

    return fig, painel

@app.callback(
    Output("nome", "value"),
    Input("grafo", "clickData"),
    prevent_initial_call=True
)
def clique_no_grafo(clickData):
    if clickData and "points" in clickData and clickData["points"]:
        codigo = clickData["points"][0].get("customdata")
        if codigo:
            for node, data in G.nodes(data=True):
                if node == codigo:
                    return [data["nome"]]
    return dash.no_update

if __name__ == "__main__":
    print("Servidor iniciando em http://127.0.0.1:8050")
    app.run(debug=True)
