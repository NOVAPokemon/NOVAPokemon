#!/bin/bash

for pod in $(kubectl get pod --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}'); do
	echo "-------------------------- POD: $pod --------------------------"
	result=$(kubectl logs "$pod" | grep "WARNING")
	time=$(date +%d_%m_%Y__%H_%M_%S)
	dir_name="data_race_logs_$time"

	if [[ $result =~ "WARNING" ]]
	then
		if ! [[ -d $dir_name ]]
		then
			mkdir "$dir_name"
		fi

		echo "FOUND DATA RACES IN $pod"
		kubectl logs "$pod" > "$dir_name"/"$pod"_data_race.log
	fi
done