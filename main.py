import os
import timeit
import random
import csv

import networkx as nx

from datetime import datetime

from eva import EvaProgram, Input, Output, evaluate
from eva.ckks import CKKSCompiler
from eva.seal import generate_keys
from eva.metric import valuation_mse

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
            if G.has_edge(row, column):
                adj_matrix[row*node_count + column] = random.randint(1, 25)
                total_edge_count += 1

    print('created a graph with total edge count: ', total_edge_count)

    return adj_matrix

def calculate_all_parents(parent):
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

def action_union(parent, rank, x, y):
    computed_parents = calculate_all_parents(parent)

    x_root = computed_parents[x]
    y_root = computed_parents[y]

    if x_root != y_root:
        if rank[x_root] < rank[y_root]:
            parent[x_root] = y_root
        elif rank[x_root] > rank[y_root]:
            parent[y_root] = x_root
        else:
            parent[y_root] = x_root
            rank[x_root] += 1

def prepare_simulation(node_count):
    parent_data_head = node_count*node_count

    eva_prog = EvaProgram("graph_boruvka", vec_size=VEC_SIZE)
    with eva_prog:
        data = Input('data')

        result = []

        for u in range(node_count):
            for v in range(node_count):
                if u == v:
                    continue

                w = data << (u*node_count + v)

                set1 = data << (parent_data_head + u)
                set2 = data << (parent_data_head + v)

                result.append((u, v, w, set1, set2))

        Output("ResultSize", len(result))

        for i in range(len(result)):
            Output(f"Result_{i}_u", result[i][0])
            Output(f"Result_{i}_v", result[i][1])
            Output(f"Result_{i}_w", result[i][2])
            Output(f"Result_{i}_s1", result[i][3])
            Output(f"Result_{i}_s2", result[i][4])

    eva_prog.set_output_ranges(30)
    eva_prog.set_input_scales(30)

    start_time = timeit.default_timer()
    compiled_func, params, signature = compiler.compile(eva_prog)
    compilation_time = (timeit.default_timer() - start_time) * 1000.0

    start_time = timeit.default_timer()
    public_ctx, secret_ctx = generate_keys(params)
    keygen_time = (timeit.default_timer() - start_time) * 1000.0

    return compiled_func, public_ctx, secret_ctx, signature, compilation_time, keygen_time

def simulate_step(compiled_func, public_ctx, secret_ctx, signature, data):
    inputs = {"data": data + [0 for _ in range(VEC_SIZE - len(data))]}
    assert(len(inputs["data"]) == VEC_SIZE)

    start_time = timeit.default_timer()
    enc_inputs = public_ctx.encrypt(inputs, signature)
    enc_time = (timeit.default_timer() - start_time) * 1000.0

    start_time = timeit.default_timer()
    enc_outputs = public_ctx.execute(compiled_func, enc_inputs)
    execute_time = (timeit.default_timer() - start_time) * 1000.0

    start_time = timeit.default_timer()
    outputs = secret_ctx.decrypt(enc_outputs, signature)
    dec_time = (timeit.default_timer() - start_time) * 1000.0

    start_time = timeit.default_timer()
    reference = evaluate(compiled_func, inputs)
    ref_time = (timeit.default_timer() - start_time) * 1000.0

    mse = valuation_mse(outputs, reference)

    result = []
    for i in range(round(outputs["ResultSize"][0])):
        u = round(outputs[f"Result_{i}_u"][0])
        v = round(outputs[f"Result_{i}_v"][0])
        w = round(outputs[f"Result_{i}_w"][0])

        s1 = round(outputs[f"Result_{i}_s1"][0])
        s2 = round(outputs[f"Result_{i}_s2"][0])

        if s1 != s2 and w > 0:
            result.append((u, v, w, s1, s2))

    return result, enc_time, execute_time, dec_time, ref_time, mse

def simulate_with_graph(node_count, adj_matrix):
    print("Will start simulation for ", node_count)

    compiled_func, public_ctx, secret_ctx, signature, compilation_time, keygen_time = prepare_simulation(node_count)

    collected_data1 = [{
        "node_count": node_count,
        "compilation_time": compilation_time,
        "keygen_time": keygen_time,
    }]
    collected_data2 = []
    collected_data3 = []

    parent = [i for i in range(node_count)]
    rank = [0 for _ in range(node_count)]

    num_trees = node_count
    total_weight = 0
    num_total_edge = 0

    while num_trees > 1:
        cheapest = [-1 for _ in range(node_count)]

        data = adj_matrix + calculate_all_parents(parent)
        results, enc_time, execute_time, dec_time, ref_time, mse = simulate_step(compiled_func, public_ctx, secret_ctx, signature, data)
        collected_data2.append({
            "node_count": node_count,
            "enc_time": enc_time,
            "execute_time": execute_time,
            "dec_time": dec_time,
            "ref_time": ref_time,
            "mse": mse,
        })

        for u, v, w, s1, s2 in results:
            if cheapest[s1] == -1 or cheapest[s1][2] > w:
                cheapest[s1] = [u, v, w]

            if cheapest[s2] == -1 or cheapest[s2][2] > w:
                cheapest[s2] = [u, v, w]

        data = convert_cheapest_to_matrix(cheapest) + calculate_all_parents(parent)
        results, enc_time, execute_time, dec_time, ref_time, mse = simulate_step(compiled_func, public_ctx, secret_ctx, signature, data)
        collected_data3.append({
            "node_count": node_count,
            "enc_time": enc_time,
            "execute_time": execute_time,
            "dec_time": dec_time,
            "ref_time": ref_time,
            "mse": mse,
        })

        for u, v, w, s1, s2 in results:
            total_weight += w
            num_trees -= 1
            num_total_edge += 1

            action_union(parent, rank, s1, s2)
            print (f"Edge {u}-{v} with weight {w} included in MST")

    return num_total_edge, total_weight, collected_data1, collected_data2, collected_data3

def simulate_random_graph(node_count):
    G = generate_graph(node_count, 3, 0.5)
    adj_matrix = serialize_graph(G)

    return simulate_with_graph(node_count, adj_matrix)

RESULT_FILE_HEADERS = [
    ["node_count", "compilation_time", "keygen_time"],
    ["node_count", "enc_time", "execute_time", "dec_time", "ref_time", "mse"],
    ["node_count", "enc_time", "execute_time", "dec_time", "ref_time", "mse"],
]

if __name__ == "__main__":
    num_sim = 1 # 3

    print("Simulation started")

    collected_data = [[], [], []]

    for node_count in [4]: # range(36, 64, 4):
        for _ in range(num_sim):
            num_total_edge, total_weight, collected_data1, collected_data2, collected_data3 = simulate_random_graph(node_count)

            collected_data[0] += collected_data1
            collected_data[1] += collected_data2
            collected_data[2] += collected_data3

    ts = int(datetime.timestamp(datetime.now()))

    os.mkdir(f"results_stage2/{ts}")

    for i in range(3):
        with open(f"results_stage2/{ts}/results{i}.csv", "w") as csv_file:
            w = csv.DictWriter(csv_file, fieldnames=RESULT_FILE_HEADERS[i])
            w.writeheader()
            w.writerows(collected_data[i])

