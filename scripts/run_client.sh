#!/bin/bash

set -e

cd "$(go env GOPATH)"/src/github.com/NOVAPokemon/ || exit

bash scripts/build_client.sh

docker run --net=novapokemon_default --env-file=client/env.list -ti client