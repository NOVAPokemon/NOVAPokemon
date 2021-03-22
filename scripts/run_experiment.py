#!/usr/bin/python3
import json
import os
import socket
import subprocess
import sys
import threading
import time
from datetime import datetime

import matplotlib.pyplot as plt

MAPS_DIR = os.path.expanduser('~/go/src/github.com/bruno-anjos/cloud-edge-deployment/latency_maps')
NOVAPOKEMON_DIR = os.path.expanduser('~/go/src/github.com/NOVAPokemon')
SCRIPTS_DIR = f'{NOVAPOKEMON_DIR}/scripts'

hostname = socket.gethostname()


def run_with_log_and_exit(cmd):
    print(f"RUNNING | {cmd}")
    ret = subprocess.run(cmd, shell=True)
    if ret.returncode != 0:
        print(f"{cmd} returned {ret.returncode}")
        exit(ret.returncode)


def run_with_log(cmd):
    print(f"RUNNING | {cmd}")
    subprocess.run(cmd, shell=True)


def run_in_node_with_fork(cmd, node):
    t = None
    if node == hostname:
        t = threading.Thread(target=run_with_log, args=(cmd,))
        t.start()
    else:
        ssh_cmd = f'ssh -f {node} "{cmd}"'
        run_with_log(ssh_cmd)

    return t


def extract_locations(scenario):
    print("Extracting locations...")

    cmd = f'python3 {SCRIPTS_DIR}/extract_locations_from_scenario.py {scenario}'
    run_with_log_and_exit(cmd)

    print("Done!")


def get_lats(deploy_opts):
    splitted_opts = deploy_opts.split(" ")

    found = False
    mapname = ""

    for i, opt in enumerate(splitted_opts):
        if opt == "--mapname":
            mapname = splitted_opts[i + 1]
            found = True

    if not found:
        print("missing mapname in deploy opts")
        exit(1)

    print(f"Getting map {mapname} lats...")

    cmd = f'cp {MAPS_DIR}/{mapname}/lat.txt {NOVAPOKEMON_DIR}/lat.txt'
    run_with_log_and_exit(cmd)

    print("Done!")


def stop_cluster():
    print("Stopping cluster...")

    cmd = f'bash {SCRIPTS_DIR}/stop_kube_cluster.sh'
    run_with_log_and_exit(cmd)

    print("Done!")


def build_novapokemon():
    print("Building NOVAPokemon...")

    cmd = f"bash {SCRIPTS_DIR}/build_service_images.sh -r"
    run_with_log_and_exit(cmd)

    cmd = f"bash {SCRIPTS_DIR}/build_client.sh -r"
    run_with_log_and_exit(cmd)

    print("Done!")


def start_cluster():
    print("Starting cluster...")

    cmd = f'bash {SCRIPTS_DIR}/install_kube_cluster.sh'
    run_with_log_and_exit(cmd)

    print("Done!")


def deploy_clients(client_scenario):
    print("Deploying clients...")

    cmd = f'python3 {SCRIPTS_DIR}/launch_clients.py {client_scenario}'
    run_with_log_and_exit(cmd)

    print("Done!")


def save_logs(experiment_dir):
    print("Saving logs...")

    cmd = f'python3 {NOVAPOKEMON_DIR}/scripts/save_logs.py {experiment_dir}'
    run_with_log_and_exit(cmd)

    print("Done!")


def process_time_string_in_sec(time_string):
    time_in_seconds = int(time_string[:-1])

    time_suffix = time_string[-1]
    if time_suffix == "m" or time_suffix == "M":
        time_in_seconds = time_in_seconds * 60
    elif time_suffix == "h" or time_suffix == "H":
        time_in_seconds = time_in_seconds * 60 * 60

    return time_in_seconds


def get_nodes():
    cmd = "kubectl get nodes -o go-template --template='{{range .items}}{{.metadata.name}}{{\"\\n\"}}" \
          "{{end}}'"
    output = subprocess.getoutput(cmd)

    return [node.strip() for node in output.split("\n")]


