#!/usr/bin/env bash

MONGO_VERSION=4.0
NETWORK_NAME="primary_net"


PREFIX=$1
N_MONGOS=$2
PORT=27017
WAIT_TIME=60 # in seconds

for ((i = 0 ; i < ${N_MONGOS} ; i++))
do
    echo "--------------------------------------------------" && \
    echo "Balancer State on mongos $i":
    docker run -it --rm --network $NETWORK_NAME mongo:$MONGO_VERSION mongo --host "${PREFIX}mongos${i}:$PORT" --eval "
        sh.getBalancerState()
    " &&

    echo "--------------------------------------------------" && \
    echo "Shard Distribution":
    docker run -it --rm --network $NETWORK_NAME mongo:$MONGO_VERSION mongo --host "${PREFIX}mongos${i}:$PORT" --eval "
        sh.status()
    " &&

    echo "--------------------------------------------------" && \
    echo "done."
done