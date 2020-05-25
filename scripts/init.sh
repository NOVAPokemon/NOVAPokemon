#!/bin/bash
# VOLUME
kubectl apply -f "${HOME}"/git/NOVAPokemon/deployment-chart/persistentVolumes/elasticSearch-pv.yaml
kubectl apply -f "${HOME}"/git/NOVAPokemon/deployment-chart/persistentVolumes/prometheus-pvs.yaml
kubectl apply -f "${HOME}"/git/NOVAPokemon/deployment-chart/persistentVolumes/prometheus-alertmanager-pvc.yaml
kubectl apply -f "${HOME}"/git/NOVAPokemon/deployment-chart/persistentVolumes/prometheus-server-pvc.yaml