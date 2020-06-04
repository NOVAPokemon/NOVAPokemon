#!/bin/bash

set -e

header="-------------------------"
subheader="-------"

if (( $# != 1))
then
	echo "Please provide only one argument with the log folder name."
fi

log_folder=$1

if [[ ! -e $log_folder/started_at.txt ]]
then
	"This folder does not contain the started_at file. Possibly you selected the wrong logs folder."
	exit 1
fi

started=$(cat "$log_folder/started_at.txt")
echo "Logs from run started at: $started"

if [[ ! -e $log_folder/client_groups.json ]]
then
	"This folder does not contain the client_groups file. Possibly you selected the wrong logs folder."
	exit 1
fi

for tester_logs in "$log_folder"/*/
do
	echo "$header COLLECTING $tester_logs $header"
	for client_log in "$tester_logs"*
	do
		echo "$subheader LOG $client_log $subheader"

		prefix="average battle: "

		values=$(grep -oP "${prefix}\K([0-9]+[.]?[0-9]+)(?= ms)" "$client_log")
		readarray -t array_values <<<"$values"

		if [[ ${#array_values[@]} -gt 0 ]]
		then
			times=$array_values[0]
			for value in "${array_values[@]}"
				times=$array_values[]
			do
				
			done
		fi
	done
done 