#!/bin/bash

time=$(date +%d_%m_%Y__%H_%M_%S)

error_string="level=error"
fatal_string="level=fatal"

for pod in $(kubectl get pod --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}'); do
	if [[ $pod =~ "novapokemon-" ]]; then
		continue
	fi

	echo "-------------------------- POD: $pod --------------------------"
	pod_logs=$(kubectl logs "$pod")
	result_races=$(echo "$pod_logs" | grep "WARNING")
	result_error=$(echo "$pod_logs" | grep $error_string)
	result_fatal=$(echo "$pod_logs" | grep $fatal_string)

	dir_name="error_logs_$time"
	if [[ $result_races =~ "WARNING" ]]; then
		if ! [[ -d $dir_name ]]; then
			mkdir "$dir_name"
		fi

		echo "FOUND DATA RACES IN $pod"
		echo "$pod_logs" >"$dir_name"/"$pod"_data_race.log
	fi

	if [[ $result_error =~ $error_string ]]; then
		if ! [[ -d $dir_name ]]; then
			mkdir "$dir_name"
		fi

		echo "FOUND ERRORS IN $pod"
		echo "$pod_logs" >"$dir_name"/"$pod"_errors.log
	fi

	if [[ $result_fatal =~ $fatal_string ]]; then
		if ! [[ -d $dir_name ]]; then
			mkdir "$dir_name"
		fi

		echo "FOUND FATAL IN $pod"
		echo "$pod_logs" >"$dir_name"/"$pod"_fatal.log
	fi

done

client_data_race_dir="clients"

for tester in /tmp/current_client_logs/*; do
	if ! [[ -d $tester ]]; then
		continue
	fi

	for client in "$tester"/*; do

		client_stripped=$(basename "$client")
		echo "-------------------------- CLIENT: $client_stripped --------------------------"

		result_races=$(grep "WARNING" "$client")
		result_error=$(grep $error_string "$client")
		result_fatal=$(grep $fatal_string "$client")

		if [[ $result_races =~ "WARNING" ]]; then
			if ! [[ -d $dir_name ]]; then
				mkdir "$dir_name"
			fi

			if ! [[ -d $dir_name/$client_data_race_dir ]]; then
				mkdir "$dir_name/$client_data_race_dir"
			fi
			
			echo "FOUND DATA RACES IN $client_stripped"
			cp "$client" "$dir_name"/$client_data_race_dir/"$client_stripped"_data_race.log
		fi

		if [[ $result_error =~ $error_string ]]; then
			if ! [[ -d $dir_name ]]; then
				mkdir "$dir_name"
			fi

			if ! [[ -d $dir_name/$client_data_race_dir ]]; then
				mkdir "$dir_name/$client_data_race_dir"
			fi
			
			echo "FOUND ERRORS IN $client_stripped"
			cp "$client" "$dir_name"/$client_data_race_dir/"$client_stripped"_errors.log
		fi

		if [[ $result_fatal =~ $fatal_string ]]; then
			if ! [[ -d $dir_name ]]; then
				mkdir "$dir_name"
			fi

			if ! [[ -d $dir_name/$client_data_race_dir ]]; then
				mkdir "$dir_name/$client_data_race_dir"
			fi

			echo "FOUND FATAL IN $client_stripped"
			cp "$client" "$dir_name"/$client_data_race_dir/"$client_stripped"_fatal.log
		fi
	done
done
