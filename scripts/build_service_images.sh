#!/usr/bin/env bash

ignored_utils="utils"
ignored_mongo_swarm="mongo-swarm"
ignored_scripts="scripts"
ignored_client="client"
ignored_base_image="base_image"
ignored_deployment_config="deployment-chart"

set -e

echo "------------------------------ BUILDING nova-server-base image ------------------------------"


cd base_image

if [ ! -e dockerize ]; then
  echo "Downloading dockerize"
  wget https://github.com/jwilder/dockerize/releases/download/v0.6.1/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
   -O dockerize.tar.gz
  tar -xzvf dockerize.tar.gz
  rm dockerize.tar.gz
fi

docker build . -t novapokemon/nova-server-base
docker push novapokemon/nova-server-base:latest
cd ..


#build images
for d in */; do
  dirname_stripped=$(basename "$d")

  if [ "$dirname_stripped" == $ignored_utils ] || [ "$dirname_stripped" == $ignored_scripts ] ||
     [ "$dirname_stripped" == $ignored_client ] || [ "$dirname_stripped" == $ignored_mongo_swarm ]  ||
     [ "$dirname_stripped" == $ignored_base_image ] || [ "$dirname_stripped" == $ignored_deployment_config ]; then
    continue
  fi

 echo "------------------------------ BUILDING $dirname_stripped executable ------------------------------"

  cd "$d" || exit

  #remove previous binary if already exists
  if [ -e "$dirname_stripped" ]; then
    rm executable
  fi

  # build new binary
  echo "Building binary..."
  GOOS=linux GOARCH=amd64 go build -v -o executable .
  echo "done"

  echo "------------------------------ BUILDING $dirname_stripped image ------------------------------"

  docker build . -t novapokemon/$dirname_stripped:latest
  docker push novapokemon/$dirname_stripped:latest

  echo "done"

  cd .. || exit
done
