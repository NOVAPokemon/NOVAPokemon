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
	echo "Building binary with RACE DETECTION..."
	echo "WARNING: BE CAREFUL, THIS BUILDS WITHOUT OS AND ARCH FLAGS DUE TO INCOMPATIBILITY"
else
	os_flag="GOOS=linux"
	arch_flag="GOARCH=amd64"
	echo "Building binary..."
fi

mv create_thread_clients.c ../
$os_flag $arch_flag go build $race_flag -o executable .
mv ../create_thread_clients.c .

cd .. || exit

docker build client -t novapokemon/client:latest
docker push novapokemon/client:latest
