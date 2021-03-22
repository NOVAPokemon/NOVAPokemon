# /usr/bin/python3
import os
import socket
import subprocess
import sys


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


def main():
    args = sys.argv[1:]
    num_args = 1

    if len(args) < num_args:
        print("Usage: python3 save_logs.py <experiment_dir>")
        exit(1)

    experiment_dir = os.path.expanduser(args[0])
    nodes = get_nodes()

    print("Saving logs...")

    elastic_logs_dir = '/tmp/logs_elastic'
    experiment_elastic_logs_dir = f'{experiment_dir}/logs_elastic'
    if not os.path.exists(experiment_elastic_logs_dir):
        os.mkdir(experiment_elastic_logs_dir)

    cmd = f'cp -r {elastic_logs_dir} {experiment_elastic_logs_dir}'
    run_with_log_and_exit(cmd)

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
            cmd = f'ssh {node} {cp_cmd}'
            run_with_log_and_exit(cmd)

    print("Done!")


if __name__ == '__main__':
    main()
