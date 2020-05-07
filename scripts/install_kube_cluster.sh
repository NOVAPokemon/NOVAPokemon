#!/bin/bash -ex

set -e

helm uninstall novapokemon || true
bash scripts/build_service_images.sh
cd deployment-chart
helm upgrade --install novapokemon . -f ./values.yaml
cd ..