def get_server_nodes():
    cmd = 'kubectl get nodes --selector serversnode=true --template=\'{{range .items}}{{.metadata.name}}{{"\\n"}}{{ \
        end}}\''
    server_nodes = [node.strip() for node in subprocess.getoutput(cmd).split("\n")]

    return server_nodes


def get_client_nodes():
    cmd = 'kubectl get nodes --selector clientsnode=true --template=\'{{range .items}}{{.metadata.name}}{{"\\n"}}{{ \
        end}}\''
    server_nodes = [node.strip() for node in subprocess.getoutput(cmd).split("\n")]

    return server_nodes


def load_images(nodes):
    for node in nodes:
        if node != hostname:
            cmd = f'ssh {node} {SCRIPTS_DIR}/load_images.sh'
            run_with_log_and_exit(cmd)


def start_recording(duration, time_between, experiment_dir, nodes):
    print(f"Will record for {duration} every {time_between} ...")

    threads_to_wait_for = []

    for client_node in nodes:
        cmd = f'python3 {SCRIPTS_DIR}/record_stats.py {time_between} {duration} {experiment_dir}'
        t = run_in_node_with_fork(cmd, client_node)
        if t is not None:
            threads_to_wait_for.append(t)

    print("Done!")

    return threads_to_wait_for


def create_experiment_dir():
    date = datetime.now()
    timestamp = date.strftime("%m-%d-%H-%M")
    target_path = os.path.expanduser(f'~/experiment_{timestamp}')
    os.mkdir(target_path)

    print(f"Created dir {target_path}")

    os.mkdir(f'{target_path}/plots')
    os.mkdir(f'{target_path}/stats')

    return target_path


TIMESTAMP = "TIMESTAMP"
BITS_OUT = "BYTES_OUT"
BITS_IN = "BYTES_IN"
BITS_TOTAL = "BYTES_TOTAL"


def find_lowest_timestamp(results):
    lowest_timestamp = -1

    for result in results:
        if lowest_timestamp == -1 or lowest_timestamp > float(result[TIMESTAMP]):
            lowest_timestamp = float(result[TIMESTAMP])

    return lowest_timestamp


def plot_bandwidths(experiment_dir, nodes, prefix):
    print("Plotting stats...")

    server_results = {}
    for node in nodes:
        with open(f'{experiment_dir}/stats/{node}_bandwidth_results.json', 'r') as f:
            results = json.load(f)
            server_results[node] = results

    min_timestamp = 0.
    for server, results in server_results.items():
        lowest_timestamp = find_lowest_timestamp(results)
        if lowest_timestamp < min_timestamp:
            min_timestamp = lowest_timestamp

    plt.figure(figsize=(25, 15))

    for node in nodes:
        x_axis = []
        y_axis = []

        for i, result in enumerate(server_results[node]):
            x_axis.append(result[TIMESTAMP] - min_timestamp)
            y_axis.append(result[BITS_TOTAL] / 1_000_000)

        plt.plot(x_axis, y_axis, label=node)

    prev_len = -1
    for node in nodes:
        curr_len = len(server_results[node])
        if prev_len != -1 and curr_len != prev_len:
            print("!different lengths!")
            prev_len = min(prev_len, curr_len)

    all_results = []
    for node in nodes:
        for i, result in enumerate(server_results[node]):
            if i == prev_len:
                break
            if len(all_results) < i + 1:
                all_results.append({
                    TIMESTAMP: result[TIMESTAMP],
                    BITS_TOTAL: result[BITS_TOTAL]
                })
            else:
                all_results[i][BITS_TOTAL] += result[BITS_TOTAL]

    x_axis = []
    y_axis = []

    for result in all_results:
        x_axis.append(result[TIMESTAMP] - min_timestamp)
        y_axis.append(result[BITS_TOTAL] / 1_000_000)

    plt.plot(x_axis, y_axis, label='all')

    prefix_dir = f'{experiment_dir}/plots/{prefix}'
    if not os.path.exists(prefix_dir):
        os.mkdir(prefix_dir)

    plt.ylabel("Megabits p/ second")
    plt.legend()
    plt.savefig(f'{prefix_dir}/bandwidths.png')

    print("Done!")


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

        plt.plot(cpus.keys(), cpus.values(), label=node)

    plt.ylim([0, 100])
    plt.legend()
    plt.savefig(f'{experiment_dir}/plots/cpu_stats.png')

    plt.figure(figsize=(25, 15))
    plt.xlabel('seconds')
    plt.ylabel('MEMORY (%)')

    for node, results in server_results.items():
        mems = results['mem']

        plt.plot(mems.keys(), mems.values(), label=node)

    prefix_dir = f'{experiment_dir}/{prefix}'
    if not os.path.exists(prefix_dir):
        os.mkdir(prefix_dir)

    plt.ylim([0, 100])
    plt.legend()
    plt.savefig(f'{prefix_dir}/plots/mem_stats.png')


