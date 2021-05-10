#!/bin/bash

numclientnodes=$1

masterNode=$(kubectl get nodes --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}' --selector='node-role.kubernetes.io/master=')
hostnode=$(hostname)

if [[ ${masterNode} != "${hostnode}" ]]; then
	echo "Running this in $hostnode, expected to run in master $masterNode. Will ssh and run there. Username?"
	read -r username
	oarsh "$username"@"$masterNode" 'cd ~/git/NOVAPokemon/ && bash scripts/init.sh'
	exit 0
fi

rm -r /tmp/logs_elastic
mkdir /tmp/logs_elastic

python3 "$NOVAPOKEMON"/scripts/setup_nodes.py $numclientnodes

# VOLUME
kubectl apply -f "${HOME}"/git/NOVAPokemon/deployment-chart/persistentVolumes/elasticSearch-pv.yaml