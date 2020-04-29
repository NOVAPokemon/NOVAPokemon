#!/usr/bin/env bash

set -e

PREFIX=$1
SHARD_CONF=$2
N_MONGOS=$3
N_CFG=$4

python3 generate-compose.py --data ${SHARD_CONF} --cfg ${N_CFG} --mongos ${N_MONGOS} --prefix ${PREFIX} > docker-compose.yml
cat docker-compose.yml
docker stack rm ${PREFIX} 2> /dev/null
docker build bootstrap -t mongo-cluster-bootstrap
docker stack deploy -c docker-compose.yml ${PREFIX}
docker rm -f ${PREFIX}-mongo-cluster-bootstrap || true
docker run -d --network primary_net --name ${PREFIX}-mongo-cluster-bootstrap mongo-cluster-bootstrap $(cat bootstrap_cmd)
#bash local-status.sh ${PREFIX} ${N_MONGOS} #if removing this comment, then the bootstrap command cannot be detached from
#rm docker-compose.yml
#rm bootstrap_cmd
echo "done"
