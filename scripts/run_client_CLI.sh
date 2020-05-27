#!/bin/bash

set -e

if [[ $# -ne  1 ]]; then
  echo "usage: ./scripts/run_client_CLI <clientName>"
  exit 1
fi

#bash scripts/build_client.sh
kubectl delete pod "$1" || true
kubectl run -i -t --image novapokemon/client:latest \
  --env AUTHENTICATION_URL="authentication-service:8001" \
  --env BATTLES_URL="battles-service:8002" \
  --env GYM_URL="gym-service:8003" \
  --env LOCATION_URL="location-service:8004" \
  --env MICROTRANSACTIONS_URL="microtransactions-service:8005" \
  --env NOTIFICATIONS_URL="notifications-service:8006" \
  --env STORE_URL="store-service:8007" \
  --env TRADES_URL="trades-service:8008" \
  --env TRAINERS_URL="trainers-service:8009" \
  "$1" --restart=Never \
  --overrides='{ "apiVersion": "v1", "spec": { "template": { "spec": { "nodeSelector": { "clientsnode": "true" }, "containers": { "securityContext": { "capabilities": { "add": "NET_ADMIN" } } } } } } }'
