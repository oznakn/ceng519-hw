import matplotlib.pyplot as plt
import networkx as nx

from raw import raw_boruvka
from fhe import serialize_graph, generate_graph

G = generate_graph(20, 3, 0.7)
adj_matrix = serialize_graph(G)

nx.draw_networkx(G, with_labels=True)

plt.savefig("graph_before.png")

plt.figure().clear()
plt.close()
plt.cla()
plt.clf()

result, edges = raw_boruvka(G.size(), adj_matrix)

edges_removal = []
for u, v, w in G.edges(data=True):
    if (u, v) not in edges and (v, u) not in edges:
        edges_removal.append((u, v))

for u,v in edges_removal:
    G.remove_edge(u, v)

nx.draw_networkx(G, with_labels=True)

plt.savefig("graph_after.png")

plt.figure().clear()
plt.close()
plt.cla()
plt.clf()
