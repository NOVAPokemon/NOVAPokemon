#!/bin/bash

# PROXY
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.0.0/aio/deploy/recommended.yaml

kubectl create serviceaccount cluster-admin-dashboard-sa
kubectl create clusterrolebinding cluster-admin-dashboard-sa \
--clusterrole=cluster-admin \
--serviceaccount=default:cluster-admin-dashboard-sa
kubectl describe secret cluster-admin-dashboard-sa-token | grep token:

kubectl proxy &

echo "Link:http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/"

# VOLUME
kubectl apply -f "${HOME}"/git/NOVAPokemon/deployment-chart/pv.yaml