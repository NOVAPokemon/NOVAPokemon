#!/bin/bash

masterNode=$(kubectl get nodes --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}' --selector='node-role.kubernetes.io/master=')
hostnode=$(hostname)

if [ $masterNode != $hostnode ]; then
	echo "Running this in $hostnode, expected to run in master $masterNode. Will ssh and run there. Username?"
	read -r username
	ssh "$username"@"$masterNode" 'cd ~/git/NOVAPokemon/ && bash scripts/init.sh'
	exit 0
fi

mkdir /tmp/logs_elastic
mkdir /tmp/logs_prometheusAlertManager
mkdir /tmp/logs_prometheusServer

bash scripts/setup_nodes.sh

# VOLUME
kubectl apply -f "${HOME}"/git/NOVAPokemon/deployment-chart/persistentVolumes/elasticSearch-pv.yaml
kubectl apply -f "${HOME}"/git/NOVAPokemon/deployment-chart/persistentVolumes/prometheus-pvs.yaml
kubectl apply -f "${HOME}"/git/NOVAPokemon/deployment-chart/persistentVolumes/prometheus-alertmanager-pvc.yaml
kubectl apply -f "${HOME}"/git/NOVAPokemon/deployment-chart/persistentVolumes/prometheus-server-pvc.yaml
