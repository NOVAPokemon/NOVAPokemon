#!/bin/bash

set -e

kubectl delete job novapokemon-tester || true
bash scripts/build_client.sh
kubectl apply -f client/clientJobs.yaml
