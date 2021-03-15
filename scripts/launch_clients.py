#!/usr/bin/python3
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from multiprocessing import Pool

NUM_ARGS = 1

NOVAPOKEMON_DIR = os.path.expanduser('~/go/src/github.com/NOVAPokemon')
CLI_SCENARIOS_PATH = os.path.expanduser('~/ced-client-scenarios')
CLI_TEMPLATE = f'{NOVAPOKEMON_DIR}/client/client-jobs-template.yaml'
CLI_LOGS_DIR = f'/tmp/client_logs'
CLI_SERVICES_DIR = f'/tmp/services'
CLI_CHARTS_DIR = f'{NOVAPOKEMON_DIR}/client/client_group_charts'

VAR_IMAGE_NAME = "VAR_IMAGE_NAME"
VAR_CLIENT_NUM = "VAR_CLIENT_NUMS"
VAR_REGION = "VAR_REGION"
VAR_LOGS_HOST_PATH = "VAR_LOGS_HOST_PATH"
VAR_SERVICES_HOST_PATH = "VAR_SERVICES_HOST_PATH"
VAR_CLI_TIMEOUT = "VAR_CLIENTS_TIMEOUT"

DICT_NUM_CLI = "number_of_clients"
DICT_REGION = "region"
DICT_TIMEOUT = "duration"
DICT_WAIT_TIME = "wait_time"


def main():
    args = sys.argv[1:]
    if len(args) != NUM_ARGS:
        print("Usage: python3 launch_clients.py <client-scenario.json>")
        exit(1)

    client_scenario_filename = args[0]
    with open(f"{CLI_SCENARIOS_PATH}/{client_scenario_filename}.json", 'r') as cli_scenario_fp:
        cli_scenario = json.load(cli_scenario_fp)

    setup_client_node_dirs(cli_scenario)
    create_job_templates(cli_scenario)

    pool = Pool(processes=os.cpu_count())

    async_waits = []
    for cli_job_name, cli_job in cli_scenario.items():
        print(f'Launching {cli_job_name}...')
        async_waits.append(pool.apply_async(launch_cli_job, (cli_job_name, cli_job)))

    for w in async_waits:
        w.get()

    pool.terminate()
    pool.close()


def setup_client_node_dirs(cli_scenario):
    clients_node = get_client_kube_node()

    clean_dir_or_create_on_node(CLI_LOGS_DIR, clients_node)
    clean_dir_or_create_on_node(CLI_SERVICES_DIR, clients_node)

    for cli_job_name in cli_scenario:
        group_logs_dir = f'{CLI_LOGS_DIR}/{cli_job_name}'
        clean_dir_or_create_on_node(group_logs_dir, clients_node)
        group_services_dir = f'{CLI_SERVICES_DIR}/{cli_job_name}'
        clean_dir_or_create_on_node(group_services_dir, clients_node)


def create_job_templates(cli_scenario):
    clean_dir_or_create(CLI_CHARTS_DIR)
    for cli_job_name, cli_job in cli_scenario.items():
        group_num = cli_job_name.split("_")[1]
        number_clients = cli_job[DICT_NUM_CLI]
        region = cli_job[DICT_REGION]
        timeout = cli_job[DICT_TIMEOUT]
        group_logs_dir = f'{CLI_LOGS_DIR}/{cli_job_name}'
        group_services_dir = f'{CLI_SERVICES_DIR}/{cli_job_name}'

        group_chart_name = f'{CLI_CHARTS_DIR}/{cli_job_name}_chart.yaml'

        sed_cmd = f'sed "s/{VAR_IMAGE_NAME}/clients-{group_num}-{number_clients}/" {CLI_TEMPLATE} |' \
                  f'sed "s/{VAR_CLIENT_NUM}/{number_clients}/" |' \
                  f'sed "s/{VAR_REGION}/{region}/" |' \
                  f'sed "s/{VAR_CLI_TIMEOUT}/{timeout}/" |' \
                  f'sed "s|{VAR_LOGS_HOST_PATH}|{group_logs_dir}|" |' \
                  f'sed "s|{VAR_SERVICES_HOST_PATH}|{group_services_dir}|" >{group_chart_name}'

        run_with_log_and_exit(sed_cmd)

        print(f'Finished setup for {cli_job_name}!')


def launch_cli_job(cli_job_name, cli_job):
    time.sleep(process_time_string(cli_job[DICT_WAIT_TIME]))

    cli_chart = f'{CLI_CHARTS_DIR}/{cli_job_name}_chart.yaml'
    launch_cmd = f'kubectl apply -f {cli_chart}'

    run_with_log_and_exit(launch_cmd)


# AUX FUNCTIONS

def clean_dir_or_create(path):
    if os.path.exists(path):
        shutil.rmtree(path)

    os.mkdir(path)


def clean_dir_or_create_on_node(path, node):
    if socket.gethostname() == node:
        clean_dir_or_create(path)
    else:
        cmd = f'ssh {node} "(rm -rf {path} && mkdir {path}) || mkdir {path}"'
        run_with_log_and_exit(cmd)


def run_with_log_and_exit(cmd):
    print(f"RUNNING | {cmd}")
    ret = subprocess.run(cmd, shell=True)
    if ret.returncode != 0:
        exit(ret.returncode)


def process_time_string(time_string):
    time_in_seconds = int(time_string[:-1])

    time_suffix = time_string[-1]
    if time_suffix == "m" or time_suffix == "M":
        time_in_seconds = time_in_seconds * 60
    elif time_suffix == "h" or time_suffix == "H":
        time_in_seconds = time_in_seconds * 60 * 60

    return time_in_seconds


def get_client_kube_node():
    cmd = "kubectl get nodes -l clientsnode -o go-template --template='{{range .items}}{{.metadata.name}}{{\"\\n\"}}" \
          "{{end}}'"

    return subprocess.getoutput(cmd).strip()


if __name__ == '__main__':
    main()
