import sys
import os
import yaml
import networkx as nx
import matplotlib.pyplot as plt

def load_yaml(file_path):
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    return data

def build_and_draw_dag(edges, nodes):
    G = nx.DiGraph()

    for edge in edges:
        G.add_edge(edge['from'], edge['to'], weight=edge['weight'])

    # Ajout des attributs Graphviz pour espacer les nœuds

    # Utilisation de Graphviz pour une disposition hiérarchique
    try:
        pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
    except ImportError:
        print("Graphviz n'est pas installé. Utilisation de spring_layout comme solution de repli.")
        pos = nx.spring_layout(G, k=1.2)
    except:
        print("Erreur avec Graphviz. Utilisation de spring_layout comme solution de repli.")
        pos = nx.spring_layout(G, k=1.2)

    # Couleurs des nœuds
    node_colors = []
    for node in G.nodes():
            n_type = next((n['type'] for n in nodes if n['id'] == node), None)
            if n_type == 'latency':
                node_colors.append('lightblue')
            elif n_type == 'workload':
                node_colors.append('pink')
            else:
                node_colors.append('gray')

    plt.figure(figsize=(12, 8))
    nx.draw(G, pos, with_labels=True, node_size=6000, node_color=node_colors,
            font_size=10, font_weight='bold', arrowsize=25)

    edge_labels = {(u, v): f"{d['weight']}" for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='black', font_size=12)

    plt.title("DAG avec disposition hiérarchique et nœuds espacés")
    file_name = os.path.splitext(os.path.basename(sys.argv[1]))[0]
    plt.savefig(file_name + ".png")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 graph_visualizor.py <file_name.bs.yaml>")
        sys.exit(1)

    file_path = sys.argv[1]

    data = load_yaml(file_path)
    build_and_draw_dag(data['edges'], data['nodes'])

if __name__ == "__main__":
    main()