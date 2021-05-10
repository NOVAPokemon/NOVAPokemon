#!/usr/local/bin/python3
import json
import os
import socket
import subprocess
import threading
from datetime import datetime

import sys
import time
import yaml

MAPS_DIR = os.path.expanduser(
    '~/go/src/github.com/bruno-anjos/cloud-edge-deployment/latency_maps')
NOVAPOKEMON_DIR = os.path.expanduser('~/go/src/github.com/NOVAPokemon')
SCRIPTS_DIR = f'{NOVAPOKEMON_DIR}/scripts'
CLIENT_SCENARIOS_DIR = os.path.expanduser('~/ced-client-scenarios')

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


def run_cmd_in_node(cmd, node):
    cmd = f'oarsh {node} "{cmd}"'
    run_with_log(cmd)


def run_in_node_with_fork(cmd, node):
    if node != hostname:
        cmd = f'oarsh {node} "{cmd}"'

    t = threading.Thread(target=run_with_log, args=(cmd,))
    t.start()

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


def build_novapokemon(race):
    print("Building NOVAPokemon...")

    cmd = f"bash {SCRIPTS_DIR}/build_service_images.sh{' -r' if race else ''}"
    run_with_log_and_exit(cmd)

    cmd = f"bash {SCRIPTS_DIR}/build_client.sh{' -r' if race else ''}"
    run_with_log_and_exit(cmd)

    print("Done!")


def start_cluster():
    print("Starting cluster...")

    cmd = f'bash {SCRIPTS_DIR}/install_kube_cluster.sh'
    run_with_log_and_exit(cmd)

    print("Done!")


def get_client_nodes():
    cmd = 'kubectl get nodes --selector clientsnode=true --template=\'{{range .items}}{{.metadata.name}}{{"\\n"}}{{ \
        end}}\''
    server_nodes = [node.strip()
                    for node in subprocess.getoutput(cmd).split("\n")]

    return server_nodes


def deploy_clients(scenario_name, cli_scenario):
    print("Deploying clients...")

    client_nodes = get_client_nodes()
    groups_per_client_node = {}

    for client_node in client_nodes:
        groups_per_client_node[client_node] = []

    index = 0
    for client_groups_name in cli_scenario:
        client_node = client_nodes[index % len(client_nodes)]
        groups_per_client_node[client_node].append(client_groups_name)
        index += 1

    client_threads = []
    for client_node, groups in groups_per_client_node.items():
        cmd = f'python3 {SCRIPTS_DIR}/launch_clients.py {scenario_name} {",".join(groups)}'
        t = run_in_node_with_fork(cmd, client_node)
        if t is not None:
            client_threads.append(t)

    print("Done!")

    return client_threads


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
    server_nodes = [node.strip()
                    for node in subprocess.getoutput(cmd).split("\n")]

    return server_nodes


def load_images(nodes):
    for node in nodes:
        if node != hostname:
            cmd = f'oarsh {node} {SCRIPTS_DIR}/load_images.sh'
            run_with_log_and_exit(cmd)


def start_recording(duration, time_between, experiment_dir, nodes):
    print(f"Will record for {duration} every {time_between} ...")

    threads_to_wait_for = []

    for node in nodes:
        cmd = f'python3 {SCRIPTS_DIR}/record_stats.py {time_between} {duration} {experiment_dir}'
        t = run_in_node_with_fork(cmd, node)
        if t is not None:
            threads_to_wait_for.append(t)

    print("Done!")

    return threads_to_wait_for


def create_experiment_dir(server_nodes, client_nodes, cli_scenario, experiment_scenario, bandwidth):
    date = datetime.now()
    timestamp = date.strftime("%m-%d-%H-%M")
    target_path = os.path.expanduser(f'~/experiment_{timestamp}')
    os.mkdir(target_path)

    print(f"Created dir {target_path}")

    os.mkdir(f'{target_path}/plots')
    os.mkdir(f'{target_path}/stats')

    with open(f'{target_path}/info.json', 'w') as f:
        info = {
            "nodes": {
                "server": server_nodes,
                "client": client_nodes
            },
            "clients_scenario": cli_scenario,
            "experiment_scenario": experiment_scenario,
            "bandwidth": bandwidth
        }

        json.dump(info, f, indent=4)

    return target_path


TIMESTAMP = "TIMESTAMP"
BITS_OUT = "BYTES_OUT"
BITS_IN = "BYTES_IN"
BITS_TOTAL = "BYTES_TOTAL"


def save_ingress_bandwidth(experiment_dir, bandwidth_annotations):
    with open(f'{experiment_dir}/bandwidths.json', 'w') as f:
        json.dump(bandwidth_annotations, f)


def get_ingress_bandwidth():
    ingress_filename = f'{NOVAPOKEMON_DIR}/deployment-chart/templates/ingress.yaml'
    with open(ingress_filename) as f:
        yaml_content = yaml.load(f, Loader=yaml.FullLoader)
    bandwidth_limits = yaml_content['metadata']['annotations']['ingress.appscode.com/annotations-pod']
    return json.loads(bandwidth_limits)


