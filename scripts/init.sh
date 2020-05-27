#!/bin/bash

masterNode=$(kubectl get nodes --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}' --selector='node-role.kubernetes.io/master=')
hostnode=$(hostname)

if [ $masterNode != $hostnode ]; then
  echo "running this in $hostnode, expected to run in master $masterNode"
  exit 1
fi

mkdir /tmp/logs_elastic
mkdir /tmp/logs_prometheusAlertManager
mkdir /tmp/logs_prometheusServer

# VOLUME
kubectl apply -f "${HOME}"/git/NOVAPokemon/deployment-chart/persistentVolumes/elasticSearch-pv.yaml
kubectl apply -f "${HOME}"/git/NOVAPokemon/deployment-chart/persistentVolumes/prometheus-pvs.yaml
kubectl apply -f "${HOME}"/git/NOVAPokemon/deployment-chart/persistentVolumes/prometheus-alertmanager-pvc.yaml
kubectl apply -f "${HOME}"/git/NOVAPokemon/deployment-chart/persistentVolumes/prometheus-server-pvc.yaml
