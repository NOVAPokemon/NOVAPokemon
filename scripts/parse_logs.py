# This script would probably be way simpler if it used pandas. So it happened i
# only discovered pandas a few scripts down the road, and this is one of the first
# ones where i didn't know about.

import json
import os
from multiprocessing.pool import Pool

import matplotlib.pyplot as plt
import pandas
import sys
from icecream import ic

INFO_HEADER = "-----------------"

# FILE INFO
CLIENT_DIR = "client_dir"
CLIENT_NAME = "client_name"
CLIENT_ID = "client_id"
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

services = [
    "battles",
    "location",
    "trades",
    "notifications"
]

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


def normalize_x_axis(result, min_timestamp):
    return (int(result[TIME_RECV]) - min_timestamp) / 1000


def write_avg_latency_for_clients_to_csv(all_results, output_dir):
    with open(f'{output_dir}/clients.csv', 'w') as f:
        f.write('timestamp;time_took;client_id\n')

        for client_id, (results_per_server, _, _, _) in all_results.items():
            for _, results in results_per_server.items():
                for result in results:
                    f.write(
                        f'{result[TIME_RECV]};{result[TIME_TOOK]};{client_id}\n')


def load_avg_latency_for_clients_to_csv(output_dir: str):
    return pandas.read_csv(f'{output_dir}/clients.csv', delimiter=';')


def plot_avg_latency_for_clients(min_timestamp, all_results, output_dir, csvs):
    print("Plotting average latency for clients...")

    timestamp_header = 'timestamp'
    time_took_header = 'time_took'
    rolling_time_took_avg_header = 'rolling_time_took_avg'

    if not csvs:
        write_avg_latency_for_clients_to_csv(all_results, output_dir)

    latencies_csv = load_avg_latency_for_clients_to_csv(output_dir)

    latencies_csv.index = pandas.to_datetime(
        latencies_csv[timestamp_header], unit='ms')
    latencies_csv.index.name = None
    latencies_csv.sort_index(inplace=True)

    print(latencies_csv)

    ic(latencies_csv)
    latencies_agg = latencies_csv.groupby(timestamp_header, as_index=False)[
        time_took_header].mean()
    latencies_agg.index = pandas.to_datetime(
        latencies_agg[timestamp_header], unit='ms')
    latencies_agg.index.name = None

    latencies_agg[rolling_time_took_avg_header] = latencies_agg.rolling(
        '2s', min_periods=1).mean()[time_took_header]

    fig = plt.figure(figsize=(25, 15))

    min_timestamp = latencies_agg[timestamp_header].min()

    plt.plot(latencies_agg[timestamp_header].apply(lambda x: (x - min_timestamp) / 1000),
             latencies_agg[rolling_time_took_avg_header])

    plot_path = f"{output_dir}/clients.png"
    print(f"Saving image to {plot_path}")
    plt.grid()
    plt.legend()
    plt.savefig(plot_path)
    print("Done!")

    plt.clf()
    plt.close(fig)


def plot_aux_1(info):
    client_id, results_per_server, aux_client_dir, client_name, output_dir, min_timestamp = info
    services = {}

    measurements = 0

    if DEBUG:
        ic.enable()
    else:
        ic.disable()

    fig = plt.figure(figsize=(25, 15))

    for _, results in results_per_server.items():
        for result in results:
            service = msg_type_to_service[result[MSG_TYPE]]
            if service in services:
                ic(result[MSG_TYPE], client_id, result[ID], result[TIME_TOOK])
                services[service]['x_axis'].append(
                    normalize_x_axis(result, min_timestamp))
                services[service]['y_axis'].append(result[TIME_TOOK])
            else:
                services[service] = {'x_axis': [normalize_x_axis(result, min_timestamp)], 'y_axis': [
                    result[TIME_TOOK]]}

    for service in services:
        measurements += len(services[service]['x_axis'])
        new_x, new_y = sort_axis(
            services[service]['x_axis'], services[service]['y_axis'])
        plt.plot(new_x, new_y, '-o', label=service)

    client_dir = f"{output_dir}/{aux_client_dir}/{client_name}"
    if not os.path.exists(client_dir):
        os.mkdir(client_dir)

    ic(f"\tplotting {client_id} ({measurements} measurements)...")

    plot_path = f'{client_dir}/services.png'
    ic(f"Saving image to {plot_path}")
    plt.grid()
    plt.savefig(plot_path)
    plt.clf()
    plt.close(fig)


