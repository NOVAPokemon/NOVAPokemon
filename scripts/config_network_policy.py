import subprocess
import sys
import json
import re
import os

ip_label = "cni.projectcalico.org/ipAddrs"
json_field_rules = "rules"
json_field_from = "from"
json_field_to = "to"
json_field_delay = "delay"
json_field_bandwidth = "bandwidth"

if len(sys.argv) != 2:
    print("Usage: python3 control_traffic.py rules_file.json")

rules_filename = sys.argv[1]


def get_pods():
    output = subprocess.run(
        ["kubectl", "get", "pods", "--template", "'{{range .items}}{{.metadata.name}}{{\"\n\"}}{{end}}'"],
        check=True, stdout=subprocess.PIPE, universal_newlines=True)
    return output.stdout.split("\n")


def load_rules_file(filename):
    with open(filename, 'r') as file:
        data = file.read()

    json_data = json.loads(data)
    return json_data[json_field_rules]


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


pods = get_pods()
pod_ips = get_ips_per_pod()
rules = load_rules_file(rules_filename)

if rules is None:
    print("could not find rules property in specified json file")
    sys.exit(1)

apply_all_rules(rules)