def main():
    args = sys.argv[1:]
    num_args = 3

    if len(args) > num_args:
        print("Usage: python3 run_experiment.py <experiment.json> [--stats-only experiment_dir]")
        exit(1)

    stats_only = False
    experiment_dir = ""
    experiment_path = ""

    skip = False

    for i, arg in enumerate(args):
        if skip:
            skip = False
            continue
        if arg == "--stats-only":
            stats_only = True
            experiment_dir = os.path.expanduser(args[i + 1])
            skip = True
        elif experiment_path == "":
            experiment_path = args[0]

    server_nodes = get_server_nodes()
    client_nodes = get_client_nodes()

    server_nodes_prefix = 'server_nodes'
    client_nodes_prefix = 'client_nodes'

    if stats_only:
        plot_bandwidths(experiment_dir, server_nodes, server_nodes_prefix)
        plot_cpu_mem_stats(experiment_dir, server_nodes, server_nodes_prefix)

        plot_bandwidths(experiment_dir, client_nodes, client_nodes_prefix)
        plot_cpu_mem_stats(experiment_dir, client_nodes, client_nodes_prefix)

        return

    with open(os.path.expanduser(experiment_path), 'r') as f:
        experiment = json.load(f)

    stop_cluster()

    extract_locations(experiment["scenario"])
    get_lats(experiment["deploy_opts"])

    nodes = get_nodes()
    print(f'Got nodes: {nodes}')

    build_novapokemon()
    load_images(nodes)

    experiment_dir = create_experiment_dir()

    start_cluster()

    time_after_stack = experiment['time_after_stack']
    time_after_deploy = experiment['time_after_deploy']
    print(f"Sleeping {time_after_stack}+{time_after_deploy} after deploying stack...")
    sleep_time = process_time_string_in_sec(time_after_stack)
    time.sleep(sleep_time)
    sleep_time = process_time_string_in_sec(time_after_deploy)
    time.sleep(sleep_time)

    threads_to_wait = start_recording(experiment["duration"], experiment["time_between_snapshots"], experiment_dir,
                                      nodes)

    cli_thread = threading.Thread(target=deploy_clients, args=(experiment["clients_scenario"],))
    cli_thread.start()

    duration = experiment['duration']
    sleep_time = process_time_string_in_sec(duration)
    time.sleep(sleep_time)

    # wait for stats recording to finish
    time.sleep(60)

    save_logs(experiment_dir)

    plot_bandwidths(experiment_dir, server_nodes, server_nodes_prefix)
    plot_cpu_mem_stats(experiment_dir, server_nodes, server_nodes_prefix)

    plot_bandwidths(experiment_dir, client_nodes, client_nodes_prefix)
    plot_cpu_mem_stats(experiment_dir, client_nodes, client_nodes_prefix)

    for thread_to_wait in threads_to_wait:
        thread_to_wait.join()

    cli_thread.join()


if __name__ == '__main__':
    main()
