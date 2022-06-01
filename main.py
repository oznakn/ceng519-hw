import timeit
import networkx as nx

from eva import EvaProgram, Input, Output, evaluate
from eva.ckks import CKKSCompiler
from eva.seal import generate_keys
from eva.metric import valuation_mse

# Using networkx, generate a random graph
# You can change the way you generate the graph
def generateGraph(n: int, k: int, p: int):
    # ws = nx.cycle_graph(n)
    G = nx.watts_strogatz_graph(n, k, p)
    return G

# If there is an edge between two vertices its weight is 1 otherwise it is zero
# You can change the weight assignment as required
# Two dimensional adjacency matrix is represented as a vector
# Assume there are n vertices
# (i,j)th element of the adjacency matrix corresponds to (i*n + j)th element in the vector representations
def serializeGraphZeroOne(G, vec_size):
    graph_weight_list = []
    graph_dict = {}

    n = G.size()

    for row in range(n):
        for column in range(n):
            if G.has_edge(row, column): #  or row == column# I assumed the vertices are connected to themselves
                weight = 2
            else:
                weight = 1

            graph_weight_list.append(weight)

            graph_dict[f"{row}-{column}"] = [weight] # EVA requires str:listoffloat

    # EVA vector size has to be large, if the vector representation of the graph is smaller, fill the eva vector with zeros
    for _ in range(vec_size - n*n):
        graph_weight_list.append(0.0)

    return graph_weight_list, graph_dict

# To display the generated graph
def printGraph(graph, n):
    for row in range(n):
        for column in range(n):
            print("{:.5f}".format(graph[row*n+column]), end = '\t')
        print()

# Eva requires special input, this function prepares the eva input
# Eva will then encrypt them
def prepareInput(n, vec_size):
    input = {}

    G = generateGraph(n, 3, 0.5)

    graph_weight_list, graph_dict = serializeGraphZeroOne(G, vec_size)
    input['Graph'] = graph_weight_list

    return input

# you can other parameters using global variables !!! do not change the signature of this function
def graph_boruvka(graph, graph_size):
    reval = 0

    for i in range(graph_size):
        reval += pow(graph<<i, 2)

    # Note that you cannot compute everything using EVA/CKKS
    # For instance, comparison is not possible
    # You can add, subtract, multiply, negate, shift right/left
    # You will have to implement an interface with the trusted entity for comparison (send back the encrypted values, push the trusted entity to compare and get the comparison output)
    return reval

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

# Repeat the experiments and show averages with confidence intervals
# You can modify the input parameters
# n is the number of nodes in your graph
# If you require additional parameters, add them
def simulate(n):
    m = 4096*4

    print("Will start simulation for ", n)
    config = {}
    config['warn_vec_size'] = 'false'
    config['lazy_relinearize'] = 'true'
    config['rescaler'] = 'always'
    config['balance_reductions'] = 'true'
    inputs = prepareInput(n, m)

    eva_prog = EvaProgramDriver("graph_boruvka", vec_size=m, n=n)
    with eva_prog:
        graph = Input('Graph')
        reval = graph_boruvka(graph, n)
        Output('ReturnedValue', reval)

    eva_prog.set_output_ranges(30)
    eva_prog.set_input_scales(30)

    start = timeit.default_timer()
    compiler = CKKSCompiler(config=config)
    compiled_multfunc, params, signature = compiler.compile(eva_prog)
    compiletime = (timeit.default_timer() - start) * 1000.0 #ms

    start = timeit.default_timer()
    public_ctx, secret_ctx = generate_keys(params)
    keygenerationtime = (timeit.default_timer() - start) * 1000.0 #ms

    start = timeit.default_timer()
    encInputs = public_ctx.encrypt(inputs, signature)
    encryptiontime = (timeit.default_timer() - start) * 1000.0 #ms

    start = timeit.default_timer()
    encOutputs = public_ctx.execute(compiled_multfunc, encInputs)
    executiontime = (timeit.default_timer() - start) * 1000.0 #ms

    start = timeit.default_timer()
    outputs = secret_ctx.decrypt(encOutputs, signature)
    decryptiontime = (timeit.default_timer() - start) * 1000.0 #ms

    start = timeit.default_timer()
    reference = evaluate(compiled_multfunc, inputs)
    referenceexecutiontime = (timeit.default_timer() - start) * 1000.0 #ms

    # Change this if you want to output something or comment out the two lines below
    for key in outputs:
        print(key, float(outputs[key][0]), float(reference[key][0]))

    mse = valuation_mse(outputs, reference) # since CKKS does approximate computations, this is an important measure that depicts the amount of error

    return compiletime, keygenerationtime, encryptiontime, executiontime, decryptiontime, referenceexecutiontime, mse


if __name__ == "__main__":
    simcnt = 3 #The number of simulation runs, set it to 3 during development otherwise you will wait for a long time
    # For benchmarking you must set it to a large number, e.g., 100
    #Note that file is opened in append mode, previous results will be kept in the file
    resultfile = open("results.csv", "a")  # Measurement results are collated in this file for you to plot later on
    resultfile.write("NodeCount,SimCnt,CompileTime,KeyGenerationTime,EncryptionTime,ExecutionTime,DecryptionTime,ReferenceExecutionTime,Mse\n")
    resultfile.close()

    print("Simulation campaing started:")
    for nc in range(36,64,4): # Node counts for experimenting various graph sizes
        n = nc
        resultfile = open("results.csv", "a")
        for i in range(simcnt):
            #Call the simulator
            compiletime, keygenerationtime, encryptiontime, executiontime, decryptiontime, referenceexecutiontime, mse = simulate(n)
            res = str(n) + "," + str(i) + "," + str(compiletime) + "," + str(keygenerationtime) + "," +  str(encryptiontime) + "," +  str(executiontime) + "," +  str(decryptiontime) + "," +  str(referenceexecutiontime) + "," +  str(mse) + "\n"
            print(res)
            # resultfile.write(res)
            break # TODO: remove
        break # TODO: remove

        resultfile.close()
