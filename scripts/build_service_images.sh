#!/usr/bin/env bash

ignored_utils="utils"
ignored_mongo_swarm="mongo-swarm"
ignored_scripts="scripts"
ignored_client="client"
ignored_base_image="base_image"
ignored_deployment_config="deployment-chart"
ignored_logs="logs"

DOCKERIZE_VERSION=v0.6.1

set -e

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

echo "------------------------------ BUILDING nova-server-base image ------------------------------"

cd base_image

if [[ ! -e dockerize ]]; then
	echo "Downloading dockerize"
	wget https://github.com/jwilder/dockerize/releases/download/v0.6.1/dockerize-linux-amd64-"$DOCKERIZE_VERSION".tar.gz \
		-O dockerize.tar.gz
	tar -xzvf dockerize.tar.gz
	rm dockerize.tar.gz
fi

docker build . -t novapokemon/nova-server-base
docker push novapokemon/nova-server-base:latest

cd ..

docker_tag=""

if [[ $test_race == true ]]; then
	docker_tag="race"
else
	docker_tag="latest"
fi

#build images
for d in */; do
	dirname_stripped=$(basename "$d")

	if [[ "$dirname_stripped" == "$ignored_utils" ]] || [[ "$dirname_stripped" == "$ignored_scripts" ]] ||
		[[ "$dirname_stripped" == "$ignored_client" ]] || [[ "$dirname_stripped" == "$ignored_mongo_swarm" ]] ||
		[[ "$dirname_stripped" == "$ignored_base_image" ]] || [[ "$dirname_stripped" == "$ignored_deployment_config" ]] ||
		[[ "$dirname_stripped" == "$ignored_logs" ]]; then
		continue
	fi

	echo "------------------------------ BUILDING $dirname_stripped executable ------------------------------"

	cd "$d" || exit

	#remove previous binary if already exists
	if [[ -e executable ]]; then
		rm executable
	fi

	# build new binary
	race_flag=""
	if [[ $test_race == true ]]; then
		race_flag="--race"
		echo "Building binary with RACE DETECTION..."
	else
		echo "Building binary..."
	fi

	GOOS=linux GOARCH=amd64 go build $race_flag -v -o executable .
	echo "done"

	echo "------------------------------ BUILDING $dirname_stripped image ------------------------------"

	


	docker build . -t novapokemon/"$dirname_stripped":$docker_tag
	docker push novapokemon/"$dirname_stripped":$docker_tag
	echo "done"

	#remove binary after building
	if [[ -e executable ]]; then
		rm executable
	fi

	cd .. || exit
done

wait
