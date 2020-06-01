#!/bin/bash

clientsnode=$(kubectl get nodes --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}' --selector='clientsnode=true')
hostname=$(hostname)

logs_dir="/tmp/current_client_logs" 

if [[ $hostname != "$clientsnode" ]]
then
	echo "Running this on node $hostname, instead of $clientsnode. Will ssh and run there. Provider username to ssh:"
	read -r username
	ssh "$username"@"$clientsnode" 'cd ~/git/NOVAPokemon && bash scripts/save_client_logs.sh'
	started=$(ssh "$username"@"$clientsnode" 'cat ~/git/NOVAPokemon/client/started_at')
	scp -R "$username"@"$clientsnode":/tmp/client_logs_collected_"$started" /tmp/client_logs_collected_"$started"
	exit 0
fi

startJobTime=$(cat client/started_at)
mv $logs_dir "/tmp/client_logs_collected_$startJobTime"
cp "client/started_at" "client_logs_collected_$startJobTime" 
