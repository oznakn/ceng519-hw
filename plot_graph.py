import matplotlib.pyplot as plt
import networkx as nx

G = nx.watts_strogatz_graph(30, 3, 0.5)


nx.draw_networkx(G, with_labels=True)

plt.savefig("graph.png")

plt.figure().clear()
plt.close()
plt.cla()
plt.clf()
