#!/bin/bash

clientsnode=$(kubectl get nodes --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}' --selector='clientsnode=true')
hostname=$(hostname)

logs_dir="/tmp/current_client_logs"

if [[ ${hostname} != "$clientsnode" ]]; then
	echo "Running this on node $hostname, instead of $clientsnode. Will ssh and run there."
	echo "Provide username for ssh:"
	username=$(whoami)
	started=$(ssh "$username"@"$clientsnode" 'cat /tmp/current_client_logs/started_at.txt')
	oarsh "$username"@"$clientsnode" 'cd ~/git/NOVAPokemon && bash scripts/save_client_logs.sh'
	dirname="/home/$username/client_logs_collected_$started"
	scp -r "$username"@"$clientsnode":"$dirname" /tmp/client_logs_collected_"$started"
	exit 0
fi

startJobTime=$(cat ${logs_dir}/started_at.txt)
finalFolder="$HOME/client_logs_collected_$startJobTime"
mv ${logs_dir} "$finalFolder"

echo "saved client logs to $finalFolder"
