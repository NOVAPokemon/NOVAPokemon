#!/bin/bash

set -e

kubectl delete job novapokemon-tester || true
helm uninstall novapokemon
echo "waiting 1m for pods to finish and collect logs..."
sleep 15s
echo "15s..."
sleep 15s
echo "30s..."
sleep 15s
echo "45s..."
sleep 15s
echo "done"
bash scripts/save_logs.sh
