import sys
import os
import re
import json

# PREFIXES

prefixTimeNotification = "time notification:"
prefixAvgNotification = "average notification:"

prefixTimeBattle = "time battle:"
prefixAvgBattle = "average battle:"
prefixTimeStartBattle = "time start battle:"
prefixAvgTimeStartBattle = "average start battle:"

prefixTimeTrade = "time trade:"
prefixAvgTrade = "average trade:"
prefixTimeStartTrade = "time start trade:"
prefixAvgTimeStartTrade = "average start trade:"

prefixes = [
    prefixTimeNotification,
    prefixAvgNotification,
    prefixTimeBattle,
    prefixAvgBattle,
    prefixTimeStartBattle,
    prefixAvgTimeStartBattle,
    prefixTimeTrade,
    prefixAvgTrade,
    prefixTimeStartTrade,
    prefixAvgTimeStartTrade
]

# HEADERS

headers = [
    "notification_times",
    "notification_avg",
    "battle_messages_times",
    "battle_messages_avg",
    "battle_start_times",
    "battle_start_avg",
    "trade_messages_times",
    "trade_messages_avg",
    "trade_start_times",
    "trade_start_avg"
]

info_header = "-----------------"

if len(sys.argv) != 2:
    print("usage: parse_logs.py path_to_logs_folder")
    sys.exit(1)

logs_folder = sys.argv[1]
json_logs = {}

for tester_dir in os.listdir(logs_folder):
    tester_name = tester_dir
    tester_dir = os.path.join(logs_folder, tester_dir)

    if not os.path.isdir(tester_dir):
        continue

    tester_logs = {}
    json_logs[tester_name] = tester_logs

    for log in os.listdir(tester_dir):
        if not log.endswith(".log"):
            continue

        client_name = log.split(".")[0]
        log = os.path.join(tester_dir, log)

        client_logs = {}
        tester_logs[client_name] = client_logs

        with open(log, 'r') as log_file:
            print(f"{info_header} LOG {log} {info_header}")
            log_content = log_file.read()

            for prefix, header in zip(prefixes, headers):
                pattern = re.compile(f"{prefix} ([0-9]+[.]?[0-9]+|[0-9]+) ms")
                results = pattern.findall(log_content)
                client_logs[header] = results
                print(f"Found {len(results)} results for {header} in client's {client_name} logs")

json_filename = "logs.json"
final_filename = os.path.join(logs_folder, json_filename)
with open(final_filename, 'w') as final_file:
    print(f"{info_header} FINISHING {info_header}")
    print(f"Writing logs to file: {final_filename}")
    json.dump(json_logs, final_file, indent=4, sort_keys=True)

averageTradeMsg = 0
averageStartTrade = 0
averageBattleMsg = 0
averageStartBattle = 0
averageNotification = 0

measurementHeaders = [
    "notification_times",
    "battle_messages_times",
    "battle_start_times",
    "trade_messages_times",
    "trade_start_times",
]

averageHeaders = [
    "notification_avg",
    "battle_messages_avg",
    "battle_start_avg",
    "trade_messages_avg",
    "trade_start_avg"
]

stats = {}

for header in measurementHeaders:
    measurementsTotal = 0
    measurementCount = 0

    for tester_name in json_logs:
        tester = json_logs[tester_name]
        for client_name in tester:
            for measurement in tester[client_name][header]:
                measurementsTotal += float(measurement)
                measurementCount += 1

    measurementAvg = measurementsTotal / measurementCount
    stats[header] = measurementAvg

    print(f"Found {measurementCount} measures of {header}")

expectedStats = {}

for header in averageHeaders:
    measurementsTotal = 0
    measurementCount = 0

    for tester_name in json_logs:
        tester = json_logs[tester_name]
        for client_name in tester:
            if len(tester[client_name][header]) > 0:
                measurement = tester[client_name][header][-1]
                measurementsTotal += float(measurement)
                measurementCount += 1

    measurementAvg = measurementsTotal / measurementCount
    expectedStats[header] = measurementAvg

print(f"{info_header} STATISTICS {info_header}")
print(stats)
print(expectedStats)