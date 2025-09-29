import networkx as nx
from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

# Mapeamento dos atributos do GEXF para nomes amigáveis no JavaScript
# Note que os títulos no GEXF são strings, então usamos strings aqui.
ATTRIBUTE_MAP = {
    'nome': 'nome',
    'grau_ponderado': 'grau_ponderado',
    'intermediacao': 'intermediacao',
    'ranking_grau': 'ranking_grau',
    'ranking_intermediacao': 'ranking_intermediacao',
    'grupo': 'grupo',
    'Projetos': 'Projetos',
    'Tipos': 'Tipos',
    'Codigos_Projetos': 'Codigos_Projetos'
}

# Invertendo o mapeamento para usar os títulos dos atributos como chaves
# Isso permite uma busca mais eficiente, mas também é possível iterar
# sobre os itens diretamente. Para este caso, vamos simplificar.
# A melhor abordagem é simplesmente usar os títulos diretamente no código.

@app.route('/data', methods=['GET'])
def get_graph_data():
    """Lê o arquivo GEXF, converte para JSON e retorna os dados."""
    gexf_file_path = 'Grafo_Para_App_Dash.gexf'
    try:
        # Carrega o grafo do arquivo GEXF
        G = nx.read_gexf(gexf_file_path)

        nodes = []
        for node_id, data in G.nodes(data=True):
            # NetworkX já lê os atributos usando seus títulos.
            # Basta acessar os atributos com os nomes corretos.
            
            # Garante que os valores numéricos são do tipo correto e evita erros
            try:
                grau_ponderado = float(data.get('grau_ponderado', 0))
                intermediacao = float(data.get('intermediacao', 0))
                ranking_grau = int(data.get('ranking_grau', 0))
                ranking_intermediacao = int(data.get('ranking_intermediacao', 0))
            except (ValueError, TypeError):
                # Caso a conversão falhe, define valores padrão
                grau_ponderado = 0
                intermediacao = 0
                ranking_grau = 0
                ranking_intermediacao = 0

            # Prepara o título do nó para o tooltip
            title = f"Nome: {data.get('nome', 'N/A')}<br/>" \
                    f"Grau Ponderado: {grau_ponderado}<br/>" \
                    f"Intermediação: {intermediacao}<br/>" \
                    f"Ranking Grau: #{ranking_grau}<br/>" \
                    f"Ranking Intermediação: #{ranking_intermediacao}"
            
            node = {
                'id': node_id,
                'nome': data.get('nome', node_id),
                'title': title,
                'size': 15,
                'color': '#73A5D5',
                'font': {'size': 12},
                'grau_ponderado': grau_ponderado,
                'intermediacao': intermediacao,
                'ranking_grau': ranking_grau,
                'ranking_intermediacao': ranking_intermediacao,
                'grupo': data.get('grupo', 'N/A'),
                'Projetos': data.get('Projetos', 'N/A'),
                'Tipos': data.get('Tipos', 'N/A'),
                'Codigos_Projetos': data.get('Codigos_Projetos', 'N/A')
            }
            nodes.append(node)

        edges = []
        for u, v, data in G.edges(data=True):
            edge = {
                'from': u,
                'to': v,
                'weight': float(data.get('weight', 1)),
                'color': '#999999'
            }
            edges.append(edge)

        return jsonify({'nodes': nodes, 'edges': edges})

    except FileNotFoundError:
        return jsonify({'error': f'Arquivo {gexf_file_path} não encontrado.'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/demograficos', methods=['GET'])
def le_demograficos():
    excel_file_path = 'Banco_Analise_Redes dos Líderes Cariocas - GTTs TCs Mentoria.xlsx'
    try:
        #Lê arquivo Excel
        df = pd.read_excel(excel_file_path, sheet_name= 'Integrantes dos Projetos')

        print("Colunas encontradas no arquivo Excel:", df.columns)

        #Tratamento de linhas em branco
        df['Sexo'] = df['Sexo'].astype(str).str.strip().str.capitalize()
        df['Sexo'].fillna('Não informado', inplace=True)

        df['Sexo'] = df['Sexo'].replace({'M': 'Masculino', 'F': 'Feminino'})

        contagem_sexo = df['Sexo'].value_counts()

        total = contagem_sexo.sum()
        percentagem_sexo = (contagem_sexo / total) *100

        #Formatando p/ gráfico
        demograficos = {
            'labels': contagem_sexo.index.tolist(),
            'values': percentagem_sexo.round(2).tolist()
        }

        return jsonify(demograficos)
    
    except FileNotFoundError:
        return jsonify({'Erro': f'Arquivo {excel_file_path} não encontrado.'}), 404
    except Exception as erro:
        # A mensagem de erro será mais detalhada
        return jsonify({'Erro': f'Ocorreu um erro no servidor: {str(erro)}'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)