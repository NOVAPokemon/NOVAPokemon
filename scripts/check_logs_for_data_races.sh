#!/bin/bash

time=$(date +%d_%m_%Y__%H_%M_%S)

for pod in $(kubectl get pod --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}'); do
	if [[ $pod =~ "novapokemon-" ]]; then
		continue
	fi

	echo "-------------------------- POD: $pod --------------------------"
	pod_logs=$(kubectl logs "$pod")
	result=$(echo "$pod_logs" | grep "WARNING")
	dir_name="data_race_logs_$time"

	if [[ $result =~ "WARNING" ]]; then
		if ! [[ -d $dir_name ]]; then
			mkdir "$dir_name"
		fi

		echo "FOUND DATA RACES IN $pod"
		echo "$pod_logs" >"$dir_name"/"$pod"_data_race.log
	fi
done
