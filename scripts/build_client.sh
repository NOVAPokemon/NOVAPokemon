#!/bin/bash

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
	export GOOS=""
	export GOARCH=""
	echo "Building binary with RACE DETECTION..."
	echo "WARNING: BE CAREFUL, THIS BUILDS WITHOUT OS AND ARCH FLAGS DUE TO INCOMPATIBILITY"
else
	export GOOS=linux
	export GOARCH=amd64
	echo "Building binary..."
fi

mv create_thread_clients.c ../
go build $race_flag -o executable .
mv ../create_thread_clients.c .

cd .. || exit

if [[ $test_race == true ]]; then
	docker build client -t novapokemon/client:race
else
	docker build client -t novapokemon/client:latest
	docker push novapokemon/client:latest
fi


