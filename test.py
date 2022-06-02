import os
import timeit
import random
import csv

from datetime import datetime

from fhe import simulate_with_graph, generate_graph, serialize_graph
from raw import raw_boruvka

def run_test(node_count, edges, expected_result):
    adj_matrix = [0 for _ in range(node_count*node_count)]
    for u, v, w in edges:
        adj_matrix[u*node_count + v] = w

    print(f"test for raw with node {node_count}")
    result, _ = raw_boruvka(node_count, adj_matrix)
    assert result == expected_result

    print(f"test for fhe with node {node_count}")
    num_e, w, _, _, _ = simulate_with_graph(node_count, adj_matrix)
    assert (num_e, w) == expected_result

RESULT_FILE_HEADERS = [
    ["node_count", "compilation_time", "keygen_time"],
    ["node_count", "enc_time", "execute_time", "dec_time", "ref_time", "mse"],
    ["node_count", "enc_time", "execute_time", "dec_time", "ref_time", "mse"],
]

if __name__ == '__main__':
    node_count = 4
    edges = [(0, 1, 10), (0, 2, 6), (0, 3, 5), (1, 3, 15), (2, 3, 4)]

    run_test(node_count, edges, (3, 19))

    node_count = 5
    edges = [(0, 1, 8), (0, 2, 5), (1, 2, 9), (1, 3, 11), (2, 3, 15), (2, 4, 10), (3, 4, 7)]
    run_test(node_count, edges, (4, 30))

    collected_data = [[], [], []]

    for node_count in [4, 12, 24, 32]:
        G = generate_graph(node_count, 3, 0.5)
        adj_matrix = serialize_graph(G)

        print('starting raw')
        start_time = timeit.default_timer()
        result, _ = raw_boruvka(node_count, adj_matrix)
        raw_time = (timeit.default_timer() - start_time) * 1000.0

        print('starting fhe')
        start_time = timeit.default_timer()
        num_e, w, d1, d2, d3 = simulate_with_graph(node_count, adj_matrix)
        simulation_time = (timeit.default_timer() - start_time) * 1000.0

        collected_data[0] += d1
        collected_data[1] += d2
        collected_data[2] += d3

        print((num_e, w), result)
        assert (num_e, w) == result
        print(simulation_time, raw_time)

    ts = int(datetime.timestamp(datetime.now()))

    os.mkdir(f"results_stage2/{ts}")

    for i in range(3):
        with open(f"results_stage2/{ts}/results{i}.csv", "w") as csv_file:
            w = csv.DictWriter(csv_file, fieldnames=RESULT_FILE_HEADERS[i])
            w.writeheader()
            w.writerows(collected_data[i])