DEBUG = False


def plot_latency_for_client_per_service(min_timestamp, all_results, output_dir, debug):
    print("Plotting latency for clients per service...")

    infos = []
    for c, (r, _, client_dir, client_name) in all_results.items():
        clients_dir = f"{output_dir}/{client_dir}/"
        if not os.path.exists(clients_dir):
            os.mkdir(clients_dir)
        infos.append((c, r, client_dir, client_name,
                      output_dir, min_timestamp))

    global DEBUG
    DEBUG = debug

    with Pool(os.cpu_count()) as p:
        p.map(plot_aux_1, infos)

    print("Done!")


def plot_latency_for_client_per_server(all_results, output_dir):
    print("Plotting latency for clients per server...")

    for client_name, (results_per_server, _) in all_results.items():
        client_dir = f"{output_dir}/{client_name}"
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

            print(
                f"\tplotting {server} for {client_name} ({measurements} measurements)...")

            plt.grid()
            plt.plot(x_axis, y_axis, label=server)

            plot_path = f'{client_dir}/servers.png'
            plt.savefig(plot_path)
            print(f"Saving image to {plot_path}")

            plt.clf()

    print("Done!")


def plot_latency_per_service(all_results, output_dir):
    print("Plotting latency per service...")

    services = {}
    measurements = 0

    for _, (results_per_server, _) in all_results.items():
        for server, results in results_per_server.items():
            for result in results:
                service = msg_type_to_service[result[MSG_TYPE]]
                if service in services:
                    services[service]['x_axis'].append(result[TIME_RECV])
                    services[service]['y_axis'].append(result[TIME_TOOK])
                else:
                    services[service] = {'x_axis': [
                        result[TIME_RECV]], 'y_axis': [result[TIME_TOOK]]}

    for service in services:
        measurements += len(services[service]['x_axis'])
        plt.plot(services[service]['x_axis'],
                 services[service]['y_axis'], label=service)

    print(f"\tplotting ({measurements} measurements)...")

    plot_path = f'{output_dir}/services.png'
    plt.grid()
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

def process_results(min_timestamp, all_results, output_dir, debug, csvs):
    plot_avg_latency_for_clients(min_timestamp, all_results, output_dir, csvs)
    plot_latency_for_client_per_service(
        min_timestamp, all_results, output_dir, debug)


def parse_receive(log_file, print_list, emitted, current_hosts, msgs_per_server, results, line, line_num):
    # print("[RECEIVE]", line)
    parts = line.split(" ")

    msg_type = parts[3]
    if msg_type in ignored:
        return

    # print(msg_type)
    msg_id = parts[4]
    time_recv = parts[5][:-1]

    if msg_id not in emitted:
        return

    emitted_msg = emitted[msg_id]

    time_sent = emitted_msg[TIME_SENT]
    if msg_type not in msg_type_to_service:
        if emitted_msg[MSG_TYPE] not in msg_type_to_service:
            ic(msg_type, emitted_msg[MSG_TYPE], log_file[PATH], line_num)
        else:
            msg_type = emitted_msg[MSG_TYPE]
    else:
        if msg_type_to_service[msg_type] in print_list:
            time_took = int(time_recv) - int(time_sent)
            ic(msg_type, msg_id, time_took, time_sent, time_recv)

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


def parse_emit(client_name, emitted, line):
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


def parse_resolved(current_hosts, line, ips_to_nodes):
    parts = line.split(" ")
    service = parts[3].split(":")[0]
    host_ip = parts[5].split(":")[0]
    current_hosts[service] = ips_to_nodes[host_ip]


def parse_requests(requests, line, log_file_path):
    try:
        msg = line.split('msg=')[1][1:-1]
        splits = msg.split(" ")

        timestamp = int(splits[1])
        count = int(splits[2])

        requests[timestamp] = count
    except Exception as e:
        print(f'{log_file_path}: {line}')


def parse_retries(retries, line):
    msg = line.split('msg=')[1][1:-1]
    splits = msg.split(" ")

    timestamp = int(splits[1])
    count = int(splits[2])

    retries[timestamp] = count


def parse_sent_req(sent_reqs, line):
    msg = line.split('msg=')[1][1:-1]
    splits = msg.split(" ")

    timestamp = int(splits[1])
    req_id = splits[2]

    sent_reqs[req_id] = timestamp


