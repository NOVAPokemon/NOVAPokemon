import json
import os
import sys
from multiprocessing import Pool

import matplotlib.pyplot as plt

INFO_HEADER = "-----------------"

# FILE INFO
CLIENT_NAME = "client_name"
PATH = "path"

# RESULT FIELDS
MSG_TYPE = "type"
TIME_SENT = "time_sent"
TIME_RECV = "time_recv"
TIME_TOOK = "time_took"
ID = "msg_id"
EMMITTER = "emitter"
REMOTE = "remote"
SERVER = "server"

# MERGED RESULT FIELDS
SERVICE = "service"
SUM_TIME_TOOK = "time_took"
NUM_ENTRIES = "num_entries"

ignored = {
    "START_BATTLE",
    "REJECT_BATTLE",
    "START_TRADE",
    "REJECT_TRADE",
}

msg_type_to_service = {
    "START_BATTLE": "battles",
    "STATUS": "battles",
    "REMOVE_ITEM": "battles",
    "UPDATE_POKEMON": "battles",
    "SELECT_POKEMON": "battles",
    "ERROR_BATTLE": "battles",
    "REJECT_BATTLE": "battles",
    "CHALLENGE": "battles",
    "ATTACK": "battles",
    "DEFEND": "battles",
    "USE_ITEM": "battles",
    "QUEUE": "battles",

    "SERVERS_RESPONSE": "location",
    "CELLS_RESPONSE": "location",
    "GYMS": "location",
    "POKEMON": "location",
    "CATCH_POKEMON_RESPONSE": "location",
    "TILES_RESPONSE": "location",
    "UPDATE_LOCATION": "location",

    "START_TRADE": "trades",
    "JOIN_TRADE": "trades",
    "UPDATE_TRADE": "trades",
    "REJECT_TRADE": "trades",
    "CREATE_TRADE": "trades",
    "TRADE": "trades",
    "ACCEPT": "trades",
}

plots_dir = os.path.expanduser('~/plots')


def main():
    args = sys.argv[1:]
    max_args = 4
    min_args = 1
    if len(args) < min_args or len(args) > max_args:
        print("usage: parse_logs.py <client_logs_folder> [--only-one] [--print=trades,battles] [--dummy-infos="
              "/tmp/dummy_infos.json]")
        sys.exit(1)

    logs_folder = ""
    only_one = False
    print_list = []
    dummy_infos_path = ""

    for arg in args:
        if arg == "--only-one":
            only_one = True
        elif "--print" in arg:
            print_list = arg.split("=")[1].split(",")
        elif "--dummy-infos" in arg:
            dummy_infos_path = os.path.expanduser(arg.split("=")[1])
            print(f"dummy_infos set to {dummy_infos_path}")
        elif logs_folder == "":
            logs_folder = arg

    if not os.path.exists(plots_dir):
        os.mkdir(plots_dir)

    files = get_files_to_parse(logs_folder, only_one)

    dummy_infos = {}
    ips_to_nodes = {}
    if dummy_infos_path == "":
        dummy_infos_path = '/tmp/dummy_infos.json'

    if os.path.exists(dummy_infos_path):
        with open(dummy_infos_path, 'r') as dummy_infos_fp:
            infos = json.load(dummy_infos_fp)
            for info in infos:
                dummy_infos[info["name"]] = info
                ips_to_nodes[info["ip"]] = info["name"]

    results = {}
    print("\n{} PARSING FILES {}\n".format(INFO_HEADER * 2, INFO_HEADER * 2))

    emitted = {}

    for file in files:
        emitted = parse_file_for_emits(file, emitted)

    for file in files:
        results[file[CLIENT_NAME]] = parse_file_for_results(file, print_list, ips_to_nodes, emitted)

    with open(os.path.expanduser('~/logs_results.json'), 'w') as results_fp:
        json.dump(results, results_fp)

    process_results(results)


def add_entry_if_missing(receiver, key, time_took):
    if key not in receiver:
        receiver[key] = {
            SUM_TIME_TOOK: time_took,
            NUM_ENTRIES: 1
        }
    else:
        value = receiver[key]
        value[SUM_TIME_TOOK] += time_took
        value[NUM_ENTRIES] += 1


def sort_axis(x_axis, y_axis):
    lists = sorted(zip(*[x_axis, y_axis]))
    new_x, new_y = list(zip(*lists))
    return new_x, new_y


def normalize_x_axis(result):
    return (int(result[TIME_RECV]) - MIN_TIMESTAMP) / 1000


