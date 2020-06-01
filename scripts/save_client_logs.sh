#!/bin/bash

clientsnode=$(kubectl get nodes --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}' --selector='clientsnode=true')
hostname=$(hostname)

logs_dir="/tmp/current_client_logs" 

if [[ $hostname != "$clientsnode" ]]
then
	echo "Running this on node $hostname, instead of $clientsnode. Will ssh and run there. Provider username to ssh:"
	read -r username
	started=$(ssh "$username"@"$clientsnode" 'cat $logs_dir/started_at.txt')
	ssh "$username"@"$clientsnode" 'cd ~/git/NOVAPokemon && bash scripts/save_client_logs.sh'
	scp -r "$username"@"$clientsnode":/tmp/client_logs_collected_"$started" /tmp/client_logs_collected_"$started"
	exit 0
fi

startJobTime=$(cat $logs_dir/started_at.txt)
finalFolder="/tmp/client_logs_collected_$startJobTime"
mv $logs_dir "$finalFolder"

echo "saved client logs to $finalFolder"