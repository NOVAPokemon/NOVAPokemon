#!/bin/bash

set -e

helm uninstall novapokemon || true
bash scripts/build_service_images.sh
cd deployment-chart
helm dependency update
helm upgrade --install novapokemon . -f ./values.yaml
cd ..
