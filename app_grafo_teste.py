# gexf_to_visjs_with_legend.py
"""
Gera um HTML interativo (vis.js) a partir de um GEXF,
com:
 - cores automáticas por label
 - legenda fixa
 - busca por label / id
 - toggle physics
 - tamanho do nó proporcional ao grau
"""

from pathlib import Path
import json
import networkx as nx
import matplotlib
from matplotlib import cm
from matplotlib import colors as mcolors

# -------------------------
INPUT_GEXF = "Grafo_Para_App_Dash.gexf"  # ajuste se necessário
OUTPUT_HTML = "graph_visjs_with_legend.html"
MAX_LABEL_CHARS = 80
BASE_NODE_SIZE = 10
SIZE_SCALE = 2
# -------------------------

gpath = Path(INPUT_GEXF)
if not gpath.exists():
    raise FileNotFoundError(f"Arquivo GEXF não encontrado: {gpath.resolve()}")

G = nx.read_gexf(str(gpath))
directed = G.is_directed()
if directed:
    H = G
else:
    H = G.to_undirected()

# coletar nomes (se existir, senão fallback para label/id)
labels = []
for n, data in H.nodes(data=True):
    nome = str(data.get("nome", data.get("label", n)))
    labels.append(nome)
unique_labels = sorted(set(labels))

# pegar colormap de forma compatível com versões do matplotlib
try:
    cmap = matplotlib.colormaps.get_cmap("tab20")
    cmap_n = cmap.colors if hasattr(cmap, "colors") else None
except Exception:
    cmap = cm.get_cmap("tab20")
    cmap_n = None

label_to_color = {}
for i, lab in enumerate(unique_labels):
    # usa índice ciclando pelo colormap
    try:
        col = mcolors.to_hex(cmap(i % (getattr(cmap, "N", 20))))
    except Exception:
        # fallback simples
        rgba = cmap(i % 20)
        col = mcolors.to_hex(rgba)
    label_to_color[lab] = col

# montar nodes e edges para vis.js
nodes = []
for node, data in H.nodes(data=True):
    lab = str(data.get("nome", data.get("label", node)))  # prioridade para 'nome'
    display_label = lab if len(lab) <= MAX_LABEL_CHARS else lab[:MAX_LABEL_CHARS - 3] + "..."
    title_parts = [f"{k}: {v}" for k, v in data.items()]
    title = "\n".join(title_parts) if title_parts else display_label
    size = BASE_NODE_SIZE + H.degree(node) * SIZE_SCALE
    nodes.append({
        "id": node,
        "label": display_label,
        "title": title,
        "value": size,
        "size": size,
        "color": label_to_color.get(lab, "#888888")
    })

edges = []
for u, v, data in H.edges(data=True):
    weight = data.get("weight", 1)
    width = max(1.0, min(8.0, float(weight)))
    edge = {"from": u, "to": v, "width": width, "value": weight, "title": f"weight: {weight}"}
    if directed:
        edge["arrows"] = "to"
    edges.append(edge)

nodes_json = json.dumps(nodes, ensure_ascii=False)
edges_json = json.dumps(edges, ensure_ascii=False)

# legenda HTML (gera blocos com cor + label)
legend_html = "<div id='legend'><b>Legenda (labels)</b><br>"
for lab, col in label_to_color.items():
    legend_html += f"<div class='legend-item'><span class='legend-swatch' style='background:{col}'></span>{lab}</div>"
legend_html += "</div>"

