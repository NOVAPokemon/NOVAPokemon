#!/usr/bin/python3
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from multiprocessing import Pool

NOVAPOKEMON_DIR = os.path.expanduser('~/go/src/github.com/NOVAPokemon')
CLI_DIR = f'{NOVAPOKEMON_DIR}/client'
CLI_SCENARIOS_PATH = os.path.expanduser('~/ced-client-scenarios')
CLI_TEMPLATE = f'{CLI_DIR}/client-jobs-template.yaml'
CLI_LOGS_DIR = f'/tmp/client_logs'
CLI_FILES_DIR = f'/tmp/files'
CLI_CHARTS_DIR = f'{CLI_DIR}/client_group_charts'

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


def get_client_nodes():
    cmd = "kubectl get nodes -l clientsnode -o go-template " \
        "--template='{{range .items}}{{.metadata.name}}{{\"\\n\"}}{{end}}'"

    return [node.strip() for node in subprocess.getoutput(cmd).split("\n")]


def setup_client_node_dirs(cli_scenario):
    print("Will setup client dirs...")

    client_nodes = get_client_nodes()

    for node in client_nodes:
        clean_dir_or_create_on_node(CLI_LOGS_DIR, node)
        clean_dir_or_create_on_node(CLI_FILES_DIR, node)

        for cli_job_name in cli_scenario:
            group_logs_dir = f'{CLI_LOGS_DIR}/{cli_job_name}'
            clean_dir_or_create_on_node(group_logs_dir, node)


def launch_cli_job(cli_job_name, cli_job, env_vars):
    time.sleep(process_time_string(cli_job[DICT_WAIT_TIME]))

    env_vars['REGION'] = cli_job[DICT_REGION]
    env_vars['CLIENTS_TIMEOUT'] = cli_job[DICT_TIMEOUT]
    env_vars['NUM_CLIENTS'] = cli_job[DICT_NUM_CLI]
    env_vars['LOGS_DIR'] = f'{CLI_LOGS_DIR}/{cli_job_name}'

    spread_env_vars = []
    for var_id, var_value in env_vars.items():
        spread_env_vars.append(f'{var_id}={var_value}')

    cmd = f'sh -c "{NOVAPOKEMON_DIR}/client/multiclient"'
    subprocess.run(f'{" ".join(spread_env_vars)} {cmd}', shell=True)


# AUX FUNCTIONS

def clean_dir_or_create(path):
    if os.path.exists(path):
        shutil.rmtree(path)

    os.mkdir(path)


def clean_dir_or_create_on_node(path, node):
    if socket.gethostname() == node:
        clean_dir_or_create(path)
    else:
        cmd = f'ssh {node} \"(rm -rf {path} && mkdir {path}) || mkdir {path}\"'
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


def get_ingress_port():
    cmd = 'kubectl get service/voyager-novapokemon-ingress ' \
        '--template=\'{{index .spec.ports 0 "nodePort"}}\''

    return subprocess.getoutput(cmd).strip()


def get_ingress_hostname():
    cmd = 'kubectl get node -l node-role.kubernetes.io/master= ' \
        '--template=\'{{index .items 0 "metadata" "name"}}\''

    return subprocess.getoutput(cmd).strip()


def get_ingress():
    port = get_ingress_port()
    hostname = get_ingress_hostname()
    return f'{hostname}:{port}'


def build_clients():
    cmd = f'bash {NOVAPOKEMON_DIR}/scripts/build_client.sh'
    subprocess.run(cmd, shell=True)


def main():
    num_args = 1

    args = sys.argv[1:]
    if len(args) != num_args:
        print("Usage: python3 launch_clients.py <client-scenario.json>")
        exit(1)

    build_clients()

    client_scenario_filename = args[0]
    with open(f"{CLI_SCENARIOS_PATH}/{client_scenario_filename}", 'r') as cli_scenario_fp:
        cli_scenario = json.load(cli_scenario_fp)

    print(f"Launching scenario: {client_scenario_filename}")

    setup_client_node_dirs(cli_scenario)

    ingress = get_ingress()

    env_vars = {
        "AUTHENTICATION_URL": ingress,
        "BATTLES_URL": ingress,
        "GYM_URL": ingress,
        "LOCATION_URL": ingress,
        "MICROTRANSACTIONS_URL": ingress,
        "NOTIFICATIONS_URL": ingress,
        "STORE_URL": ingress,
        "TRADES_URL": ingress,
        "TRAINERS_URL": ingress,
        "INGRESS_URL": ingress,
        "NOVAPOKEMON": NOVAPOKEMON_DIR,
        "LOCATION_TAGS": f'{CLI_DIR}/location_tags.json',
        "DELAYS_CONFIG": f'{CLI_DIR}/delays_config.json',
        "CLIENT_DELAYS": f'{CLI_DIR}/client_delays.json',
        "CELLS_TO_REGION": f'{CLI_DIR}/cells_to_region.json',
        "REGIONS_TO_AREA": f'{CLI_DIR}/regions_to_area.json',
        "CONFIGS": f'{CLI_DIR}/configs.json',
        "LAT": f'{CLI_DIR}/lat.txt',
        "LOCATIONS": f'{CLI_DIR}/locations.json'
    }

    pool = Pool(processes=os.cpu_count())

    async_waits = []
    for cli_job_name, cli_job in cli_scenario.items():
        print(f'Launching {cli_job_name}...')
        async_waits.append(pool.apply_async(
            launch_cli_job, (cli_job_name, cli_job, env_vars)))

    for w in async_waits:
        w.get()

    pool.terminate()
    pool.close()


if __name__ == '__main__':
    main()
