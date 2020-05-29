#!/bin/bash

set -e

for job in $(kubectl get pods --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}' | grep tester)
do
    echo "deleting $job"
    kubectl delete pod ${job}
done

jobs_file="client/clientJobs.yaml"

groups=$(cat client/client_groups.json | python3 -c "\
import sys, json;\
groups = json.load(sys.stdin)['groups'];\
[print(group) for group in groups]")

for group in ${groups}
do
	sed -i "s/value:.*/value: $group/1" ${jobs_file}
	#kubectl apply -f client/clientJobs.yaml
done

#bash scripts/build_client.sh
#kubectl apply -f client/clientJobs.yaml

