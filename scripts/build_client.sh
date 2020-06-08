#!/bin/bash

set -e

cd client || exit

echo "------------------------------ BUILDING CLIENT ------------------------------"

#remove previous binary if already exists
if [[ -e executable ]]; then
	rm executable
fi

test_race=false

while getopts 'r' flag; do
	case "${flag}" in
	r)
		test_race=true
		;;
	*)
		print_usage
		exit 1
		;;
	esac
done

# build new binary
race_flag=""
if [[ $test_race == true ]]; then
	race_flag="--race"
	echo "Building binary with RACE DETECTION..."
else
	echo "Building binary..."
fi

GOOS=linux GOARCH=amd64 go build $race_flag -o executable .

cd .. || exit

docker build client -t novapokemon/client:latest
docker push novapokemon/client:latest
