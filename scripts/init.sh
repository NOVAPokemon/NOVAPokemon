#!/bin/bash
# VOLUME
kubectl apply -f "${HOME}"/git/NOVAPokemon/deployment-chart/pv.yaml

bash scripts/setup_nodes.sh
