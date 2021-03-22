#!/usr/bin/python3
import json
import socket
import subprocess
import sys

import matplotlib.pyplot as plt

HOSTNAME = socket.gethostname()


def find_lowest_timestamp(results):
    lowest_timestamp = -1

    for result in results:
        if lowest_timestamp == -1 or lowest_timestamp > float(result[TIMESTAMP]):
            lowest_timestamp = float(result[TIMESTAMP])

    return lowest_timestamp


def get_server_nodes():
    cmd = 'kubectl get nodes --selector serversnode=true --template=\'{{range .items}}{{.metadata.name}}{{"\\n"}}{{ \
        end}}\''
    server_nodes = [node.strip() for node in subprocess.getoutput(cmd).split("\n")]

    return server_nodes


TIMESTAMP = "TIMESTAMP"
BITS_OUT = "BYTES_OUT"
BITS_IN = "BYTES_IN"
BITS_TOTAL = "BYTES_TOTAL"


def plot_bandwidth(experiment_dir):
    print("Plotting stats...")

    with open(f'{experiment_dir}/stats/{HOSTNAME}_bandwidth_results.json', 'r') as f:
        results = json.load(f)

    plt.figure(figsize=(25, 15))

    lowest_timestamp = find_lowest_timestamp(results)

    x_axis = []
    y_axis = []

    for result in results:
        x_axis.append(result[TIMESTAMP] - lowest_timestamp)
        y_axis.append(result[BITS_TOTAL] / 1_000_000)

    plt.plot(x_axis, y_axis, label=HOSTNAME)
    plt.ylabel("Megabits p/ second")
    plt.legend()
    plt.savefig(f'{experiment_dir}/plots/{HOSTNAME}_bandwidths.png')

    print("Done!")


def plot_cpu_and_mem(experiment_dir):
    results_path = f'{experiment_dir}/stats/{HOSTNAME}_cpu_mem.json'
    with open(results_path, 'r') as f:
        results = json.load(f)

    cpus = results['cpu']
    mems = results['mem']

    fig, ax1 = plt.subplots(figsize=(25, 15))

    color = 'blue'
    ax1.set_xlabel('seconds')
    ax1.set_ylabel('CPU (%)', color=color)
    ax1.set_ylim([0, 100])

    ax1.plot([int(key) for key in cpus.keys()], cpus.values(), color=color, label='cpu')
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()

    color = 'red'
    ax2.set_ylabel('Memory (GB)', color=color)
    ax2.plot([int(key) for key in mems.keys()], [value for value in mems.values()], color=color, label='memory')
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.set_ylim([0, 100])

    plt.legend()
    plt.savefig(f'{experiment_dir}/plots/{HOSTNAME}_cpu_mem_stats.png')


def main():
    args = sys.argv[1:]

    num_args = 1
    if len(args) != num_args:
        print("Usage: python3 plot_stats.py <experiment_dir>")
        exit(1)

    experiment_dir = args[0]

    plot_cpu_and_mem(experiment_dir)
    plot_bandwidth(experiment_dir)


if __name__ == '__main__':
    main()
