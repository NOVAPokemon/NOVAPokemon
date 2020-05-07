#!/usr/bin/env bash

#!/bin/bash

ignored_utils="utils"
ignored_mongo_swarm="mongo-swarm"
ignored_scripts="scripts"
ignored_client="client"
ignored_base_image="base_image"

set -e

#build images
for d in */; do
  dirname_stripped=$(basename "$d")

  if [ "$dirname_stripped" == $ignored_utils ] || [ "$dirname_stripped" == $ignored_scripts ] ||
     [ "$dirname_stripped" == $ignored_client ] || [ "$dirname_stripped" == $ignored_mongo_swarm ]  ||
     [ "$dirname_stripped" == $ignored_base_image ]; then
    continue
  fi

  echo "------------------------------ BUILDING $dirname_stripped ------------------------------"

  cd "$d" || exit

  docker build . -t $dirname_stripped

  cd .. || exit
done
