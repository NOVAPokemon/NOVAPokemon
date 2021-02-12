import json
import os
import sys

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

# MERGED RESULT FIELDS\
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
    "UPDATE_TRADE": "trades",
    "REJECT_TRADE": "trades",
    "CREATE_TRADE": "trades",
    "TRADE": "trades",
    "ACCEPT": "trades",
}


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


def process_results(all_results):
    server_results = {}

    for client_name, (results_per_server, msgs_per_server) in all_results.items():
        client_result = {}
        client_result_remotes = {}
        client_avgs = {}
        client_remote_avgs = {}

        for server, results in results_per_server.items():
            if server not in server_results:
                server_results[server] = {}

            service_result_for_client = {}
            service_result_for_client_remote = {}

            for result in results:
                service = msg_type_to_service[result[MSG_TYPE]]
                time_took = result[TIME_TOOK]
                if result[REMOTE]:
                    add_entry_if_missing(service_result_for_client_remote, service, time_took)
                    add_entry_if_missing(client_remote_avgs, service, time_took)
                else:
                    add_entry_if_missing(service_result_for_client, service, time_took)
                    add_entry_if_missing(client_avgs, service, time_took)

                add_entry_if_missing(server_results[server], service, time_took)

            client_result[server] = service_result_for_client
            client_result_remotes[server] = service_result_for_client_remote

        print(f"------------------------- {client_name} -------------------------")
        print(f"\t-------------- LOCAL --------------")
        print(f"\t---- Servers ----")

        for server, results in client_result.items():
            print(f"\t\tServer {server}:")
            print(f"\t\tNumMsgs: {msgs_per_server[server]}")
            for service, result in results.items():
                print(f"\t\t\t{service}: {result[TIME_TOOK] / result[NUM_ENTRIES]}")

        print("\t---- Averages ----")
        for service, result in client_avgs.items():
            print(f"\t\t{service}: {result[TIME_TOOK] / result[NUM_ENTRIES]}")

        print("\t-------------- REMOTE --------------")
        for server, results in client_result_remotes.items():
            print(f"\t\tServer {server}:")
            for service, result in results.items():
                print(f"\t\t\t{service}: {result[TIME_TOOK] / result[NUM_ENTRIES]}")

        print("\t---- Averages ----")
        for service, result in client_remote_avgs.items():
            print(f"\t\t{service}: {result[TIME_TOOK] / result[NUM_ENTRIES]}")

    for server, results in server_results.items():
        print(f"------------------------- SERVER {server} -------------------------")
        for service, result in results.items():
            print(f"\t{service}: {result[TIME_TOOK] / result[NUM_ENTRIES]}")


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
            tester_dir = os.path.join(client_logs_folder, tester_dir)

            if not os.path.isdir(tester_dir):
                continue

            for log in os.listdir(tester_dir):
                client_name = log.split(".")[0]
                log_path = os.path.join(tester_dir, log)
                files.append({
                    CLIENT_NAME: client_name,
                    PATH: log_path
                })

    return files


if __name__ == '__main__':
    main()
