#!/bin/bash

set -e

#bash scripts/build_service_images.sh
helm uninstall novapokemon 2>/dev/null || true

cd deployment-chart
helm dependency update
#kubectl taint nodes --all node-role.kubernetes.io/master- || true
helm upgrade --install novapokemon . -f ./values.yaml

# grafana dashboard
kubectl delete cm grafana-dashboard-default || true
kubectl create configmap grafana-dashboard-default --from-file="$(pwd)/utils/grafana_dashboard.json" -o yaml || true
kubectl label cm grafana-dashboard-default grafana_dashboard=1

# dashboard
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.0.0/aio/deploy/recommended.yaml
kubectl create serviceaccount dashboard -n default || true
kubectl create clusterrolebinding dashboard-admin -n default --clusterrole=cluster-admin --serviceaccount=default:dashboard || true

echo "---Dashboard key---"
kubectl get secret "$(kubectl get serviceaccount dashboard -o jsonpath="{.secrets[0].name}")" -o jsonpath="{.data.token}" | base64 --decode
echo ""
echo "---end---"
killall kubectl 2>/dev/null || true && kubectl proxy --address 0.0.0.0 2>/dev/null &
echo "Dashboard url: http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/#/login"
cd ..
