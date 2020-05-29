#!/bin/bash

set -e

test_run=false

while getopts ":t" opt; do
  case ${opt} in
    a)
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
    kubectl delete job ${job}
done

echo "$header DELETING PVs $header"

for pv in $(kubectl get pv | grep tester)
do
    echo "Deleting pv: $pv"
    kubectl delete pv ${pv}
done

until ! kubectl get pods --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}' 2>&1 | grep tester 2>&1 1>/dev/null
do
	echo "waiting for testers to finish"
	sleep 2
done

jobs_file="client/client-jobs-template.yaml"

groups_out=$(cat client/client_groups.json | python3 -c "\
import sys, json;\
groups = json.load(sys.stdin)['groups'];\
groups = list(map(str, groups))
groups_joined = \" \".join(groups)
print(groups_joined)")

echo "$header GROUPS CONFIG $header"

echo "Groups in config: $groups_out"

# Job template vars
var_image_name="VAR_IMAGE_NAME"
var_client_nums="VAR_CLIENT_NUMS"

# PV template vars
var_client_pv_name="VAR_CLIENT_PV_NAME"
var_client_pv_path="VAR_CLIENT_PV_PATH"

client_job_charts="client/clients_charts_applied"
client_pvs_dirname="client/client_pvs"

mkdir ${client_job_charts}
mkdir ${client_pvs_dirname}

group_num=0
for number_clients in ${groups_out}
do

    echo "$header GROUP $group_num $header"

    echo "Creating client group PV ($group_num)"

    time=$(date +%d_%m_%Y__%H_%M_%S)
    dirname="/tmp/client_logs_${time}/novapokemon-tester-${group_num}"
    mkdir dirname

    client_pv_name="${client_pvs_dirname}/client-group-pv-${group_num}"

    sed "s/${var_client_pv_name}/novapokemon-pv-${group_num}/" | \
    sed "s|${var_client_pv_path}|${dirname}|" > ${client_pv_name}

    echo "Applying client-group-pv-$group_num"

    if [[ ! ${test_run} ]]
    then
        kubectl apply -f ${client_pv_name}
    fi

	echo "Creating job for client group $group_num with $number_clients clients"

	sed "s/${var_image_name}/novapokemon-tester-${group_num}-${number_clients}/" ${jobs_file} | \
	sed "s/${var_client_nums}/$number_clients/" ${jobs_file} > client-group-job-${group_num}

    echo "Applying client-group-job-$group_num"

    if [[ ! ${test_run} ]]
    then
	    kubectl apply -f client/client-group-job-${group_num}.yaml
    fi

	group_num=$((group_num+1))
done

#bash scripts/build_client.sh
#kubectl apply -f client/clientJobs.yaml

