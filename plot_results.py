import os
import sys

import csv
import matplotlib.pyplot as plt

def run_for_metrics(metrics):
    data = []
    columns = dict()

    with open("results.csv") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=",")

        for j, row in enumerate(csv_reader):
            if j == 0:
                for k, col in enumerate(row):
                    columns[col] = k
            else:
                data.append(row)

    total_results = dict()
    avg_results = dict()

    for metric in metrics:
        total_results[metric] = dict()
        avg_results[metric] = dict()

    for row in data:
        node_count = int(row[columns["node_count"]])

        for metric in metrics:
            if node_count not in total_results[metric]:
                total_results[metric][node_count] = []

            total_results[metric][node_count].append(float(row[columns[metric]]))

    for metric in metrics:
        for k, v in total_results[metric].items():
            avg_results[metric][k] = (sum(v) / len(v), len(v))

    x_values = avg_results["result_fhe"].keys()
    y_values = list(map(lambda x: x[0], avg_results["result_fhe"].values()))
    y1_values = list(map(lambda x: x[0], avg_results["result_raw"].values()))

    print(len(y_values), len(y1_values))

    fig, ax = plt.subplots()
    ax.set_xticks(list(x_values))

    plt.yscale("log")

    ax.bar(list(x_values), list(y1_values), width=3, color='r', label="RAW", align='edge')
    ax.bar(list(map(lambda x: x + 3, x_values)), list(y_values), width=3, color='b', label="FHE", align='edge')

    plt.xlabel("Node Count")
    plt.ylabel(f"Execution Time in Milliseconds")
    plt.legend(loc='best')

    plt.title(f"Total Execution Time")

    plt.savefig(f"out.png")

    plt.figure().clear()
    plt.close()
    plt.cla()
    plt.clf()

if __name__ == '__main__':
    metrics = ["result_fhe", "result_raw"]

    run_for_metrics(metrics)
