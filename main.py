import timeit
import networkx as nx

from eva import EvaProgram, Input, Output, evaluate
from eva.ckks import CKKSCompiler
from eva.seal import generate_keys
from eva.metric import valuation_mse

def generate_graph(n: int, k: int, p: int):
    # ws = nx.cycle_graph(n)
    G = nx.watts_strogatz_graph(n, k, p)

    return G

def serialize_graph(G, vec_size):
    node_count = G.size()
    total_edge_count = 0

    adj_matrix = [0 for _ in range(node_count*node_count)]

    for row in range(node_count):
        for column in range(node_count):
            if G.has_edge(row, column): #  or row == column# I assumed the vertices are connected to themselves
                adj_matrix[row*node_count + column] = 1
                total_edge_count += 1

    adj_matrix += [0 for _ in range(vec_size - len(adj_matrix))]

    print('created a graph with total edge count: ', total_edge_count)

    return adj_matrix

def pre_compute_parent(parent, vec_size):
    result = []

    for u in range(len(parent)):
        while parent[u] != u:
            u = parent[u]
        result.append(u)

    for _ in range(vec_size - len(result)):
        result.append(0)

    return result

def action_union(computed_parent, parent, rank, x, y):
    x_root = computed_parent[x]
    y_root = computed_parent[y]

    if x_root != y_root:
        if rank[x_root] < rank[y_root]:
            parent[x_root] = y_root
        elif rank[x_root] > rank[y_root]:
            parent[y_root] = x_root
        else:
            parent[y_root] = x_root
            rank[x_root] += 1

def graph_boruvka_1(node_count, data):
    parent_data_head = node_count*node_count
    cheapest = [-1 for _ in range(node_count)]

    result = 0

    for u in range(node_count):
        for v in range(node_count):
            if u == v:
                continue

            w = data << (u*node_count + v)

            set1 = data << (parent_data_head + u)
            set2 = data << (parent_data_head + v)

            result += w

    return result

def step(public_ctx, secret_ctx, signature, compiled_func, inputs):
    encInputs = public_ctx.encrypt(inputs, signature)
    encOutputs = public_ctx.execute(compiled_func, encInputs)

    outputs = secret_ctx.decrypt(encOutputs, signature)

    reference = evaluate(compiled_func, inputs)

    # Change this if you want to output something or comment out the two lines below
    for key in outputs:
        print(key, float(outputs[key][0]), float(reference[key][0]))


# Repeat the experiments and show averages with confidence intervals
# You can modify the input parameters
# n is the number of nodes in your graph
# If you require additional parameters, add them
def simulate(node_count):
    print("Will start simulation for ", node_count)

    config = {}
    config['warn_vec_size'] = 'true'
    config['lazy_relinearize'] = 'true'
    config['rescaler'] = 'always'
    config['balance_reductions'] = 'true'

    compiler = CKKSCompiler(config=config)

    vec_size = 4096

    G = generate_graph(node_count, 3, 0.5)
    adj_matrix = serialize_graph(G, vec_size // 2)

    parent = [i for i in range(node_count)]

    eva_prog_1 = EvaProgram("graph_boruvka_1", vec_size=vec_size)
    with eva_prog_1:
        data = Input('data')
        reval = graph_boruvka_1(node_count, data)

        Output('ReturnedValue', reval)

    eva_prog_1.set_output_ranges(30)
    eva_prog_1.set_input_scales(30)

    compiled_func_1, params, signature = compiler.compile(eva_prog_1)
    public_ctx, secret_ctx = generate_keys(params)

    while True:
        inputs = {"data": adj_matrix + pre_compute_parent(parent, vec_size // 2)}

        step(public_ctx, secret_ctx, signature, compiled_func_1, inputs)
        break


if __name__ == "__main__":
    num_sim = 1 # The number of simulation runs, set it to 3 during development otherwise you will wait for a long time

    print("Simulation started:")

    for n in range(36,64,4): # Node counts for experimenting various graph sizes
        for i in range(num_sim):
            simulate(n)
        break # TODO: remove