def parse_got_resp(got_resps, line):
    msg = line.split('msg=')[1][1:-1]
    splits = msg.split(" ")

    req_id = splits[1]

    got_resps[req_id] = None


def parse_file_for_emits(log_file, emitted, retries, requests, sent_reqs, got_resps):
    client_retries, client_requests, client_sent_reqs, client_got_resps = {}, {}, {}, {}

    with open(log_file[PATH], 'r') as file_data:
        for lineUntrimmed in file_data.readlines():
            line = lineUntrimmed.rstrip('\n')

            if "[RET]" in line:
                parse_retries(client_retries, line)
            elif "[REQ]" in line:
                parse_requests(client_requests, line, log_file[PATH])
            elif "[SENT_REQ_ID]" in line:
                parse_sent_req(client_sent_reqs, line)
            elif "[GOT_RESP_ID]" in line:
                parse_got_resp(client_got_resps, line)
            elif "[EMIT]" in line:
                parse_emit(log_file[CLIENT_NAME], emitted, line)

    retries[log_file[CLIENT_ID]] = client_retries
    requests[log_file[CLIENT_ID]] = client_requests
    sent_reqs.update(client_sent_reqs)
    got_resps.update(client_got_resps)

    return emitted


def parse_file_for_results(log_file, print_list, ips_to_nodes, emitted):
    results = {}
    current_hosts = {}
    for service in services:
        current_hosts[service] = "fallback"

    msgs_per_server = {}

    with open(log_file[PATH], 'r') as file_data:
        for lineNum, lineUntrimmed in enumerate(file_data.readlines()):
            line = lineUntrimmed.rstrip('\n')

            if "[RECEIVE]" in line:
                parse_receive(log_file, print_list, emitted, current_hosts,
                              msgs_per_server, results, line, lineNum)
            elif "resolved" in line:
                parse_resolved(current_hosts, line, ips_to_nodes)

    return results, msgs_per_server, log_file[CLIENT_DIR], log_file[CLIENT_NAME]


def get_files_to_parse(client_logs_folder, only_one):
    files = []

    if only_one:
        for log in os.listdir(client_logs_folder):
            if log[-4:] != '.log':
                continue

            client_name = log.split(".")[0]

            log_path = os.path.join(client_logs_folder, log)
            files.append({
                CLIENT_NAME: client_name,
                PATH: log_path
            })
        return files

    for tester_dir in os.listdir(client_logs_folder):
        tester_dir_full_path = os.path.join(client_logs_folder, tester_dir)

        if not os.path.isdir(tester_dir_full_path):
            continue

        for log in os.listdir(tester_dir_full_path):
            if log[-4:] != '.log':
                continue

            client_name = log.split(".")[0]

            log_path = os.path.join(tester_dir_full_path, log)
            files.append({
                CLIENT_DIR: tester_dir,
                CLIENT_NAME: client_name,
                CLIENT_ID: f'{tester_dir}_{client_name}',
                PATH: log_path
            })

    return files


def write_reqs_rets_to_csv(requests, retries, output_dir):
    with open(f'{output_dir}/reqs.csv', 'w') as f:
        f.write('timestamp;reqs;client_id\n')
        for client_id in requests:
            for ts, count in requests[client_id].items():
                f.write(f'{ts};{count};{client_id}\n')

    with open(f'{output_dir}/rets.csv', 'w') as f:
        f.write('timestamp;rets;client_id\n')
        for client_id in retries:
            for ts, count in retries[client_id].items():
                f.write(f'{ts};{count};{client_id}\n')


def load_reqs_rets_to_csv(output_dir):
    return pandas.read_csv(f'{output_dir}/reqs.csv', delimiter=';'), \
        pandas.read_csv(f'{output_dir}/rets.csv', delimiter=';')


