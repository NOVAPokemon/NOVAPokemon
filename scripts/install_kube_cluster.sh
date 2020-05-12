#!/bin/bash

set -e
helm uninstall novapokemon || true
bash scripts/build_service_images.sh
cd deployment-chart
helm dependency update
kubectl taint nodes --all node-role.kubernetes.io/master- || true
helm upgrade --install novapokemon . -f ./values.yaml
cd ..
