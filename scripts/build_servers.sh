#!/bin/bash

ignored_utils="utils"
ignored_scripts="scripts"
ignored_client="client"

set -e

DOCKERIZE_VERSION=v0.6.1

#build binaries
for d in */; do
  dirname_stripped=$(basename "$d")

  if [ "$dirname_stripped" == $ignored_utils ] || [ "$dirname_stripped" == $ignored_scripts ] ||
    [ "$dirname_stripped" == $ignored_client ]; then
    continue
  fi

  echo "------------------------------ BUILDING $dirname_stripped ------------------------------"

  cd "$d" || exit

  if [ ! -e dockerize ]; then
    echo "Downloading dockerize"
    wget https://github.com/jwilder/dockerize/releases/download/v0.6.1/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz -O dockerize.tar.gz
    tar -xzvf dockerize.tar.gz
    rm dockerize.tar.gz
  fi

  #remove previous binary if already exists
  if [ -e "$dirname_stripped" ]; then
    rm executable
  fi

  # build new binary
  echo "Building binary..."
  go build -o executable .

  cd .. || exit
done