def process_requests_retries(requests, retries, output_dir, csvs):
    client_id_header = 'client_id'
    reqs_rolling_header = 'reqs_rolling'
    rets_rolling_header = 'rets_rolling'
    rets_per_rolling_header = 'rets_per_rolling'
    timestamp_header = 'timestamp'
    reqs_header = 'reqs'
    rets_header = 'rets'

    if not csvs:
        write_reqs_rets_to_csv(requests, retries, output_dir)

    reqs_csv, rets_csv = load_reqs_rets_to_csv(output_dir)

    fig = plt.figure(figsize=(25, 15))

    min_timestamp = reqs_csv[timestamp_header].min()
    reqs_csv[reqs_header] = reqs_csv[reqs_header].apply(lambda x: 1)
    reqs_csv.index = pandas.to_datetime(reqs_csv[timestamp_header], unit='ms')
    reqs_csv = reqs_csv.sort_index()
    reqs_csv.index.name = None

    rets_csv[rets_header] = rets_csv[rets_header].apply(lambda x: 1)
    rets_csv.index = pandas.to_datetime(rets_csv[timestamp_header], unit='ms')
    rets_csv = rets_csv.sort_index()
    rets_csv.index.name = None

    reqs_csv.drop(client_id_header, axis=1, inplace=True)
    rets_csv.drop(client_id_header, axis=1, inplace=True)

    ic(reqs_csv, rets_csv)

    reqs_agg = reqs_csv.groupby(timestamp_header, as_index=False)[
        reqs_header].sum()
    reqs_agg.index = pandas.to_datetime(reqs_agg[timestamp_header], unit='ms')

    rets_agg = rets_csv.groupby(timestamp_header, as_index=False)[
        rets_header].sum()
    rets_agg.index = pandas.to_datetime(rets_agg[timestamp_header], unit='ms')

    reqs_agg.index.name = None
    rets_agg.index.name = None

    merged = pandas.merge(reqs_agg, rets_agg, how='left').fillna(0).astype(int)
    merged.index = pandas.to_datetime(merged[timestamp_header], unit='ms')
    merged = merged.sort_index()

    merged[reqs_rolling_header] = merged.rolling(
        '2s', min_periods=1).sum()[reqs_header]

    merged[rets_rolling_header] = merged.rolling(
        '2s', min_periods=1).sum()[rets_header]

    ic(merged)

    plt.plot(
        merged[timestamp_header].apply(
            lambda x: (x - min_timestamp) / 1000
        ),
        merged[reqs_rolling_header]
    )

    plt.plot(
        merged[timestamp_header].apply(
            lambda x: (x - min_timestamp) / 1000
        ),
        merged[rets_rolling_header]
    )

    plt.grid()
    plt.savefig(f'{output_dir}/reqs_rets.png')
    plt.clf()
    plt.close(fig)


def write_sent_reqs_got_resps_to_csv(sent_reqs, got_resps, got_reqs, output_dir):
    with open(f'{output_dir}/reqs_resps.csv', 'w') as f:
        f.write('timestamp;req_id;was_recv;got_resp\n')
        for req_id, timestamp in sent_reqs.items():
            was_received = req_id in got_reqs
            got_resp = req_id in got_resps
            f.write(
                f'{timestamp};{req_id};{1 if was_received else 0};{1 if got_resp else 0}\n')


def load_sent_reqs_got_resps_to_csv(output_dir):
    return pandas.read_csv(f'{output_dir}/reqs_resps.csv', delimiter=';')


def process_server_log(filename):
    recv_reqs = {}
    with open(filename) as f:
        for line in f.readlines():
            line = line.strip()
            if "[GOT_REQ_ID]" in line:
                msg = line.split('msg=')[1][1:-1]
                splits = msg.split(" ")
                timestamp = int(splits[1])
                req_id = splits[2]
                recv_reqs[req_id] = timestamp

    return recv_reqs


