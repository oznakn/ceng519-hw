import csv
import matplotlib.pyplot as plt

metrics = ["CompileTime", "KeyGenerationTime", "EncryptionTime", "ExecutionTime", "DecryptionTime", "ReferenceExecutionTime", "Mse"]
data = []
columns = dict()

for i in range(1, 10 + 1):
    with open(f"results/results-{i}.csv") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=",")

        for j, row in enumerate(csv_reader):
            if i == 1 and j == 0:
                for k, col in enumerate(row):
                    columns[col] = k
            elif j != 0:
                data.append(row)

total_results = dict()
avg_results = dict()

for metric in metrics:
    total_results[metric] = dict()
    avg_results[metric] = dict()

for row in data:
    node_count = int(row[columns["NodeCount"]])

    for metric in metrics:
        if node_count not in total_results[metric]:
            total_results[metric][node_count] = []

        total_results[metric][node_count].append(float(row[columns[metric]]))

for metric in metrics:
    for k, v in total_results[metric].items():
        avg_results[metric][k] = (sum(v) / len(v), len(v))

for metric in metrics:
    x_values = avg_results[metric].keys()
    y_values = list(map(lambda x: x[0], avg_results[metric].values()))

    plt.bar(x_values, y_values)

    plt.xlabel("Node Count")
    plt.ylabel(f"{metric} in milliseconds")

    plt.title(f"Average {metric}")

    plt.savefig(f"results/{metric}.png")

    fig = plt.figure()
    plt.figure().clear()
    plt.close()
    plt.cla()
    plt.clf()

print(avg_results)
