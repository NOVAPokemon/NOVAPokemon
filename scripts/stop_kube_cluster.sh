#!/bin/bash

set -e

kubectl delete job novapokemon-tester || true
helm uninstall novapokemon

until kubectl get pods 2>&1 | grep "No resources found"
do
	echo "waiting for pods to terminate:"
	echo "$(kubectl get pods --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}')"
	sleep 5
done

bash scripts/save_logs.sh
bash scripts/save_logs_prometheus.sh
