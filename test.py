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

def boruvka(node_count, data):
    total_weight = 0
    num_total_edge = 0

    num_trees = node_count

    parent = [i for i in range(node_count)]
    rank = [0 for _ in range(node_count)]

    while num_trees > 1:
        cheapest = [-1 for _ in range(node_count)]

        for u in range(node_count):
            for v in range(node_count):
                if u == v:
                    continue

                w = data[u*node_count + v]

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

                    num_total_edge += 1

                    num_trees -= 1

    return (num_total_edge, total_weight)

if __name__ == '__main__':
    node_count = 4
    edges = [(0, 1, 10), (0, 2, 6), (0, 3, 5), (1, 3, 15), (2, 3, 4)]

    data = [0 for _ in range(node_count*node_count)]
    for u, v, w in edges:
        data[u*node_count + v] = w

    result = boruvka(node_count, data)
    print("total edge, weight", result)
    assert result == (3, 19)

    node_count = 5
    edges = [(0, 1, 8), (0, 2, 5), (1, 2, 9), (1, 3, 11), (2, 3, 15), (2, 4, 10), (3, 4, 7)]

    data = [0 for _ in range(node_count*node_count)]
    for u, v, w in edges:
        data[u*node_count + v] = w

    result = boruvka(node_count, data)
    print("total edge, weight", result)
    assert result == (4, 30)
