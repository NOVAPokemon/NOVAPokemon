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

rm -rf build_logs || true
mkdir build_logs

echo "------------------------------ BUILDING SERVICE IMAGES ------------------------------"

for d in */; do
	dirname_stripped=$(basename "$d")

	if [[ "$dirname_stripped" == "$ignored_utils" ]] || [[ "$dirname_stripped" == "$ignored_scripts" ]] ||
		[[ "$dirname_stripped" == "$ignored_client" ]] || [[ "$dirname_stripped" == "$ignored_mongo_swarm" ]] ||
		[[ "$dirname_stripped" == "$ignored_base_image" ]] || [[ "$dirname_stripped" == "$ignored_deployment_config" ]] ||
		[[ "$dirname_stripped" == "$ignored_logs" ]] || [[ "$dirname_stripped" == "build_logs" ]]; then
		continue
	fi

	cd "$d" || exit

	#remove previous binary if already exists
	if [[ -e executable ]]; then
		rm executable
	fi
	echo "Starting build and push of image for service: ${dirname_stripped}"
	if [[ -e ../build_logs/"$dirname_stripped" ]]; then
		rm ../build_logs/"$dirname_stripped"
	fi
	touch ../build_logs/"$dirname_stripped"

	# build new binary
	race_flag=""
	if [[ $test_race == true ]]; then
		export GOOS=""
		export GOARCH=""
		race_flag="--race"
		echo "Building $dirname_stripped with RACE DETECTION..."
		go-1.14 build $race_flag -v -o executable .
	else
		export GOOS=linux
		export GOARCH=amd64
		echo "Building $dirname_stripped..."
		go build $race_flag -v -o executable .
	fi

	docker build . -t novapokemon/"$dirname_stripped":$docker_tag >../build_logs/"$dirname_stripped"
	if [[ $test_race == false ]]; then
		docker push novapokemon/"$dirname_stripped":$docker_tag >../build_logs/"$dirname_stripped"
	fi
	echo "Done building and pushing image for service: ${dirname_stripped}"
	if [[ -e executable ]]; then
		rm executable
	fi

	cd .. || exit
done

echo "Waiting for finish..."
wait

for f in build_logs/*; do
	echo ""
	cat "${f}"
done
rm -rf build_logs
