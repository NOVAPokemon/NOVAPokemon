#!/bin/bash

nodes_out=$(kubectl get nodes --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}')
readarray -t nodes <<<"$nodes_out"


for ((i=0;i<((${#nodes[@]}-1));i++))
do
  kubectl label nodes "${nodes[$i]}" nodetype-
  kubectl label nodes "${nodes[$i]}" nodetype=servers
done

lastNode="${nodes[((${#nodes[@]}-1))]}"
kubectl label nodes "$lastNode" nodetype-
kubectl label nodes "$lastNode" nodetype=clients