def process_sent_reqs_got_resps(reqs, resps, csvs, server_logs, output_dir):
    timestamp_header = 'timestamp'
    req_id_header = 'req_id'
    reqs_header = 'reqs'
    was_recv_header = 'was_recv'
    got_resp_header = 'got_resp'
    rolling_reqs_header = 'rolling_reqs'
    rolling_recvs_header = 'rolling_recvs'
    rolling_resps_header = 'rolling_resps'

    service_names = [
        "authentication",
        "battles",
        "gyms",
        "location",
        "microtransactions",
        "notifications",
        "store",
        "trades",
        "trainers"
    ]

    got_reqs = {}
    dummies = [os.path.join(server_logs, dummy)
               for dummy in os.listdir(server_logs)]
    logs = []
    for dummy in dummies:
        for log in os.listdir(dummy):
            matches = False
            for service in service_names:
                if service in log:
                    matches = True
                    break
            if matches:
                logs.append(os.path.join(dummy, log))

    print(f'Considering logs {logs}')

    with Pool(os.cpu_count()) as p:
        results = p.map(process_server_log, logs)

    for result in results:
        got_reqs.update(result)

    if not csvs:
        write_sent_reqs_got_resps_to_csv(reqs, resps, got_reqs, output_dir)

    values = load_sent_reqs_got_resps_to_csv(output_dir)

    fig, ax1 = plt.subplots(figsize=(25, 15))

    min_timestamp = values[timestamp_header].min()
    values.index = pandas.to_datetime(values[timestamp_header], unit='ms')
    values = values.sort_index()
    values.index.name = None

    values[reqs_header] = 1
    # reqs_agg = values.groupby(timestamp_header, as_index=False)[
    #     reqs_header].sum()

    # ic(values)
    # ic(reqs_agg)

    values_rolling = values.rolling('10s', min_periods=0).sum()

    ic(values_rolling)
    values[rolling_reqs_header] = values_rolling[reqs_header]
    values[rolling_recvs_header] = values_rolling[was_recv_header]
    values[rolling_resps_header] = values_rolling[got_resp_header]

    ax1.set_ylabel('Number of requests', color='tab:blue')

    ax1.plot(
        (values[timestamp_header] - min_timestamp) / 1000,
        values[rolling_reqs_header],
        label='requests emitted',
        color='tab:blue'
    )

    ax2 = ax1.twinx()

    ax2.plot(
        (values[timestamp_header] - min_timestamp) / 1000,
        values[rolling_recvs_header].div(values[rolling_reqs_header]).mul(100),
        label='requests received',
        color='black',
        linestyle='--',
        linewidth=1
    )

    ax2.plot(
        (values[timestamp_header] - min_timestamp) / 1000,
        values[rolling_resps_header].div(
            values[rolling_reqs_header]).mul(100),
        label='responses',
        color='red',
        linestyle='',
        marker='x'
    )

    ax2.set_ylim((0, 101))
    ax2.set_ylabel('% of requests', color='red')

    fig.tight_layout()
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    h, l = [], []
    h.extend(h1)
    h.extend(h2)

    l.extend(l1)
    l.extend(l2)
    fig.legend(h, l, loc='upper right')

    plt.grid()
    plt.savefig(f'{output_dir}/sent_reqs_got_resps.png')
    plt.clf()
    plt.close(fig)


def main():
    args = sys.argv[1:]
    max_args = 8
    min_args = 2
    if len(args) < min_args or len(args) > max_args:
        print("usage: parse_logs.py <client_logs_folder> <server_logs_folder> [--only-one]"
              "[--print=trades,battles] [--dummy-infos=/tmp/dummy_infos.json]"
              " [--debug] [--output=<output_dir>] [--csvs]")
        sys.exit(1)

    logs_folder = ""
    server_logs_folder = ""
    only_one = False
    print_list = []
    dummy_infos_path = ""
    output_dir = os.path.expanduser('~/plots')
    csvs = False
    debug = False
    min_timestamp = 0

    ic.disable()

    for arg in args:
        if arg == "--only-one":
            only_one = True
        elif "--print" in arg:
            print_list = arg.split("=")[1].split(",")
        elif "--dummy-infos" in arg:
            dummy_infos_path = os.path.expanduser(arg.split("=")[1])
            print(f"dummy_infos set to {dummy_infos_path}")
        elif "--debug" == arg:
            debug = True
            ic.enable()
        elif "--output" in arg:
            output_dir = os.path.expanduser(arg.split('=')[1])
        elif "--csvs" == arg:
            csvs = True
        elif "--ts=" in arg:
            min_timestamp = float(arg.split("=")[1])
        elif logs_folder == "":
            logs_folder = arg
        elif server_logs_folder == "":
            server_logs_folder = arg

    ic('Logging enabled')

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

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

    emitted, retries, requests, sent_reqs, got_resps = {}, {}, {}, {}, {}

    for file in files:
        emitted = parse_file_for_emits(
            file, emitted, retries, requests, sent_reqs, got_resps)

    for file in files:
        results[file[CLIENT_ID]] = parse_file_for_results(
            file, print_list, ips_to_nodes, emitted)

    with open(os.path.expanduser('~/logs_results.json'), 'w') as results_fp:
        json.dump(results, results_fp)

    process_results(min_timestamp, results, output_dir, debug, csvs)

    process_requests_retries(requests, retries, output_dir, csvs)
    process_sent_reqs_got_resps(
        sent_reqs, got_resps, csvs, server_logs_folder, output_dir)


if __name__ == '__main__':
    main()
