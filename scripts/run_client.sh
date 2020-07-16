#!/bin/bash

set -e

clientsnode=$(kubectl get nodes --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}' --selector='clientsnode=true')
hostname=$(hostname)

if [[ ${hostname} != "$clientsnode" ]]; then
	echo "Running this on node $hostname, instead of $clientsnode. Will ssh and run there."
	echo "Provider username to ssh:"
	read -r username
	ssh "$username"@"$clientsnode" 'cd ~/git/NOVAPokemon/ && bash scripts/run_client.sh'
	exit 0
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

for job in $(kubectl get job --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}' | grep tester); do
	echo "Deleting job: $job"
	kubectl delete job "${job}"
done

echo "Checking for running testers. Waiting for testers to finish..."

until ! kubectl get pods --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}' 2>&1 | grep tester 1>/dev/null 2>&1; do
	sleep 2
done

jobs_file="client/client-jobs-template.yaml"

groups_raw=$(python3 -c "
import sys, json
groups = json.load(sys.stdin)['groups']
client_nums = []
for group in groups:
	client_nums.append(group['num_clients'])
client_nums = list(map(str, client_nums))
client_nums_joined = \" \".join(client_nums)
print(client_nums_joined)" <client/client_groups.json)

regions_raw=$(python3 -c "
import sys, json
groups = json.load(sys.stdin)['groups']
regions = []
for group in groups:
	regions.append(group['region'])
regions = list(map(str, regions))
regions_joined = \" \".join(regions)
print(regions_joined)" <client/client_groups.json)

IFS=' ' read -ra regions <<<"$regions_raw"

echo "$header GROUPS CONFIG $header"

echo "Groups in config: $groups_raw"

# Job template vars
var_image_name="VAR_IMAGE_NAME"
var_client_nums="VAR_CLIENT_NUMS"
var_region="VAR_REGION"

# PV template vars
var_host_path="VAR_HOST_PATH"

client_charts_dirname="client/client_charts"

if [[ ! -d ${client_charts_dirname} ]]; then
	mkdir ${client_charts_dirname}
fi

time=$(date +%d_%m_%Y__%H_%M_%S)

logs_dir="/tmp/current_client_logs"
if [[ -d ${logs_dir} ]]; then
	echo "There are logs in the folder. Do you wish to save them?[y/n]"
	read -r confirmation
	if [[ ${confirmation} == "y" ]]; then
		bash scripts/save_client_logs.sh
	elif [[ ${confirmation} == "n" ]]; then
		echo "Deleting logs..."
		rm -rf "/tmp/current_client_logs/"
	else
		echo "unexpected option $confirmation, exiting..."
		exit 1
	fi
fi

mkdir "$logs_dir"
echo "$time" >"$logs_dir/started_at.txt"
cp client/client_groups.json ${logs_dir}

group_num=0
for number_clients in ${groups_raw}; do
	echo "$header GROUP $group_num $header"

	dirname="$logs_dir/novapokemon_tester_${group_num}"
	mkdir "$dirname"

	echo "Creating job for client group $group_num with $number_clients clients"

	client_chart_name="${client_charts_dirname}/client-group-chart-${group_num}"

	group_region=${regions[$group_num]}

	sed "s/${var_image_name}/novapokemon-tester-${group_num}-${number_clients}/" ${jobs_file} |
		sed "s/${var_client_nums}/$number_clients/" |
		sed "s/${var_region}/$group_region/" |
		sed "s|${var_host_path}|$dirname|" >${client_chart_name}

	echo "Applying client-group-job-$group_num"

	if [[ ${test_run} == false ]]; then
		kubectl apply -f ${client_chart_name}
	fi

	group_num=$((group_num + 1))
done

#bash scripts/build_client.sh
#kubectl apply -f client/clientJobs.yaml
