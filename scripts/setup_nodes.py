#!/usr/bin/python3
import subprocess
import sys

CLIENTS_PROP = "clientsnode"
SERVERS_PROP = "serversnode"


def run_with_log_and_exit(cmd):
    print(f"RUNNING | {cmd}")
    ret = subprocess.run(cmd, shell=True)
    if ret.returncode != 0:
        print(f"{cmd} returned {ret.returncode}")
        exit(ret.returncode)


def get_nodes():
    cmd = 'kubectl get nodes --template \'{{range .items}}{{.metadata.name}}{{"\\n"}}{{end}}\''
    output = subprocess.getoutput(cmd)

    return [node.strip() for node in output.split("\n")]


def clear_prop_for_node(node, prop):
    cmd = f'kubectl label nodes {node} {prop}-'
    run_with_log_and_exit(cmd)


def clear_client_and_server_prop_for_node(node):
    clear_prop_for_node(CLIENTS_PROP)
    clear_prop_for_node(SERVERS_PROP)


def set_prop_for_node(node, prop):
    cmd = f'kubectl label nodes {node} {prop}=true'
    run_with_log_and_exit(cmd)


def set_as_client_node(node):
    set_prop_for_node(node, CLIENTS_PROP)


def set_as_service_node(node):
    set_prop_for_node(node, SERVERS_PROP)


def clear_props(nodes):
    for node in nodes:
        clear_prop_for_node(node, CLIENTS_PROP)
        clear_prop_for_node(node, SERVERS_PROP)
    print("Cleared props!")


def main():
    num_args = 1

    args = sys.argv[1:]
    if len(args) != num_args:
        print("Usage: python3 setup_nodes.py <number_of_client_nodes>")
        exit(1)

    number_of_clients = int(args[0])

    nodes = get_nodes()
    print(f"Got nodes {nodes}")

    clear_props(nodes)

    if len(nodes) == 1:
        node = nodes[0]

        print(f"Only 1 node ({node}). Applying both server and client prop...")

        set_prop_for_node(node, CLIENTS_PROP)
        set_prop_for_node(node, SERVERS_PROP)
    else:
        for i in range(len(nodes) - number_of_clients):
            node = nodes[i]
            set_as_service_node(node)
            print(f"{node} is a server node")
        for i in range(len(nodes) - number_of_clients, len(nodes)):
            node = nodes[i]
            set_as_client_node(node)
            print(f"{node} is a client node")


if __name__ == '__main__':
    main()
