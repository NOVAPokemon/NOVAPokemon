#!/bin/bash

masterNode=$(kubectl get nodes --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}' --selector='node-role.kubernetes.io/master=')
hostnode=$(hostname)

if [ $masterNode != $hostnode ]; then
  echo "running this in $hostnode, expected to run in master $masterNode"
  exit 1
fi

mkdir /tmp/logs_elastic

# VOLUME
kubectl apply -f "${HOME}"/git/NOVAPokemon/deployment-chart/pv.yaml

bash scripts/setup_nodes.sh
