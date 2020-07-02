#!/bin/bash

time=$(date +%d_%m_%Y__%H_%M_%S)

for pod in $(kubectl get pod --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}'); do
	if [[ $pod =~ "novapokemon-" ]]; then
		continue
	fi

	echo "-------------------------- POD: $pod --------------------------"
	pod_logs=$(kubectl logs "$pod")
	result_races=$(echo "$pod_logs" | grep "WARNING")
	result_error=$(echo "$pod_logs" | grep "error")
	result_fatal=$(echo "$pod_logs" | grep "fatal")

	dir_name="error_logs_$time"
	if [[ $result_races =~ "WARNING" ]]; then
		if ! [[ -d $dir_name ]]; then
			mkdir "$dir_name"
		fi

		echo "FOUND DATA RACES IN $pod"
		echo "$pod_logs" >"$dir_name"/"$pod"_data_race.log
	fi

	if [[ $result_error =~ "error" ]]; then
		if ! [[ -d $dir_name ]]; then
			mkdir "$dir_name"
		fi

		echo "FOUND ERRORS IN $pod"
		echo "$pod_logs" >"$dir_name"/"$pod"_errors.log
	fi

	if [[ $result_fatal =~ "fatal" ]]; then
		if ! [[ -d $dir_name ]]; then
			mkdir "$dir_name"
		fi

		echo "FOUND FATAL IN $pod"
		echo "$pod_logs" >"$dir_name"/"$pod"_fatal.log
	fi

done
