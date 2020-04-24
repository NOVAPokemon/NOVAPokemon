#!/bin/bash

set -e

DOCKERIZE_VERSION=v0.6.1

cd "$(go env GOPATH)"/src/github.com/NOVAPokemon/ || exit

bash scripts/build_servers.sh

#MONGO
export MONGODB_URL="mongodb://localhost:27017"

# PORTS
export AUTH_PORT=8001
export BATTLES_PORT=8002
export GYM_PORT=8003
export LOCATION_PORT=8004
export MICROTRANSACTIONS_PORT=8005
export NOTIFICATIONS_PORT=8006
export STORE_PORT=8007
export TRADES_PORT=8008
export TRAINERS_PORT=8009

# HOSTNAMES
export AUTH_NAME="authentication"
export BATTLES_NAME="battles"
export GYM_NAME="gym"
export LOCATION_NAME="location"
export MICROTRANSACTIONS_NAME="microtransactions"
export NOTIFICATIONS_NAME="notifications"
export STORE_NAME="store"
export TRADES_NAME="trades"
export TRAINERS_NAME="trainers"

export WAIT_FLAG="-wait"
export WAIT_TIMEOUT_FLAG="-timeout 60s"
export RETRY_INTERVAL_FLAG="-wait-retry-interval 5s"
export DEFAULT_FLAGS="$WAIT_TIMEOUT_FLAG $RETRY_INTERVAL_FLAG"

# PREFIXES
export HTTP_PREFIX="http://"
export TCP_PREFIX="tcp://"

# WAIT FLAGS
export WAIT_AUTH="$WAIT_FLAG $HTTP_PREFIX$AUTH_NAME:$AUTH_PORT"
export WAIT_BATTLES="$WAIT_FLAG $HTTP_PREFIX$BATTLES_NAME:$BATTLES_PORT"
export WAIT_GYM="$WAIT_FLAG $HTTP_PREFIX$GYM_NAME:$GYM_PORT"
export WAIT_LOCATION="$WAIT_FLAG $HTTP_PREFIX$LOCATION_NAME:$LOCATION_PORT"
export WAIT_MICROTRANSACTIONS="$WAIT_FLAG $HTTP_PREFIX$MICROTRANSACTIONS_NAME:$MICROTRANSACTIONS_PORT"
export WAIT_NOTIFICATIONS="$WAIT_FLAG $HTTP_PREFIX$NOTIFICATIONS_NAME:$NOTIFICATIONS_PORT"
export WAIT_STORE="$WAIT_FLAG $HTTP_PREFIX$STORE_NAME:$STORE_PORT"
export WAIT_TRADES="$WAIT_FLAG $HTTP_PREFIX$TRADES_NAME:$TRADES_PORT"
export WAIT_TRAINERS="$WAIT_FLAG $HTTP_PREFIX$TRAINERS_NAME:$TRAINERS_PORT"

# COMMANDS
cd base_image || exit

if [ ! -e dockerize ]; then
  echo "Downloading dockerize"
  wget https://github.com/jwilder/dockerize/releases/download/v0.6.1/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
   -O dockerize.tar.gz
  tar -xzvf dockerize.tar.gz
  rm dockerize.tar.gz
fi

echo "------------------------------ BUILDING nova-server-base image ------------------------------"

docker build -t nova-server-base:latest .

cd .. || exit

echo "------------------------------ BUILDING images with docker-compose ------------------------------"

docker-compose build

echo "------------------------------ STARTING docker-compose ------------------------------"

docker-compose up --remove-orphan

bash scripts/clean_binaries.sh

cd - || exit
