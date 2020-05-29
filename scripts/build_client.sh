#!/bin/bash

set -e

cd client || exit

echo "------------------------------ BUILDING $dirname_stripped ------------------------------"

#remove previous binary if already exists
if [[ -e executable ]]; then
  rm executable
fi

# build new binary
echo "Building binary..."
GOOS=linux GOARCH=amd64 go build -o executable .

if [[ -e multiclient ]]; then
  rm multiclient
fi

echo "Building multi client binary"
gcc -o multiclient create_thread_clients.c -lpthread

cd .. || exit

docker build client -t novapokemon/client:latest
docker push novapokemon/client:latest