# HTML template
html = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Grafo (vis.js) — com legenda</title>
  <style>
    html,body {{ height:100%; margin:0; font-family: Arial, sans-serif; }}
    #mynetwork {{ width: 100%; height: 100vh; border: 1px solid #ddd; box-sizing: border-box; }}
    #controls {{
      position: fixed; left: 10px; top: 10px; z-index: 9999;
      background: rgba(255,255,255,0.95); border: 1px solid #ccc; padding: 8px; border-radius: 6px;
    }}
    #legend {{
      position: fixed; right: 10px; top: 10px; z-index: 9999;
      background: white; border: 1px solid #ccc; padding: 8px; max-height: 60vh; overflow:auto; border-radius:6px;
      font-size: 13px;
    }}
    .legend-item {{ margin:4px 0; display:flex; align-items:center; }}
    .legend-swatch {{ display:inline-block; width:14px; height:14px; margin-right:8px; border:1px solid #999; }}
    #search {{ width:200px; }}
    button {{ margin-left:6px; }}
  </style>
  <!-- vis.js standalone UMD -->
  <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
</head>
<body>
  <div id="controls">
    <input id="search" placeholder="Buscar por label ou id"/>
    <button onclick="searchNode()">Buscar</button>
    <button id="togglePhysics" onclick="togglePhysics()">Toggle physics</button>
  </div>

  {legend_html}

  <div id="mynetwork"></div>

  <script>
    const nodes = new vis.DataSet({nodes_json});
    const edges = new vis.DataSet({edges_json});

    const container = document.getElementById('mynetwork');
    const data = {{ nodes: nodes, edges: edges }};
    const options = {{
      nodes: {{
        shape: 'dot',
        scaling: {{
          min: 6,
          max: 60
        }},
        font: {{
          size: 14,
          face: 'Arial'
        }}
      }},
      edges: {{
        smooth: true,
        color: {{inherit: false}}
      }},
      physics: {{
        enabled: true,
        solver: 'forceAtlas2Based',
        stabilization: {{
          enabled: true,
          iterations: 1000,
        }},
        forceAtlas2Based: {{
          gravitationalConstant: -50,
          centralGravity: 0.01,
          springLength: 100,
          springConstant: 0.08,
          damping: 0.4,
          avoidOverlap: 0.5
        }},
        minVelocity: 0.75,
        timestep: 0.35
      }},
      interaction: {{
        hover: true,
        multiselect: false,
        dragNodes: true,
        zoomView: true
      }}
    }};

    const network = new vis.Network(container, data, options);

    function searchNode() {{
      const q = document.getElementById('search').value.trim().toLowerCase();
      if (!q) return;
      const all = nodes.get();
      // busca por id exato ou substring do label
      let found = all.find(n => String(n.id).toLowerCase() === q || (n.label && String(n.label).toLowerCase().includes(q)));
      if (!found) {{
        alert('Nenhum nó encontrado para: ' + q);
        return;
      }}
      network.selectNodes([found.id]);
      network.focus(found.id, {{scale: 1.3, animation: {{duration: 400}}}});
    }}

    let physicsOn = true;
    function togglePhysics() {{
      physicsOn = !physicsOn;
      network.setOptions({{ physics: {{ enabled: physicsOn }} }});
    }}

    // ADICIONADO: Efeito de esmaecimento ao selecionar um nó
    network.on("selectNode", function(params) {{
      const selectedNodeId = params.nodes[0];
      if (selectedNodeId) {{
        // Encontra todos os nós e arestas conectados ao nó selecionado
        const connectedNodes = network.getConnectedNodes(selectedNodeId);
        const connectedEdges = network.getConnectedEdges(selectedNodeId);

        // Define um conjunto com os IDs de todos os nós que DEVEM permanecer visíveis
        const visibleNodes = new Set(connectedNodes);
        visibleNodes.add(selectedNodeId);

        // Itera sobre todos os nós e ajusta a opacidade
        const updatedNodes = allNodes.map(node => {{
          const isVisible = visibleNodes.has(node.id);
          const color = nodes.get(node.id).color;
          return {{
            id: node.id,
            color: isVisible ? color : {{ border: '#e0e0e0', background: '#f5f5f5', highlight: color, hover: color }},
            font: {{ color: isVisible ? '#343434' : '#cccccc' }}
          }};
        }});

        // Itera sobre todas as arestas e ajusta a opacidade
        const updatedEdges = allEdges.map(edge => {{
          const isConnected = connectedEdges.includes(edge.id) || (visibleNodes.has(edge.from) && visibleNodes.has(edge.to));
          return {{
            id: edge.id,
            color: {{ color: isConnected ? '#848484' : '#f0f0f0' }},
            hidden: !isConnected // Oculta arestas não conectadas
          }};
        }});
        
        nodes.update(updatedNodes);
        edges.update(updatedEdges);

      }} else {{
        // Se nenhum nó estiver selecionado (clique no fundo), reverte para o estado original
        // Reinicializa com os dados originais
        nodes.clear();
        nodes.add(allNodes);
        edges.clear();
        edges.add(allEdges);
      }}
    }});

    // Tratamento para o caso de o usuário clicar no fundo
    network.on("click", function(params) {{
      if (params.nodes.length === 0) {{
        // Deseleciona tudo e reverte o estado
        network.unselectAll();
        nodes.clear();
        nodes.add(allNodes);
        edges.clear();
        edges.add(allEdges);
      }}
    }});
    
    // tooltip já vem do 'title' dos nodes; para debugar:
    // network.on('click', function(params) {{
    //   // params.nodes contém nó(s) clicados
    // }});
    
    
    

  </script>
</body>
</html>
"""

# escrever o arquivo
Path(OUTPUT_HTML).write_text(html, encoding="utf-8")
print(f"HTML gerado: {OUTPUT_HTML}")
