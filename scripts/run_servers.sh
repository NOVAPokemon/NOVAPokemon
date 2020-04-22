#!/bin/bash

cd "$(go env GOPATH)"/src/github.com/NOVAPokemon/ || exit

bash scripts/build_binaries.sh

docker-compose build
docker-compose up --remove-orphan

bash scripts/clean_binaries.sh

cd - || exit