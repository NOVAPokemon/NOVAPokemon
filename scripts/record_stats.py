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
    file_path = f'{experiment_dir}/stats/{HOSTNAME}_bandwidth.csv'

    with open(file_path, 'w') as f:
        f.write('timestamp;iface_name;bytes_out_s;bytes_in_s;bytes_total_s;'
                'bytes_in;bytes_out;packets_out_s;packets_in_s;packets_total_s;'
                'packets_in;packets_out;errors_out_s;errors_in_s;errors_in;'
                'errors_out;bits_out_s;bits_in_s;bits_total_s;bits_in;'
                'bits_out\n')

    cmd = f'bwm-ng -t {interval * 1000} -o csv -c {count} -u bits -T rate ' \
          f'-F {file_path}'
    subprocess.run(cmd, shell=True)


def record_cpu_and_mem(interval, count, experiment_dir):
    psutil.cpu_percent()

    max_memory = psutil.virtual_memory().total

    values = {}

    i = 0
    while i < count:
        timestamp = time.time()
        time.sleep(interval)

        cpu, mem = get_stats()
        mem_per = (mem / max_memory) * 100
        values[timestamp] = (cpu, mem_per)
        i += 1

    results_path = f'{experiment_dir}/stats/{HOSTNAME}_cpu_mem.csv'
    with open(results_path, 'w') as f:
        f.write('timestamp;cpu;mem\n')
        for ts, (cpu, mem) in values.items():
            f.write(f'{ts};{cpu};{mem}\n')

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

    t = threading.Thread(target=record_bandwidth,
                         args=(interval, count, experiment_dir))
    t.start()

    record_cpu_and_mem(interval, count, experiment_dir)

    t.join()


if __name__ == '__main__':
    main()
