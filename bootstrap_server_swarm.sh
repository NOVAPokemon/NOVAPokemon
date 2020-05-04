#!/bin/bash

set -e

source server_swarm.config
bash scripts/build_servers.sh

# COMMANDS
echo "------------------------------ Cleaning previous swarm------------------------------"
bash scripts/clean_swarm.sh

echo "------------------------------ Creating networks------------------------------"
bash scripts/create_swarm_networks.sh || true
echo "------------------------------ BOOTSTRAPING MONGO CLUSTERS ------------------------------"

cd mongo-swarm
# changing args here may change the url of database (if messing with number of mongos)
bash bootstrap_mongo_cluster.sh "trainers" ${TRAINERS_SHARD_CONFIG} ${TRAINERS_N_ROUTERS} ${TRAINERS_N_CFG_SRV}
bash bootstrap_mongo_cluster.sh "users" ${USERS_SHARD_CONFIG} ${USERS_N_ROUTERS} ${USERS_N_CFG_SRV}
bash bootstrap_mongo_cluster.sh "notifications" ${NOTIFICATIONS_SHARD_CONFIG} ${NOTIFICATIONS_N_ROUTERS} ${NOTIFICATIONS_N_CFG_SRV}
bash bootstrap_mongo_cluster.sh "microtransactions" ${MICROTRANSACTIONS_SHARD_CONFIG} ${MICROTRANSACTIONS_N_ROUTERS} ${MICROTRANSACTIONS_N_CFG_SRV}
bash bootstrap_mongo_cluster.sh "location" ${LOCATION_SHARD_CONFIG} ${LOCATION_N_ROUTERS} ${LOCATION_N_CFG_SRV}
cd .. || exit

cd base_image || exit

if [ ! -e dockerize ]; then
  echo "Downloading dockerize"
  wget https://github.com/jwilder/dockerize/releases/download/v0.6.1/dockerize-linux-amd64-${DOCKERIZE_VERSION}.tar.gz \
   -O dockerize.tar.gz
  tar -xzvf dockerize.tar.gz
  rm dockerize.tar.gz
fi

echo "------------------------------ BUILDING nova-server-base image ------------------------------"

docker build -t nova-server-base:latest .
cd .. || exit

echo "------------------------------ BUILDING other images ------------------------------"

bash scripts/build_service_images.sh

echo "------------------------------ STARTING swarm stack ------------------------------"

docker stack deploy -c docker-compose-swarm.yml services

bash scripts/clean_binaries.sh

cd - || exit