def plot_avg_latency_for_clients(all_results):
    print("Plotting average latency for clients...")

    measurements = 0

    for client_name, (results_per_server, _) in all_results.items():
        x_axis = []
        y_axis = []

        for _, results in results_per_server.items():
            for result in results:
                x_axis.append(normalize_x_axis(result))
                y_axis.append(result[TIME_TOOK])

        new_x, new_y = sort_axis(x_axis, y_axis)
        measurements += len(new_x)

        plt.plot(new_x, new_y, label=client_name)
        print(f"plotting {client_name}")

    print(f"\tplotting ({measurements} measurements)...")

    plot_path = f"{plots_dir}/clients.png"
    print(f"Saving image to {plot_path}")
    plt.legend()
    plt.savefig(plot_path)
    print("Done!")

    plt.clf()


def plot_aux_1(info):
    client_name, results_per_server = info
    services = {}

    measurements = 0

    for _, results in results_per_server.items():
        for result in results:
            service = msg_type_to_service[result[MSG_TYPE]]
            if service in services:
                print(f'[{result[MSG_TYPE]}] {client_name} {result[ID]} {result[TIME_TOOK]}')
                services[service]['x_axis'].append(normalize_x_axis(result))
                services[service]['y_axis'].append(result[TIME_TOOK])
            else:
                services[service] = {'x_axis': [normalize_x_axis(result)], 'y_axis': [result[TIME_TOOK]]}

    for service in services:
        measurements += len(services[service]['x_axis'])
        new_x, new_y = sort_axis(services[service]['x_axis'], services[service]['y_axis'])
        plt.plot(new_x, new_y, '-o', label=service)

    client_dir = f"{plots_dir}/{client_name}"
    if not os.path.exists(client_dir):
        os.mkdir(client_dir)

    print(f"\tplotting {client_name} ({measurements} measurements)...")

    plot_path = f'{client_dir}/services.png'
    print(f"Saving image to {plot_path}")
    plt.legend()
    plt.savefig(plot_path)
    plt.clf()


def plot_latency_for_client_per_service(all_results):
    print("Plotting latency for clients per service...")

    infos = []
    for c, (r, _) in all_results.items():
        infos.append((c, r))

    with Pool(os.cpu_count()) as p:
        p.map(plot_aux_1, infos)

    print("Done!")


def plot_latency_for_client_per_server(all_results):
    print("Plotting latency for clients per server...")

    for client_name, (results_per_server, _) in all_results.items():
        client_dir = f"{plots_dir}/{client_name}"
        if not os.path.exists(client_dir):
            os.mkdir(client_dir)

        for server, results in results_per_server.items():
            measurements = 0

            x_axis = []
            y_axis = []

            for result in results:
                x_axis.append(result[TIME_RECV])
                y_axis.append(result[TIME_TOOK])

            measurements += len(x_axis)

            print(f"\tplotting {server} for {client_name} ({measurements} measurements)...")

            plt.plot(x_axis, y_axis, label=server)

            plot_path = f'{client_dir}/servers.png'
            plt.savefig(plot_path)
            print(f"Saving image to {plot_path}")

            plt.clf()

    print("Done!")


def plot_latency_per_service(all_results):
    print("Plotting latency per service...")

    services = {}
    measurements = 0

    for client_name, (results_per_server, _) in all_results.items():
        for server, results in results_per_server.items():
            for result in results:
                service = msg_type_to_service[result[MSG_TYPE]]
                if service in services:
                    services[service]['x_axis'].append(result[TIME_RECV])
                    services[service]['y_axis'].append(result[TIME_TOOK])
                else:
                    services[service] = {'x_axis': [result[TIME_RECV]], 'y_axis': [result[TIME_TOOK]]}

    for service in services:
        measurements += len(services[service]['x_axis'])
        plt.plot(services[service]['x_axis'], services[service]['y_axis'], label=service)

    print(f"\tplotting ({measurements} measurements)...")

    plot_path = f'{plots_dir}/services.png'
    plt.savefig()
    print(f"Saving image to {plot_path}")

    plt.clf()

    print("Done!")


# To plot:
#   - latency for clients (ignore server, service)
#   - latency for client per service (ignore server)
#   - latency for client per server (ignore server)
#   - latency for service (ignore server, client)
#   - histogram with messages sent per client
#   - histogram with messages sent for client per server

