# /usr/bin/python3
import os
import socket
import subprocess
import sys
import yaml

NOVAPOKEMON_DIR = os.path.expanduser('~/go/src/github.com/NOVAPokemon')
DEPL_CHARTS_DIR = f'{NOVAPOKEMON_DIR}/deployment-chart'

SERVICES = ['authentication', 'battles', 'location', 'microtransactions',
            'notifications', 'store', 'trades', 'trainers']


def get_nodes():
    cmd = "kubectl get nodes -l clientsnode -o go-template --template='{{range .items}}{{.metadata.name}}{{\"\\n\"}}" \
          "{{end}}'"
    output = subprocess.getoutput(cmd)

    return output.split("\n")


def run_with_log_and_exit(cmd):
    print(f"RUNNING | {cmd}")
    ret = subprocess.run(cmd, shell=True)
    if ret.returncode != 0:
        print(f"{cmd} returned {ret.returncode}")
        exit(ret.returncode)


def save_client_logs(experiment_dir):
    nodes = get_nodes()

    client_logs_dir = "/tmp/client_logs"
    experiment_clients_dir = f'{experiment_dir}/clients/'

    if not os.path.exists(experiment_clients_dir):
        os.mkdir(experiment_clients_dir)

    cp_cmd = f'cp -r {client_logs_dir}/* {experiment_clients_dir}'
    if os.path.exists(client_logs_dir):
        run_with_log_and_exit(cp_cmd)

    hostname = socket.gethostname()
    for node in nodes:
        if node != hostname:
            cmd = f'oarsh {node} {cp_cmd}'
            run_with_log_and_exit(cmd)


def get_pod_logs(pod_name, server_logs_dir):
    cmd = f'kubectl logs {pod_name} > {server_logs_dir}/{pod_name}.log'
    run_with_log_and_exit(cmd)


def save_server_logs(experiment_dir):
    output = subprocess.getoutput(
        f'cd {DEPL_CHARTS_DIR} && helm template novapokemon . -f ./values.yaml')

    docs = yaml.safe_load_all(output)

    stateful_sets = []
    for doc in docs:
        if doc['kind'] == 'StatefulSet' and 'metadata' in doc and 'name' in doc['metadata'] and \
                doc['metadata']['name'] in SERVICES:
            stateful_sets.append(doc)

    replicas = {}
    for stateful_set in stateful_sets:
        name = stateful_set['metadata']['name']
        replicas[name] = stateful_set['spec']['replicas']

    server_logs_dir = f'{experiment_dir}/servers'
    if not os.path.exists(server_logs_dir):
        os.mkdir(server_logs_dir)

    for service, num_replicas in replicas.items():
        for i in range(num_replicas):
            get_pod_logs(f'{service}-{i}', server_logs_dir)


def main():
    args = sys.argv[1:]
    num_args = 1

    if len(args) < num_args:
        print("Usage: python3 save_logs.py <experiment_dir>")
        exit(1)

    experiment_dir = os.path.expanduser(args[0])

    print("Saving logs...")

    save_server_logs(experiment_dir)
    save_client_logs(experiment_dir)

    print("Done!")


if __name__ == '__main__':
    main()
