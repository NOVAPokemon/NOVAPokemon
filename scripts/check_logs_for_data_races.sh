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

client_data_race_dir="clients"

for tester in $(ls /tmp/current_client_logs/)
do
	tester="/tmp/current_client_logs/$tester"
	if ! [[ -d $tester ]]; then
		continue
	fi

	for client in $(ls $tester)
	do
		
		echo "-------------------------- CLIENT: $client --------------------------"
		client="$tester/$client"

		result=$(cat $client | grep "WARNING")

		if [[ $result =~ "WARNING" ]]; then
			if ! [[ -d $dir_name ]]; then
                        	mkdir "$dir_name"
                	fi

			if ! [[ -d $dir_name/$client_data_race_dir ]]; then
				mkdir "$dir_name/$client_data_race_dir"
			fi

                	echo "FOUND DATA RACES IN $client"
                	cp $client $dir_name/$client_data_race_dir/
		fi
	done
done
