#!/usr/bin/python3
import json
import os
import socket
import subprocess

import matplotlib.pyplot as plt
import pandas
import sys
from icecream import ic

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


def plot_cpu_mem_stats(min_timestamp, experiment_dir, nodes, prefix):
    server_results = {}
    for node in nodes:
        results = pandas.read_csv(
            f'{experiment_dir}/stats/{node}_cpu_mem.csv', delimiter=';')
        server_results[node] = results

    plt.figure(figsize=(25, 15))
    plt.xlabel('seconds')
    plt.ylabel('CPU (%)')

    if min_timestamp == 0:
        for node, results in server_results.items():
            timestamp = results['timestamp'].min()
            if timestamp < min_timestamp or min_timestamp == 0:
                min_timestamp = timestamp

    for node, results in server_results.items():
        plt.plot(results['timestamp'].apply(lambda x: x -
                                                      min_timestamp), results['cpu'], label=node)

    prefix_dir = f'{experiment_dir}/plots/{prefix}'
    if not os.path.exists(prefix_dir):
        os.mkdir(prefix_dir)

    plt.ylim([0, 100])
    plt.legend()
    plt.grid()
    plt.savefig(f'{prefix_dir}/cpu_stats.png')

    plt.figure(figsize=(25, 15))
    plt.xlabel('seconds')
    plt.ylabel('MEMORY (%)')

    for node, results in server_results.items():
        plt.plot(results['timestamp'].apply(lambda x: x -
                                                      min_timestamp), results['mem'], label=node)

    plt.ylim([0, 100])
    plt.legend()
    plt.grid()
    plt.savefig(f'{prefix_dir}/mem_stats.png')


def plot_bandwidths(min_timestamp, experiment_dir, nodes, prefix):
    print("Plotting stats...")

    iface_header = 'iface_name'
    bits_header = 'bits_total_s'
    fixed_bits_header = 'fixed_bits_total_s'
    rolling_bits_header = 'rolling_bits_total_s'
    timestamp_header = 'timestamp'

    prefix_dir = f'{experiment_dir}/plots/{prefix}'
    if not os.path.exists(prefix_dir):
        os.mkdir(prefix_dir)

    interface_regex = r''
    if prefix == 'server_nodes':
        interface_regex = r'bwp'

    for node in nodes:
        plt.figure(figsize=(25, 15))

        file_path = f'{experiment_dir}/stats/{node}_bandwidth.csv'
        bandwidth_data = pandas.read_csv(file_path, delimiter=';')


        to_keep = bandwidth_data[iface_header].str.contains(
            interface_regex, regex=True)
        bandwidth_data = bandwidth_data[to_keep]
        bandwidth_data.index = pandas.to_datetime(
            bandwidth_data[timestamp_header], unit='s')
        bandwidth_data.index.name = None

        bandwidth_per_interface = bandwidth_data.groupby(iface_header,
                                                         as_index=False)

        if min_timestamp == 0:
            min_timestamp = bandwidth_data[timestamp_header].min()

        ifaces = bandwidth_data[iface_header].unique()

        for iface in ifaces:
            iface_bandwidth = bandwidth_per_interface.get_group(iface).copy()
            ic(iface_bandwidth)
            x = iface_bandwidth[timestamp_header].apply(
                lambda time: time - min_timestamp
            )

            iface_bandwidth[fixed_bits_header] = iface_bandwidth[bits_header].apply(
                lambda x: x / 1_000_000)
            ic(iface_bandwidth)

            iface_bandwidth[rolling_bits_header] = iface_bandwidth.rolling('2s').mean()[
                fixed_bits_header]
            ic(iface_bandwidth)

            y = iface_bandwidth[rolling_bits_header]
            plt.plot(x, y, label=f'{iface}_mean')

        image_path = f'{prefix_dir}/{node}_bandwidths.png'

        plt.grid()
        plt.ylabel("Megabits p/ second")
        plt.legend()
        plt.savefig(image_path)

        print(f'Wrote image to {image_path}')


def main():
    args = sys.argv[1:]

    max_num_args = 3
    if len(args) > max_num_args:
        print(
            "Usage: python3 plot_stats.py <experiment_dir> [--ts=min_timestamp] [--debug]")
        exit(1)

    experiment_dir = ""
    min_timestamp = 0
    debug = False

    for arg in args:
        if '--ts=' in arg:
            min_timestamp = float(arg.split('=')[1])
        elif '--debug' == arg:
            debug = True
        elif experiment_dir == "":
            experiment_dir = arg

    if debug:
        ic.enable()
    else:
        ic.disable()

    server_nodes_prefix = 'server_nodes'
    client_nodes_prefix = 'client_nodes'

    with open(f'{experiment_dir}/info.json', 'r') as f:
        info = json.load(f)

    nodes = info['nodes']

    server_nodes = nodes['server']
    client_nodes = nodes['client']

    plot_bandwidths(min_timestamp, experiment_dir,
                    server_nodes, server_nodes_prefix)
    plot_cpu_mem_stats(min_timestamp, experiment_dir,
                       server_nodes, server_nodes_prefix)

    plot_bandwidths(min_timestamp, experiment_dir,
                    client_nodes, client_nodes_prefix)
    plot_cpu_mem_stats(min_timestamp, experiment_dir,
                       client_nodes, client_nodes_prefix)


if __name__ == '__main__':
    main()