def find_lowest_timestamp(results):
    lowest_timestamp = -1

    for result in results:
        if lowest_timestamp == -1 or lowest_timestamp > float(result[TIMESTAMP]):
            lowest_timestamp = float(result[TIMESTAMP])

    return lowest_timestamp


def format_ingress():
    cmd = f'python3 {SCRIPTS_DIR}/format_ingress.py'
    run_with_log_and_exit(cmd)


def plot_stats(experiment_dir, min_timestamp):
    cmd = f'python3 {SCRIPTS_DIR}/plot_stats.py {experiment_dir} --ts={min_timestamp}'
    run_with_log_and_exit(cmd)

    cmd = f'python3 {SCRIPTS_DIR}/parse_logs.py {experiment_dir}/clients ' \
          f'{experiment_dir}/servers --output={experiment_dir}/plots --ts={min_timestamp}'
    run_with_log_and_exit(cmd)


def load_min_timestamp(experiment_dir):
    cmd = f'python3 {SCRIPTS_DIR}/get_experiment_min_timestamp.py {experiment_dir}'
    min_timestamp = float(subprocess.getoutput(cmd).strip())
    return min_timestamp


def stop_clients(client_nodes):
    cmd = 'killall multiclient; killall executable'
    for node in client_nodes:
        run_cmd_in_node(cmd, node)


def change_tc_qdisc():
    list_and_filter_rules_cmd = 'sudo-g5k tc qdisc show | grep tbf'
    output = subprocess.getoutput(list_and_filter_rules_cmd)
    rules = output.split('\n')
    bandwidth_limit = rules[0].split(' ')[9]
    interfaces = [rule.strip().split(' ')[4] for rule in rules]

    print(f'Got interfaces: {interfaces}')
    change_qdisc_cmd = 'sudo-g5k tc qdisc change dev {interface} handle 1: tbf rate {bandwidth} burst 1600 latency 1ms'
    for interface in interfaces:
        run_with_log_and_exit(change_qdisc_cmd.format(interface=interface, bandwidth=bandwidth_limit))

    print('Finished changing from tbf to htb')


def main():
    args = sys.argv[1:]
    num_args = 3

    if len(args) > num_args:
        print("Usage: python3 run_experiment.py <experiment.json>"
              "[--build-only] [--race]")
        exit(1)

    experiment_path = ""
    build_only = False
    race = False

    for arg in args:
        if arg == "--build-only":
            build_only = True
        elif arg == "--race":
            race = True
        elif experiment_path == "":
            experiment_path = args[0]

    server_nodes = get_server_nodes()
    client_nodes = get_client_nodes()

    with open(os.path.expanduser(experiment_path), 'r') as f:
        experiment = json.load(f)

    stop_cluster()

    extract_locations(experiment["scenario"])
    get_lats(experiment["deploy_opts"])

    nodes = get_nodes()
    print(f'Got nodes: {nodes}')

    build_novapokemon(race)
    load_images(nodes)

    if build_only:
        return

    client_scenario_name = experiment["clients_scenario"]
    with open(f'{CLIENT_SCENARIOS_DIR}/{client_scenario_name}') as f:
        cli_scenario = json.load(f)

    format_ingress()

    bandwidth = get_ingress_bandwidth()

    experiment_dir = create_experiment_dir(
        server_nodes, client_nodes, cli_scenario, experiment, bandwidth)

    save_ingress_bandwidth(experiment_dir, bandwidth)

    start_cluster()

    time_after_stack = experiment['time_after_stack']
    time_after_deploy = experiment['time_after_deploy']
    print(
        f"Sleeping {time_after_stack}+{time_after_deploy} after deploying stack...")
    sleep_time = process_time_string_in_sec(time_after_stack)
    time.sleep(sleep_time)
    sleep_time = process_time_string_in_sec(time_after_deploy)
    time.sleep(sleep_time)

    change_tc_qdisc()

    threads_to_wait = start_recording(
        experiment["duration"], experiment["time_between_snapshots"],
        experiment_dir, nodes)

    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    print(f'Launching clients at {current_time}')

    client_threads = deploy_clients(client_scenario_name, cli_scenario)

    duration = experiment['duration']
    sleep_time = process_time_string_in_sec(duration)

    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    print(f'Starting sleep at {current_time}')
    time.sleep(sleep_time)

    # wait for stats recording to finish
    time.sleep(60)

    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    print(f"Finished sleeping at {current_time}")

    stop_clients(client_nodes)

    for c_thread in client_threads:
        c_thread.join()

    save_logs(experiment_dir)

    for thread_to_wait in threads_to_wait:
        thread_to_wait.join()

    min_timestamp = load_min_timestamp(experiment_dir)

    plot_stats(experiment_dir, min_timestamp)


if __name__ == '__main__':
    main()
