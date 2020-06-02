#!/bin/bash

set -e

cd client || exit

echo "------------------------------ BUILDING CLIENT ------------------------------"

#remove previous binary if already exists
if [[ -e executable ]]; then
	rm executable
fi

# build new binary
echo "Building binary..."
GOOS=linux GOARCH=amd64 go build -o executable .

cd .. || exit

docker build client -t novapokemon/client:latest
docker push novapokemon/client:latest
