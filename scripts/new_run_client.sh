#!/bin/bash

set -e

for job in $(kubectl get job --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}' | grep tester)
do
    echo "deleting $job"
    kubectl delete job ${job}
done

until ! kubectl get pods --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}' 2>&1 | grep tester
do
	echo "waiting for testers to finish"
	sleep 2
done

jobs_file="client/clientJobs.yaml"

groups_out=$(cat client/client_groups.json | python3 -c "\
import sys, json;\
groups = json.load(sys.stdin)['groups'];\
groups = list(map(str, groups))
groups_joined = \" \".join(groups)
print(groups_joined)")

echo "found groups: $groups_out"

group_num=0
for group in $groups_out
do
	echo "adding job for group $group_num with $group clients"
	sed -i "0,/name:.*/{s/name:.*/name: novapokemon-tester-${group_num}-${group}/}" ${jobs_file}
	sed -i "s/value:.*/value: \"$group\"/1" ${jobs_file}
	kubectl apply -f client/clientJobs.yaml
	group_num=$((group_num+1))
done

#bash scripts/build_client.sh
#kubectl apply -f client/clientJobs.yaml

