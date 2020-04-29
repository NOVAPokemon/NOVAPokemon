#!/bin/bash

ignored_utils="utils"
ignored_mongo_swarm="mongo-swarm"
ignored_scripts="scripts"
ignored_client="client"
ignored_base_image="base_image"

set -e

#build binaries
for d in */; do
  dirname_stripped=$(basename "$d")

  if [ "$dirname_stripped" == $ignored_utils ] || [ "$dirname_stripped" == $ignored_scripts ] ||
     [ "$dirname_stripped" == $ignored_client ] || [ "$dirname_stripped" == $ignored_mongo_swarm ]  ||
     [ "$dirname_stripped" == $ignored_base_image ]; then
    continue
  fi

  echo "------------------------------ BUILDING $dirname_stripped ------------------------------"

  cd "$d" || exit

  #remove previous binary if already exists
  if [ -e "$dirname_stripped" ]; then
    rm executable
  fi

  # build new binary
  echo "Building binary..."
  GOOS=linux GOARCH=amd64 go build -v -o executable .

  cd .. || exit
done
