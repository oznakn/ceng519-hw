import timeit
import networkx as nx

from eva import EvaProgram, Input, Output, evaluate
from eva.ckks import CKKSCompiler
from eva.seal import generate_keys
from eva.metric import valuation_mse

from test import union

VEC_SIZE = 4096

compiler_config = {}
compiler_config['warn_vec_size'] = 'true'
compiler_config['lazy_relinearize'] = 'true'
compiler_config['rescaler'] = 'always'
compiler_config['balance_reductions'] = 'true'

compiler = CKKSCompiler(config=compiler_config)

def generate_graph(n: int, k: int, p: int):
    # ws = nx.cycle_graph(n)
    G = nx.watts_strogatz_graph(n, k, p)

    return G

def serialize_graph(G):
    node_count = G.size()
    total_edge_count = 0

    adj_matrix = [0 for _ in range(node_count*node_count)]

    for row in range(node_count):
        for column in range(node_count):
            if G.has_edge(row, column): #  or row == column# I assumed the vertices are connected to themselves
                adj_matrix[row*node_count + column] = 1
                total_edge_count += 1

    print('created a graph with total edge count: ', total_edge_count)

    return adj_matrix

def pre_compute_parent(parent):
    result = []

    for u in range(len(parent)):
        while parent[u] != u:
            u = parent[u]
        result.append(u)

    return result

def convert_cheapest_to_matrix(cheapest):
    node_count = len(cheapest)

    result = [0 for _ in range(node_count*node_count)]

    for i in range(node_count):
        if cheapest[i] != -1:
            u, v, w = cheapest[i]

            result[u*node_count + v] = w

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

def graph_boruvka(node_count, data):
    parent_data_head = node_count*node_count

    result = []

    for u in range(node_count):
        for v in range(node_count):
            if u == v:
                continue

            w = data << (u*node_count + v)

            set1 = data << (parent_data_head + u)
            set2 = data << (parent_data_head + v)

            result.append((u, v, w, set1, set2))

    return result

def step(compiled_func, public_ctx, secret_ctx, signature, adj_matrix, parent, rank, cheapest):
    total_weight = 0

    data = adj_matrix + pre_compute_parent(parent)
    inputs = {"data": data + [0 for _ in range(VEC_SIZE - len(data))]}

    enc_inputs = public_ctx.encrypt(inputs, signature)
    enc_outputs = public_ctx.execute(compiled_func, enc_inputs)
    outputs = secret_ctx.decrypt(enc_outputs, signature)
    # reference = evaluate(compiled_func, inputs)

    num_result = round(outputs["ResultSize"][0])
    for i in range(num_result):
        u = round(outputs[f"Result_{i}_u"][0])
        v = round(outputs[f"Result_{i}_v"][0])
        w = round(outputs[f"Result_{i}_w"][0])

        s1 = round(outputs[f"Result_{i}_s1"][0])
        s2 = round(outputs[f"Result_{i}_s2"][0])

        if s1 != s2 and w > 0:
            if cheapest[s1] == -1 or cheapest[s1 + 2] > w:
                cheapest[s1] = u
                cheapest[s1 + 1] = v
                cheapest[s1 + 2] = w

            if cheapest[s2] == -1 or cheapest[s2 + 2] > w:
                cheapest[s2] = u
                cheapest[s2 + 1] = v
                cheapest[s2 + 2] = w

    print(cheapest)

    data = convert_cheapest_to_matrix(cheapest) + pre_compute_parent(parent)
    inputs = {"data": data + [0 for _ in range(VEC_SIZE - len(data))]}

    enc_inputs = public_ctx.encrypt(inputs, signature)
    enc_outputs = public_ctx.execute(compiled_func, enc_inputs)
    outputs = secret_ctx.decrypt(enc_outputs, signature)
    # reference = evaluate(compiled_func, inputs)

    num_result = round(outputs["ResultSize"][0])
    for i in range(num_result):
        u = round(outputs[f"Result_{i}_u"][0])
        v = round(outputs[f"Result_{i}_v"][0])
        w = round(outputs[f"Result_{i}_w"][0])

        s1 = round(outputs[f"Result_{i}_s1"][0])
        s2 = round(outputs[f"Result_{i}_s2"][0])

        if s1 != s2 and w > 0:
            total_weight += w
            union(parent, rank, s1, s2)

    # # Change this if you want to output something or comment out the two lines below
    # for key in outputs:
    #     print(key, int(reference[key][0])) # float(outputs[key][0]),

    print(total_weight)

def prepare_simulation(node_count):
    eva_prog = EvaProgram("graph_boruvka", vec_size=VEC_SIZE)
    with eva_prog:
        data = Input('data')
        result = graph_boruvka(node_count, data)

        Output("ResultSize", len(result))

        for i in range(len(result)):
            Output(f"Result_{i}_u", result[i][0])
            Output(f"Result_{i}_v", result[i][1])
            Output(f"Result_{i}_w", result[i][2])
            Output(f"Result_{i}_s1", result[i][3])
            Output(f"Result_{i}_s2", result[i][4])

    eva_prog.set_output_ranges(30)
    eva_prog.set_input_scales(30)

    compiled_func, params, signature = compiler.compile(eva_prog)
    public_ctx, secret_ctx = generate_keys(params)

    return compiled_func, public_ctx, secret_ctx, signature

# Repeat the experiments and show averages with confidence intervals
# You can modify the input parameters
# n is the number of nodes in your graph
# If you require additional parameters, add them
def simulate(node_count):
    print("Will start simulation for ", node_count)

    compiled_func, public_ctx, secret_ctx, signature = prepare_simulation(node_count)

    G = generate_graph(node_count, 3, 0.5)
    adj_matrix = serialize_graph(G)

    parent = [i for i in range(node_count)]
    rank = [0 for i in range(node_count)]
    cheapest = [-1 for _ in range(node_count)]

    while True:
        step(compiled_func, public_ctx, secret_ctx, signature, adj_matrix, parent, rank, cheapest)
        break


if __name__ == "__main__":
    num_sim = 1 # The number of simulation runs, set it to 3 during development otherwise you will wait for a long time

    print("Simulation started:")
    simulate(4)

    # for n in range(36,64,4): # Node counts for experimenting various graph sizes
    #     for i in range(num_sim):
    #     break # TODO: remove
