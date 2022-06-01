import timeit
import networkx as nx

from eva import EvaProgram, Input, Output, evaluate
from eva.ckks import CKKSCompiler
from eva.seal import generate_keys
from eva.metric import valuation_mse

ctx = dict()

def generate_graph(n: int, k: int, p: int):
    # ws = nx.cycle_graph(n)
    G = nx.watts_strogatz_graph(n, k, p)

    return G

def serialize_graph(G, vec_size):
    edge_list = []

    for row in range(G.size()):
        for column in range(G.size()):
            if G.has_edge(row, column): #  or row == column# I assumed the vertices are connected to themselves
                edge_list += [row, column, 1]

    for _ in range(vec_size - len(edge_list)):
        edge_list.append(0)

    return edge_list

# Eva requires special input, this function prepares the eva input
# Eva will then encrypt them
def prepare_initial_input(n, vec_size):
    input = {}

    G = generate_graph(n, 3, 0.5)

    edge_list = serialize_graph(G, vec_size)
    input["Edges"] = edge_list

    return input

def set_context(node_count, edge_count):
    ctx["node_count"] = node_count
    ctx["edge_count"] = edge_count


def pre_compute_parent(parent):
    result = []

    for u in range(len(parent)):
        while parent[u] != u:
            u = parent[u]
        result.append(u)

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

def graph_boruvka_1(edges):
    print("hey")
    node_count = ctx["node_count"]
    edge_count = ctx["edge_count"]

    cheapest = [-1 for _ in range(node_count)]

    for i in range(0, edge_count, 3):
        return (0, 0)


# Do not change this
# the parameter n can be passed in the call from simulate function
class EvaProgramDriver(EvaProgram):
    def __init__(self, name, vec_size=4096, n=4):
        self.n = n
        super().__init__(name, vec_size)

    def __enter__(self):
        super().__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        super().__exit__(exc_type, exc_value, traceback)

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
def simulate(n):
    m = 4096*4
    print("Will start simulation for ", n)

    inputs = prepare_initial_input(n, m)

    set_context(n, len(inputs["Edges"]))

    config = {}
    config['warn_vec_size'] = 'false'
    config['lazy_relinearize'] = 'true'
    config['rescaler'] = 'always'
    config['balance_reductions'] = 'true'

    compiler = CKKSCompiler(config=config)

    eva_prog_1 = EvaProgramDriver("graph_boruvka", vec_size=m, n=n)
    with eva_prog_1:
        edges = Input('Edges')
        reval, x = graph_boruvka_1(edges)

        Output('ReturnedValue', reval)
        Output('X', x)

    eva_prog_1.set_output_ranges(30)
    eva_prog_1.set_input_scales(30)

    compiled_func_1, params, signature = compiler.compile(eva_prog_1)
    public_ctx, secret_ctx = generate_keys(params)

    step(public_ctx, secret_ctx, signature, compiled_func_1, inputs)


if __name__ == "__main__":
    num_sim = 1 # The number of simulation runs, set it to 3 during development otherwise you will wait for a long time

    print("Simulation campaing started:")

    for n in range(36,64,4): # Node counts for experimenting various graph sizes
        for i in range(num_sim):
            simulate(n)
        break # TODO: remove
