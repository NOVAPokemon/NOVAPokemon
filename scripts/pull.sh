#!/bin/bash

ignored_scripts="scripts/"
ignored_base_image="base_image/"
ignored_mongo_swarm="mongo-swarm/"

for d in */; do
	if [ "$d" == $ignored_scripts ] || [ "$d" == $ignored_base_image ] || [ "$d" == $ignored_mongo_swarm ]; then
		continue
	fi
	cd "$d" || exit
	git pull
	cd .. || exit
done
