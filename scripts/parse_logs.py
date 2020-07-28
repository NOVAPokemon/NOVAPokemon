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

# MERGED RESULT FIELDS\
SERVICE = "service"
SUM_TIME_TOOK = "time_took"
NUM_ENTRIES = "num_entries"

msg_type_to_service = {

    "START_BATTLE": "battles",
    "STATUS": "battles",
    "REMOVE_ITEM": "battles",
    "UPDATE_POKEMON": "battles",

    "SERVERS_RESPONSE": "location",
    "CELLS_RESPONSE": "location",
    "GYMS": "location",
    "POKEMON": "location",
    "CATCH_POKEMON_RESPONSE": "location",

    "START_TRADE": "battles",
    "UPDATE_TRADE": "trades",
}


def main():
    if len(sys.argv) != 2:
        print("usage: parse_logs.py path_to_logs_folder")
        sys.exit(1)

    logs_folder = sys.argv[1]

    files = get_files_to_parse(logs_folder)

    results = []
    print("\n{} PARSING FILES {}\n".format(INFO_HEADER * 2, INFO_HEADER * 2))
    for file in files:
        results += parse_file(file)

    merged_results = merge_results(results)

    print("\n{} RESULTS {}\n".format(INFO_HEADER * 2, INFO_HEADER * 2))
    for key in merged_results:
        num_entries = merged_results[key][NUM_ENTRIES]
        total_latencies = merged_results[key][SUM_TIME_TOOK]
        avg_latency = total_latencies / num_entries
        print("{:<20}: num_samples: {:<3}, average: {:<3}ms".format(key, num_entries, avg_latency))


def merge_results(results):
    print("\n{} MERGING RESULTS {}\n".format(INFO_HEADER * 2, INFO_HEADER * 2))

    merged_results = {}
    for result in results:
        msg_type = result[MSG_TYPE]
        time_took = result[TIME_TOOK]
        service = msg_type_to_service[msg_type]
        try:
            curr_results = merged_results[service]
            curr_results[SUM_TIME_TOOK] += time_took
            curr_results[NUM_ENTRIES] += 1
        except KeyError:
            merged_results[service] = {
                SUM_TIME_TOOK: time_took,
                NUM_ENTRIES: 1,
            }
    print("merged {} samples".format(len(results)))
    return merged_results


def parse_file(log_file):
    results = []
    emitted = {}  # dict used to check if the received msg was sent by the user

    with open(log_file[PATH], 'r') as file_data:

        for lineUntrimmed in file_data:
            line = lineUntrimmed.rstrip('\n')

            if "[EMIT]" in line:
                # print("[EMIT]", line)
                parts = line.split(" ")
                msg_id = parts[4]
                time_sent = parts[5][:-1]
                emitted[msg_id] = time_sent

            if "[RECEIVE]" in line:
                # print("[RECEIVE]", line)
                parts = line.split(" ")
                msg_type = parts[3]
                # print(msg_type)
                msg_id = parts[4]
                time_recv = parts[5][:-1]
                try:
                    time_sent = emitted.pop(msg_id)  # means message was received in an emit
                    results.append({
                        MSG_TYPE: msg_type,
                        ID: msg_id,
                        TIME_RECV: time_recv,
                        TIME_SENT: time_sent,
                        TIME_TOOK: int(time_recv) - int(time_sent)
                    })
                except KeyError:
                    continue

    print("{}.log : {} samples".format(log_file[CLIENT_NAME], len(results)))
    return results


def get_files_to_parse(logs_folder):
    files = []
    for tester_dir in os.listdir(logs_folder):
        tester_dir = os.path.join(logs_folder, tester_dir)

        if not os.path.isdir(tester_dir):
            continue

        for log in os.listdir(tester_dir):
            if not log.endswith(".log"):
                continue

            client_name = log.split(".")[0]
            log_path = os.path.join(tester_dir, log)
            files.append({
                CLIENT_NAME: client_name,
                PATH: log_path
            })

    return files


if __name__ == '__main__':
    main()
