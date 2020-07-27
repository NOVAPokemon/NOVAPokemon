#!/bin/bash
# $1 is the flag for race

nodes=$(kubectl get nodes --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}' --selector='serversnode=true')

shopt -s expand_aliases

for node in $nodes
do
  buildCmd="\"cd ${HOME}/git/NOVAPokemon/ && bash scripts/build_service_images.sh ${1}\""
  cmd="bash -ic $buildCmd"
  ssh -t  $node "$cmd"
done

wait

echo "Done"
