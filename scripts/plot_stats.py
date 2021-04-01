#!/usr/bin/python3
import json
import socket
import subprocess
import sys
import os
import pandas

import matplotlib.pyplot as plt

HOSTNAME = socket.gethostname()
IGNORED_INTERFACES = ['lo', 'eno0', 'en1']


def find_lowest_timestamp(results):
    lowest_timestamp = -1

    for result in results:
        if lowest_timestamp == -1 or lowest_timestamp > float(result[TIMESTAMP]):
            lowest_timestamp = float(result[TIMESTAMP])

    return lowest_timestamp


def get_server_nodes():
    cmd = 'kubectl get nodes --selector serversnode=true --template=\'{{range .items}}{{.metadata.name}}{{"\\n"}}{{ \
        end}}\''
    server_nodes = [node.strip()
                    for node in subprocess.getoutput(cmd).split("\n")]

    return server_nodes


TIMESTAMP = "TIMESTAMP"
BITS_OUT = "BYTES_OUT"
BITS_IN = "BYTES_IN"
BITS_TOTAL = "BYTES_TOTAL"


def plot_cpu_mem_stats(experiment_dir, nodes, prefix):
    server_results = {}
    for node in nodes:
        with open(f'{experiment_dir}/stats/{node}_cpu_mem.json', 'r') as f:
            results = json.load(f)
        server_results[node] = results

    plt.figure(figsize=(25, 15))
    plt.xlabel('seconds')
    plt.ylabel('CPU (%)')

    for node, results in server_results.items():
        cpus = results['cpu']

        plt.plot([int(time) for time in cpus.keys()],
                 cpus.values(), label=node)

    plt.ylim([0, 100])
    plt.legend()
    plt.grid()
    plt.savefig(f'{experiment_dir}/plots/cpu_stats.png')

    plt.figure(figsize=(25, 15))
    plt.xlabel('seconds')
    plt.ylabel('MEMORY (%)')

    for node, results in server_results.items():
        mems = results['mem']

        plt.plot([int(mem) for mem in mems.keys()], mems.values(), label=node)

    prefix_dir = f'{experiment_dir}/plots/{prefix}'
    if not os.path.exists(prefix_dir):
        os.mkdir(prefix_dir)

    plt.ylim([0, 100])
    plt.legend()
    plt.grid()
    plt.savefig(f'{prefix_dir}/mem_stats.png')


def plot_bandwidths(experiment_dir, nodes, prefix):
    print("Plotting stats...")

    iface_header = 'iface_name'
    bits_header = 'bits_total_s'
    timestamp_header = 'timestamp'

    prefix_dir = f'{experiment_dir}/plots/{prefix}'
    if not os.path.exists(prefix_dir):
        os.mkdir(prefix_dir)

    for node in nodes:
        plt.figure(figsize=(25, 15))

        file_path = f'{experiment_dir}/stats/{node}_bandwidth.csv'
        bandwidth_data = pandas.read_csv(file_path, delimiter=';')
        to_keep = bandwidth_data[iface_header].str.match('bond0')
        bandwidth_data = bandwidth_data[to_keep]

        bandwidth_per_interface = bandwidth_data.groupby(iface_header)

        min_timestamp = bandwidth_data[timestamp_header].min()

        print(min_timestamp)

        ifaces = bandwidth_data[iface_header].unique()

        for iface in ifaces:
            x = bandwidth_per_interface.get_group(iface)[timestamp_header].apply(
                lambda time: time - min_timestamp
            )
            y = bandwidth_per_interface.get_group(iface)[bits_header].apply(
                lambda val: val / 1_000_000
            )
            plt.plot(x, y, label=iface)

        image_path = f'{prefix_dir}/{node}_bandwidths.png'

        plt.grid()
        plt.ylabel("Megabits p/ second")
        plt.legend()
        plt.savefig(image_path)

        print(f'Wrote image to {image_path}')


def main():
    args = sys.argv[1:]

    num_args = 1
    if len(args) != num_args:
        print("Usage: python3 plot_stats.py <experiment_dir>")
        exit(1)

    experiment_dir = args[0]

    server_nodes_prefix = 'server_nodes'
    client_nodes_prefix = 'client_nodes'

    with open(f'{experiment_dir}/nodes.json', 'r') as f:
        nodes = json.load(f)

    server_nodes = nodes['server']
    client_nodes = nodes['client']

    plot_bandwidths(experiment_dir, server_nodes, server_nodes_prefix)
    plot_cpu_mem_stats(experiment_dir, server_nodes, server_nodes_prefix)

    plot_bandwidths(experiment_dir, client_nodes, client_nodes_prefix)
    plot_cpu_mem_stats(experiment_dir, client_nodes, client_nodes_prefix)


if __name__ == '__main__':
    main()
