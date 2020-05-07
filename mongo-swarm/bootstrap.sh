#!/usr/bin/env bash

set -e

PREFIX=$1
SHARD_CONF=$2
N_MONGOS=$3
N_CFG=$4

echo "-----Bootstraping ${PREFIX} mongo cluster-----"
python3 generate-compose.py --data ${SHARD_CONF} --cfg ${N_CFG} --mongos ${N_MONGOS} --prefix ${PREFIX} > docker-compose.yml
echo "-----Deleting previous ${PREFIX} mongo cluster-----"
docker stack rm ${PREFIX} || true
echo "-----Building bootstrap image-----"
docker build bootstrap -t mongo-cluster-bootstrap
echo "-----Deploying ${PREFIX} mongo cluster-----"
docker stack deploy -c docker-compose.yml ${PREFIX}
echo "-----Deleting previous bootstrap container-----"
docker rm -f ${PREFIX}-mongo-cluster-bootstrap || true
echo "-----Deploying bootstrap container-----"
docker run -d --network primary_net --name ${PREFIX}-mongo-cluster-bootstrap mongo-cluster-bootstrap $(cat bootstrap_cmd)
#bash local-status.sh ${PREFIX} ${N_MONGOS} #if removing this comment, then the bootstrap command cannot be detached from
echo "-----Cleaning up-----"
rm docker-compose.yml || true
rm bootstrap_cmd || true
echo "done"
