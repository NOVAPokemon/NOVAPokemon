#!/bin/bash

set -e

# kill client jobs
header="-------------------------"

echo "$header DELETING JOBS $header"

for job in $(kubectl get job --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}' | grep tester); do
	echo "Deleting job: $job"
	kubectl delete job "${job}"
done

# kill cluster
helm uninstall novapokemon

# wait for cluster to finish
echo "waiting for pods to terminate"
until kubectl get pods 2>&1 | grep "No resources found"; do
	sleep 5
done

# collect cluster and client logs
bash scripts/save_logs.sh
bash scripts/save_client_logs.sh
