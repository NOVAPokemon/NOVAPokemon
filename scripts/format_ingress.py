#!/usr/bin/python3
import os
import subprocess

import yaml

NOVAPOKEMON_DIR = os.path.expanduser('~/go/src/github.com/NOVAPokemon')
DEPL_CHARTS_DIR = f'{NOVAPOKEMON_DIR}/deployment-chart'

services = ['authentication', 'battles', 'location', 'microtransactions', 'notifications', 'store', 'trades',
            'trainers']

'''
- host: store-0
  http:
    paths:
      - path: /store
        backend:
          hostNames:
            - store-0
          serviceName: store-service-headless
          servicePort: 8007
'''


def create_path_rules(name, replicas, port):
    rules = []
    for index in range(replicas):
        rule = {
            "host": f'{name}-{index}',
            "http": {
                "paths": [
                    {
                        "path": f'/{name}',
                        "backend": {
                            'hostNames': [f'{name}-{index}'],
                            'serviceName': f'{name}-service-headless',
                            'servicePort': port
                        }
                    }
                ]
            }
        }
        rules.append(rule)

    return rules


def helm_unignore_file(file):
    has_line = False
    with open(f'{DEPL_CHARTS_DIR}/.helmignore', "r") as f:
        lines = []
        for line in f.readlines():
            if file in line:
                has_line = True
            else:
                lines.append(line)

    if has_line:
        with open(f'{DEPL_CHARTS_DIR}/.helmignore', "w") as f:
            for line in lines:
                f.write(line)


def helm_ignore_file(file):
    has_line = False
    with open(f'{DEPL_CHARTS_DIR}/.helmignore', 'r') as f:
        for line in f.readlines():
            if file in line:
                has_line = True

    if not has_line:
        with open(f'{DEPL_CHARTS_DIR}/.helmignore', 'a') as f:
            f.write(f'{file}\n')


def main():
    helm_unignore_file('templates/ingress-template.yaml')
    helm_ignore_file('templates/ingress.yaml')

    output = subprocess.getoutput(f'cd {DEPL_CHARTS_DIR} && helm template novapokemon . -f ./values.yaml')

    docs = yaml.safe_load_all(output)

    ingress_doc = None
    stateful_sets = []
    for doc in docs:
        if doc['kind'] == 'StatefulSet' and 'metadata' in doc and 'name' in doc['metadata'] and \
                doc['metadata']['name'] in services:
            stateful_sets.append(doc)
        elif doc['apiVersion'] == "voyager.appscode.com/v1beta1":
            ingress_doc = doc

    if ingress_doc is None:
        print("[ERROR] No ingress chart.")
        exit(1)

    replicas = {}
    ports = {}
    for stateful_set in stateful_sets:
        name = stateful_set['metadata']['name']
        replicas[name] = stateful_set['spec']['replicas']
        ports[name] = stateful_set['spec']['template']['spec']['containers'][0]['ports'][0]['containerPort']

    rules = ingress_doc['spec']['rules']
    for service, num_replicas in replicas.items():
        rules.extend(create_path_rules(service, num_replicas, ports[service]))

    with open(f'{DEPL_CHARTS_DIR}/templates/ingress.yaml', 'w') as f:
        yaml.safe_dump(ingress_doc, f)

    helm_ignore_file('templates/ingress-template.yaml')
    helm_unignore_file('templates/ingress.yaml')


if __name__ == '__main__':
    main()
