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
if [[ $test_race == false ]]; then
	docker push novapokemon/nova-server-base:latest
fi

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
		export GOOS=""
		export GOARCH=""
		race_flag="--race"
		echo "Building binary with RACE DETECTION..."
	else
		export GOOS=linux
		export GOARCH=amd64
		echo "Building binary..."
	fi

	go build $race_flag -v -o executable .
	echo "done"

	echo "------------------------------ BUILDING $dirname_stripped image ------------------------------"

	docker build . -t novapokemon/"$dirname_stripped":$docker_tag
	if [[ $test_race == false ]]; then
		docker push novapokemon/"$dirname_stripped":$docker_tag
	fi
	echo "done"

	#remove binary after building
	if [[ -e executable ]]; then
		rm executable
	fi

	cd .. || exit
done

wait
