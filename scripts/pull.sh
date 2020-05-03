#!/bin/bash

ignored_scripts="scripts/"
ignored_base_image="base_image/"

for d in */; do
	if [ "$d" == $ignored_scripts ] || [ "$d" == $ignored_base_image ]; then
		continue
	fi
	cd "$d" || exit
	git pull
	cd .. || exit
done
