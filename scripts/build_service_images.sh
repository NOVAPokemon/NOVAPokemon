#!/usr/bin/env bash

ignored_utils="utils"
ignored_mongo_swarm="mongo-swarm"
ignored_scripts="scripts"
ignored_client="client"
ignored_base_image="base_image"
ignored_deployment_config="deployment-chart"
ignored_logs="logs"
ignored_map_viewer="map-viewer"
ignored_results="results"
ignored_images="images"
ignored_venv="venv"
ignored_build_logs="build_logs"

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
cp ../location_tags.json .
cp ../delays_config.json .
cp ../client_delays.json .
cp ../cells_to_region.json .
cp ../lat.txt .
cp ../locations.json .

if [[ ! -e dockerize ]]; then
	echo "Downloading dockerize"
	wget https://github.com/jwilder/dockerize/releases/download/v0.6.1/dockerize-linux-amd64-"$DOCKERIZE_VERSION".tar.gz \
		-O dockerize.tar.gz
	tar -xzvf dockerize.tar.gz
	rm dockerize.tar.gz
fi

docker build . -t brunoanjos/nova-server-base
if [[ $test_race == false ]]; then
	docker push brunoanjos/nova-server-base:latest
fi

rm location_tags.json
rm delays_config.json
rm client_delays.json
rm cells_to_region.json
rm lat.txt
rm locations.json

cd ..

docker_tag="latest"

rm -rf build_logs || true
mkdir build_logs

echo "------------------------------ BUILDING SERVICE IMAGES ------------------------------"

rm -rf images/*

for d in */; do
	dirname_stripped=$(basename "$d")

	if [[ "$dirname_stripped" == "$ignored_utils" ]] || [[ "$dirname_stripped" == "$ignored_scripts" ]] ||
		[[ "$dirname_stripped" == "$ignored_client" ]] || [[ "$dirname_stripped" == "$ignored_mongo_swarm" ]] ||
		[[ "$dirname_stripped" == "$ignored_base_image" ]] || [[ "$dirname_stripped" == "$ignored_deployment_config" ]] ||
		[[ "$dirname_stripped" == "$ignored_logs" ]] || [[ "$dirname_stripped" == "$ignored_build_logs" ]] ||
		[[ "$dirname_stripped" == "$ignored_map_viewer" ]] || [[ "$dirname_stripped" == "$ignored_results" ]] ||
		[[ "$dirname_stripped" == "$ignored_images" ]] || [[ "$dirname_stripped" == "$ignored_venv" ]];
	  then
		continue
	fi

	cd "$d" || exit

	#remove previous binary if already exists
	if [[ -e executable ]]; then
		rm executable
	fi
	echo "Starting build of image for service: ${dirname_stripped}"
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
		go build $race_flag -v -o executable .
	else
		export GOOS=linux
		export GOARCH=amd64
		echo "Building $dirname_stripped..."
		go build $race_flag -v -o executable .
	fi

	docker build . -t brunoanjos/"$dirname_stripped":$docker_tag >../build_logs/"$dirname_stripped"
	if [ -f ../images/"$dirname_stripped".tar ]; then
    rm ../images/"$dirname_stripped".tar
  fi
	docker save brunoanjos/"$dirname_stripped":$docker_tag > ../images/"$dirname_stripped".tar

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
