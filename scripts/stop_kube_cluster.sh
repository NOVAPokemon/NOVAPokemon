#!/bin/bash

set -e

header="-------------------------"
echo "$header DELETING JOBS $header"

# kill client jobs
for job in $(kubectl get job --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}' | grep clients); do
	echo "Deleting job: $job"
	kubectl delete job "${job}"
done

# kill cluster
helm uninstall novapokemon || true
helm uninstall voyager-operator || true

# wait for cluster to finish
echo "waiting for pods to terminate"
until kubectl get pods 2>&1 | grep "No resources found"; do
	sleep 5
done
