import subprocess
import sys
import json
import re
import os

ip_label = "cni.projectcalico.org/ipAddrs"

ip_range_char = 'X'

json_field_ips = "ips"
json_field_pod = "pod"
json_field_ip = "ip"

json_field_rules = "rules"
json_field_from = "from"
json_field_to = "to"
json_field_delay = "delay"
json_field_bandwidth = "bandwidth"

apply_ips = False
apply_rules = False

if len(sys.argv) < 3:
    print("Usage: python3 config_network_policy.py [OPTIONS] config_file.json\n"
          "OPTIONS:\n"
          "\t-i\tapply IPs from config file\n"
          "\t-r\tapply traffic control rules from config file")


def parse_flag(flag):
    global apply_ips, apply_rules

    if flag == "-i":
        apply_ips = True
    elif flag == "-r":
        apply_rules = True
    else:
        print(f"invalid option '{flag}'")
        sys.exit(1)


if len(sys.argv) == 3:
    parse_flag(sys.argv[1])
    config_filename = sys.argv[2]
elif len(sys.argv) == 4:
    parse_flag(sys.argv[1])
    parse_flag(sys.argv[2])
    config_filename = sys.argv[3]
else:
    print(f"too many arguments {len(sys.argv)}")
    sys.exit(1)


def get_pods():
    output = subprocess.run(
        ["kubectl", "get", "pods", "--template", "'{{range .items}}{{.metadata.name}}{{\"\n\"}}{{end}}'"],
        check=True, stdout=subprocess.PIPE, universal_newlines=True)
    return output.stdout.split("\n")


def load_json_data(filename):
    with open(filename, 'r') as file:
        data = file.read()

    return json.loads(data)


def get_matching_pods(podname):
    return [pod if re.match(podname, pod) else None for pod in pods]


def get_ips_per_pod():
    output = subprocess.run(["kubectl", "get", "pods", "--show-labels", "|" "awk", "'{ print $1, $6}'"],
                            check=True, stdout=subprocess.PIPE, universal_newlines=True)
    labels_output = output.stdout.split('\n')
    labels_output.pop(0)

    ips_per_pod = {}
    for label_output in labels_output:
        output_splitted = label_output.split(' ')
        pod_name = output_splitted[0]
        labels_joined = output_splitted[1].split(',')
        found = False

        for label in labels_joined:
            label_splitted = label.split('=')
            if label_splitted[0] == ip_label:
                found = True
                ips_per_pod[pod_name] = label_splitted[1]
                break

        if not found:
            print("could not find ip for pod ", pod_name)
            sys.exit(1)

    return ips_per_pod


def apply_rules(from_pod, rule_to_apply):
    os.system(f"kubectl exec {from_pod} -- sh -c \"tc qdisc add dev eth0 root handle 1: htb\"")

    target_pods = get_matching_pods(rule_to_apply[json_field_to])
    bandwidth = rule_to_apply[json_field_bandwidth]
    delay = rule_to_apply[json_field_delay]

    for i, to_pod in enumerate(target_pods, start=1):
        to_pod_ip = pod_ips[to_pod]
        if to_pod_ip is None:
            print(f"could not find matching ip for {to_pod}")
            sys.exit(1)

        print(f"applying {delay} and {bandwidth} from {from_pod} to {to_pod}")
        exit_code = os.system(
            f"kubectl exec -- sh -c \"tc class add dev eth0 parent 1: classid 1:{i}1 htb rate {bandwidth}\" prio 0")
        if exit_code != 0:
            print(f"exit_code {exit_code} applying class")
            sys.exit(1)

        exit_code = os.system(
            f"kubectl exec -- sh -c \"tc qdisc add dev eth0 parent 1:{i}1 handle {i}10: netem delay {delay}\"")
        if exit_code != 0:
            print(f"exit_code {exit_code} applying qdisc")
            sys.exit(1)

        exit_code = os.system(f"kubectl exec -- sh -c \"tc filter add dev eth0 protocol ip parent 1:0 prio"
                              f" 1 u32 match ip dst {to_pod_ip} flowid 1:{i}1\"")
        if exit_code != 0:
            print(f"exit_code {exit_code} applying filter")
            sys.exit(1)


def apply_all_rules(rules_to_apply):
    for rule in rules_to_apply:
        pod_name = rule[json_field_from]
        pods_to_apply = get_matching_pods(pod_name)
        print("matching pods for ", pod_name, ": ", pods_to_apply)
        for pod_to_apply in pods_to_apply:
            apply_rules(pod_to_apply, rule)


def translate_ip_to_range(ip, range_size):
    ip_range = []

    for num in range(range_size):
        ip_range.append(ip.replace(ip_range_char, num))

    return ip_range

def apply_ips(ips_config):
    for ip_config in ips_config:
        podname = ip_config[json_field_pod]
        ip = ip_config[json_field_ip]

        matching_pods = get_matching_pods(podname)

        if len(matching_pods) > 1:
            if not ip_range_char in ip:
                print(f"can not assing same ip to multiple pods: {podname} -> {ip}")
                sys.exit(1)
            ip_range = translate_ip_to_range(ip, len(matching_pods))



pods = get_pods()

pod_ips = get_ips_per_pod()
json_data = load_json_data(config_filename)

ips = json_data[json_field_ips]

if ips is None:
    print("could not find ips property in specified json file")
    sys.exit(1)

rules = json_data[json_field_rules]

if rules is None:
    print("could not find rules property in specified json file")
    sys.exit(1)

if apply_ips:
    apply_ips(ips)

if apply_rules:
    apply_all_rules(rules)
