#!/bin/bash

for pod in $(kubectl get pod --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}'); do
	echo "-------------------------- POD: $pod --------------------------"
	result=$(kubectl logs "$pod" | grep "WARNING")
	time=$(date +%d_%m_%Y__%H_%M_%S)
	dir_name="data_race_logs_"$time""
	mkdir $dir_name

	if [[ $result =~ "WARNING" ]]
	then
		echo "FOUND DATA RACES IN $pod"
		kubeclt logs "$pod" > "$dir_name"/"$pod"_data_race.log
	fi
done