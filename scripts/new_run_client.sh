#!/bin/bash

set -e

clientsnode=$(kubectl get nodes --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}' --selector='clientsnode=true')
hostname=$(hostname)

if [[ hostname != clientsnode ]]
then
  echo "Running this on node $hostname, instead of $clientsnode. Exiting..."
  exit 1
fi

test_run=false

while getopts ":t" opt; do
  case ${opt} in
    t)
      test_run=true
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
  esac
done

header="-------------------------"

echo "$header DELETING JOBS $header"

for job in $(kubectl get job --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}' | grep tester)
do
    echo "Deleting job: $job"
    kubectl delete job "${job}"
done

until ! kubectl get pods --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}' 2>&1 | grep tester 1>/dev/null 2>&1
do
	echo "waiting for testers to finish"
	sleep 2
done

jobs_file="client/client-jobs-template.yaml"

groups_out=$(python3 -c "\
import sys, json;\
groups = json.load(sys.stdin)['groups'];\
groups = list(map(str, groups))
groups_joined = \" \".join(groups)
print(groups_joined)" < client/client_groups.json)

echo "$header GROUPS CONFIG $header"

echo "Groups in config: $groups_out"

# Job template vars
var_image_name="VAR_IMAGE_NAME"
var_client_nums="VAR_CLIENT_NUMS"

# PV template vars
var_host_path="VAR_HOST_PATH"

client_charts_dirname="client/client_charts"

if [[ ! -d ${client_charts_dirname} ]]
then
    mkdir ${client_charts_dirname}
fi

time=$(date +%d_%m_%Y__%H_%M_%S)
logs_dir="/tmp/client_logs_${time}"
mkdir "$logs_dir"

group_num=0
for number_clients in ${groups_out}
do
    echo "$header GROUP $group_num $header"

    dirname="$logs_dir/novapokemon_tester_${group_num}"
    mkdir "$dirname"

    echo "Creating job for client group $group_num with $number_clients clients"
    
    client_chart_name="${client_charts_dirname}/client-group-chart-${group_num}"

    sed "s/${var_image_name}/novapokemon-tester-${group_num}-${number_clients}/" ${jobs_file} | \
    sed "s/${var_client_nums}/$number_clients/" | \
    sed "s|${var_host_path}|$dirname|" > ${client_chart_name}

    echo "Applying client-group-job-$group_num"

    if [[ ${test_run} = false ]]
    then
	    kubectl apply -f ${client_chart_name}
    fi

    group_num=$((group_num+1))
done

#bash scripts/build_client.sh
#kubectl apply -f client/clientJobs.yaml

