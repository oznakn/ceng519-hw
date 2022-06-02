import os
import sys

import csv
import matplotlib.pyplot as plt

def run_for_metrics(metrics, metric_names, results_paths, irange, log_scale=True):
    data = []
    columns = dict()

    for results_path in results_paths:
        for i in irange:
            with open(f"{results_path}/results{i}.csv") as csv_file:
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

    for metric in metrics:
        x_values = avg_results[metric].keys()
        y_values = list(map(lambda x: x[0], avg_results[metric].values()))

        fig, ax = plt.subplots()
        ax.set_xticks(list(x_values))

        if log_scale:
            plt.yscale("log")

        plt.bar(list(x_values), list(y_values), width=3)

        plt.xlabel("Node Count")
        plt.ylabel(f"{metric_names[metrics.index(metric)]} in milliseconds")

        plt.title(f"Average {metric_names[metrics.index(metric)]}")

        plt.savefig(f"results_output/{metric}.png")

        plt.figure().clear()
        plt.close()
        plt.cla()
        plt.clf()

if __name__ == '__main__':

    if len(sys.argv) < 2:
        raise Exception("argument needed")

    results_path = sys.argv[1:]

    metrics = ["execute_time", "dec_time", "ref_time"]
    metric_names = ["Execution Time", "Decryption Time", "Reference Time"]

    run_for_metrics(metrics, metric_names, results_path, [1, 2])

    metrics = ["enc_time", "mse"]
    metric_names = ["Encryption Time", "MSE"]

    run_for_metrics(metrics, metric_names, results_path, [1, 2], log_scale=False)


    metrics = ["compilation_time", "keygen_time"]
    metric_names = ["Compilation Time", "Key Generation Time"]

    run_for_metrics(metrics, metric_names, results_path, [0])
