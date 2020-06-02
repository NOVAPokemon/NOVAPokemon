#!/bin/bash

set -e

# kill client jobs
kubectl delete job novapokemon-tester || true

# kill cluster
helm uninstall novapokemon

# wait for cluster to finish
until kubectl get pods 2>&1 | grep "No resources found"
do
	echo "waiting for pods to terminate:"
	kubectl get pods --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}'
	sleep 5
done

# collect cluster and client logs
bash scripts/save_logs.sh
bash scripts/save_client_logs.sh