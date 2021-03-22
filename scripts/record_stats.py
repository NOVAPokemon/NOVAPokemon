#!/usr/bin/python3
import json
import os
import socket
import subprocess
import sys
import threading
import time

import psutil

HOSTNAME = socket.gethostname()

NOVAPOKEMON_DIR = os.path.expanduser('~/go/src/github.com/NOVAPokemon')
SCRIPTS_DIR = f'{NOVAPOKEMON_DIR}/scripts'


def get_stats():
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().used

    return cpu, mem


def process_time_string_in_sec(time_string):
    time_in_seconds = int(time_string[:-1])

    time_suffix = time_string[-1]
    if time_suffix == "m" or time_suffix == "M":
        time_in_seconds = time_in_seconds * 60
    elif time_suffix == "h" or time_suffix == "H":
        time_in_seconds = time_in_seconds * 60 * 60

    return time_in_seconds


TIMESTAMP = "TIMESTAMP"
BITS_OUT = "BYTES_OUT"
BITS_IN = "BYTES_IN"
BITS_TOTAL = "BYTES_TOTAL"


def record_bandwidth(interval, count, experiment_dir):
    cmd = f'bwm-ng -t {interval * 1000} -I cni0 -o csv -c {count} -u bits -T rate ' \
          f'-F {experiment_dir}/stats/{HOSTNAME}_bandwidth.csv'
    subprocess.run(cmd, shell=True)

    results = []
    with open(f"{experiment_dir}/stats/{HOSTNAME}_bandwidth.csv") as bandwidth_fp:
        measures = 0

        for line in bandwidth_fp.readlines():
            measures += 1
            splits = line.split(";")

            timestamp = float(splits[0])
            bits_out_s = float(splits[-5])
            bits_in_s = float(splits[-4])
            bits_total_s = float(splits[-3])

            results.append({
                TIMESTAMP: timestamp,
                BITS_OUT: bits_out_s,
                BITS_IN: bits_in_s,
                BITS_TOTAL: bits_total_s
            })

    results_path = f'{experiment_dir}/stats/{HOSTNAME}_bandwidth_results.json'
    with open(results_path, 'w') as results_fp:
        json.dump(results, results_fp, indent=4)

    print(f"Wrote bandwidth results to {results_path}!")


def record_cpu_and_mem(interval, count, experiment_dir):
    psutil.cpu_percent()

    cpus, mems = {}, {}

    max_memory = psutil.virtual_memory().total

    i = 0
    while i < count:
        timestamp = i * interval
        time.sleep(interval)

        cpu, mem = get_stats()
        cpus[timestamp] = cpu
        mems[timestamp] = (mem / max_memory) * 100

        i += 1

    results = {'cpu': cpus, 'mem': mems}

    results_path = f'{experiment_dir}/stats/{HOSTNAME}_cpu_mem.json'
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=4)

    print(f"Wrote CPU/MEM results to {results_path}")


def main():
    args = sys.argv[1:]

    num_args = 3
    if len(args) != num_args:
        print('Usage: python3 record_stats.py <interval> <duration> <experiment_dir>')
        exit(1)

    interval = process_time_string_in_sec(args[0])
    duration = process_time_string_in_sec(args[1])
    experiment_dir = os.path.expanduser(args[2])

    count = duration // interval

    t = threading.Thread(target=record_bandwidth, args=(interval, count, experiment_dir))
    t.start()

    record_cpu_and_mem(interval, count, experiment_dir)

    t.join()

    subprocess.run(f'python3 {SCRIPTS_DIR}/plot_stats.py {experiment_dir}', shell=True)


if __name__ == '__main__':
    main()
