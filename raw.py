def find(parent, u):
    while parent[u] != u:
        u = parent[u]
    return u

def union(parent, rank, x, y):
    x_root = find(parent, x)
    y_root = find(parent, y)

    if x_root != y_root:
        if rank[x_root] < rank[y_root]:
            parent[x_root] = y_root
        elif rank[x_root] > rank[y_root]:
            parent[y_root] = x_root
        else:
            parent[y_root] = x_root
            rank[x_root] += 1

def raw_boruvka(node_count, adj_matrix):
    total_weight = 0
    num_total_edge = 0
    result_edges = set()

    num_trees = node_count

    parent = [i for i in range(node_count)]
    rank = [0 for _ in range(node_count)]

    while num_trees > 1:
        cheapest = [-1 for _ in range(node_count)]

        for u in range(node_count):
            for v in range(node_count):
                if u == v:
                    continue

                w = adj_matrix[u*node_count + v]

                if w > 0:
                    set1 = find(parent, u)
                    set2 = find(parent, v)

                    if set1 != set2:
                        if cheapest[set1] == -1 or cheapest[set1][2] > w:
                            cheapest[set1] = [u, v, w]

                        if cheapest[set2] == -1 or cheapest[set2][2] > w:
                            cheapest[set2] = [u, v, w]

        for i in range(node_count):
            if cheapest[i] != -1:
                u, v, w = cheapest[i]

                set1 = find(parent, u)
                set2 = find(parent, v)

                if set1 != set2:
                    total_weight += w
                    union(parent, rank, set1, set2)

                    print (f"Edge {u}-{v} with weight {w} included in MST")

                    result_edges.add((u, v))
                    num_total_edge += 1

                    num_trees -= 1

    return (num_total_edge, total_weight), result_edges
