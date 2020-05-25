#!/bin/bash

nodes_out=$(kubectl get nodes --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}')
readarray -t nodes <<<"$nodes_out"

if [ ${#nodes[@]} -eq 1 ]; then
  kubectl label nodes "${nodes[0]}" serversnode-
  kubectl label nodes "${nodes[0]}" clientsnode-
  kubectl label nodes "${nodes[0]}" serversnode=true
  kubectl label nodes "${nodes[0]}" clientsnode=true

  exit 1
fi

for ((i=0;i<((${#nodes[@]}-1));i++))
do
  kubectl label nodes "${nodes[$i]}" serversnode-
  kubectl label nodes "${nodes[$i]}" clientsnode-
  kubectl label nodes "${nodes[$i]}" serversnode=true
done

lastNode="${nodes[((${#nodes[@]}-1))]}"
kubectl label nodes "$lastNode" serversnode-
kubectl label nodes "$lastNode" clientsnode-
kubectl label nodes "$lastNode" clientsnode=true