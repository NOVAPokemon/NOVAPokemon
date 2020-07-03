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

client_data_race_dir="clients"

for tester in /tmp/current_client_logs/*; do
	tester="/tmp/current_client_logs/$tester"
	if ! [[ -d $tester ]]; then
		continue
	fi

	for client in "$tester"/*; do

		echo "-------------------------- CLIENT: $client --------------------------"
		client="$tester/$client"

		result_races=$(grep "WARNING" "$client")
		result_error=$(grep "error" "$client")
		result_fatal=$(grep "fatal" "$client")

		if [[ $result_races =~ "WARNING" ]]; then
			if ! [[ -d $dir_name ]]; then
				mkdir "$dir_name"
			fi

			if ! [[ -d $dir_name/$client_data_race_dir ]]; then
				mkdir "$dir_name/$client_data_race_dir"
			fi

			echo "FOUND DATA RACES IN $client"
			cp "$client" "$dir_name"/$client_data_race_dir/"$client"_data_race.log
		fi

		if [[ $result_error =~ "error" ]]; then
			if ! [[ -d $dir_name ]]; then
				mkdir "$dir_name"
			fi

			if ! [[ -d $dir_name/$client_data_race_dir ]]; then
				mkdir "$dir_name/$client_data_race_dir"
			fi

			echo "FOUND ERRORS IN $client"
			cp "$client" "$dir_name"/$client_data_race_dir/"$client"_errors.log
		fi

		if [[ $result_fatal =~ "fatal" ]]; then
			if ! [[ -d $dir_name ]]; then
				mkdir "$dir_name"
			fi

			if ! [[ -d $dir_name/$client_data_race_dir ]]; then
				mkdir "$dir_name/$client_data_race_dir"
			fi

			echo "FOUND FATAL IN $client"
			cp "$client" "$dir_name"/$client_data_race_dir/"$client"_fatal.log
		fi
	done
done