def process_results(all_results):
    plt.figure(figsize=(25, 15))
    plot_avg_latency_for_clients(all_results)
    plot_latency_for_client_per_service(all_results)


def parse_receive(log_file, print_list, emitted, current_hosts, msgs_per_server, results, line, line_num):
    # print("[RECEIVE]", line)
    parts = line.split(" ")

    msg_type = parts[3]
    if msg_type in ignored:
        return

    # print(msg_type)
    msg_id = parts[4]
    time_recv = parts[5][:-1]

    emitted_msg = emitted[msg_id]
    time_sent = emitted_msg[TIME_SENT]
    if msg_type not in msg_type_to_service:
        if emitted_msg[MSG_TYPE] not in msg_type_to_service:
            print(f"Found key {msg_type} or {emitted_msg[MSG_TYPE]} in {log_file[PATH]} at line {line_num}")
        else:
            msg_type = emitted_msg[MSG_TYPE]
    else:
        if msg_type_to_service[msg_type] in print_list:
            print(f"[{msg_type}] {msg_id} {int(time_recv) - int(time_sent)} {time_sent} -> {time_recv}")

    service = msg_type_to_service[msg_type]

    if service in current_hosts:
        server = current_hosts[service]
    else:
        server = current_hosts["notifications"]

    if server not in msgs_per_server:
        msgs_per_server[server] = 1
    else:
        msgs_per_server[server] += 1

    result = {
        MSG_TYPE: msg_type,
        ID: msg_id,
        TIME_RECV: time_recv,
        TIME_SENT: time_sent,
        TIME_TOOK: int(time_recv) - int(time_sent),
        REMOTE: emitted_msg[EMMITTER] != log_file[CLIENT_NAME]
    }

    if server not in results:
        results[server] = [result]
    else:
        results[server].append(result)


MIN_TIMESTAMP = -1


def parse_emit(client_name, emitted, line):
    global MIN_TIMESTAMP

    parts = line.split(" ")

    msg_type = parts[3]
    if msg_type in ignored:
        return

    # print("[EMIT]", line)
    msg_id = parts[4]
    time_sent = parts[5][:-1]
    emitted[msg_id] = {
        TIME_SENT: time_sent,
        EMMITTER: client_name,
        MSG_TYPE: msg_type
    }

    if MIN_TIMESTAMP == -1 or int(time_sent) < MIN_TIMESTAMP:
        MIN_TIMESTAMP = int(time_sent)


def parse_resolved(current_hosts, line, ips_to_nodes):
    parts = line.split(" ")
    service = parts[3].split(":")[0]
    host_ip = parts[5].split(":")[0]
    current_hosts[service] = ips_to_nodes[host_ip]


def parse_file_for_emits(log_file, emitted):
    with open(log_file[PATH], 'r') as file_data:
        for lineNum, lineUntrimmed in enumerate(file_data.readlines()):
            line = lineUntrimmed.rstrip('\n')

            if "[EMIT]" in line:
                parse_emit(log_file[CLIENT_NAME], emitted, line)

    return emitted


def parse_file_for_results(log_file, print_list, ips_to_nodes, emitted):
    results = {}
    current_hosts = {}
    msgs_per_server = {}

    with open(log_file[PATH], 'r') as file_data:
        for lineNum, lineUntrimmed in enumerate(file_data.readlines()):
            line = lineUntrimmed.rstrip('\n')

            if "[RECEIVE]" in line:
                parse_receive(log_file, print_list, emitted, current_hosts, msgs_per_server, results, line, lineNum)
            elif "resolved" in line:
                parse_resolved(current_hosts, line, ips_to_nodes)

    return results, msgs_per_server


def get_files_to_parse(client_logs_folder, only_one):
    files = []

    if only_one:
        for log in os.listdir(client_logs_folder):
            client_name = log.split(".")[0]
            log_path = os.path.join(client_logs_folder, log)
            files.append({
                CLIENT_NAME: client_name,
                PATH: log_path
            })
    else:
        for tester_dir in os.listdir(client_logs_folder):
            tester_dir_full_path = os.path.join(client_logs_folder, tester_dir)

            if not os.path.isdir(tester_dir_full_path):
                continue

            for log in os.listdir(tester_dir_full_path):
                client_name = log.split(".")[0]
                log_path = os.path.join(tester_dir_full_path, log)
                files.append({
                    CLIENT_NAME: f'{tester_dir}_{client_name}',
                    PATH: log_path
                })

    return files


if __name__ == '__main__':
    main()
