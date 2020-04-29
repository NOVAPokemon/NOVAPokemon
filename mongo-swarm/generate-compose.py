import argparse

# Define structure

INDENT = "  "

DOCKER_COMPOSE_VERSION = "3.6"
MONGO_VERSION = "4.0"
MONGO_PORT = 27017
NETWORK = "primary_net"

NETWORKS_BLOCK = \
    """
networks:
  {0}:
      external: true
""".format(NETWORK)

VERSION_BLOCK = \
    """
version: "{version}"
""".format(version=DOCKER_COMPOSE_VERSION)

SERVICES_BLOCK_HEADER = \
    """
services:
"""

COMMANDS = {
    "data": "mongod --shardsvr --replSet {prefix}data{datars_number}rs --smallfiles --port 27017 --bind_ip_all",
    "cfg": "mongod --configsvr --replSet {prefix}cfgrs --smallfiles --port 27017 --bind_ip_all",
    "mongos": "mongos --configdb {cfgrs} --bind_ip_all",  # TODO
}

BLOCK = \
    """
  {prefix}{type}{instance_number}:
    image: mongo:{mongo_version}
    command: {command}
    networks:
      - {network}
"""


def main():
    parser = argparse.ArgumentParser(description='Generate compose file')
    parser.add_argument('--data', dest='data', action='store', default="3,3,3",
                        help='Data shards to generate. Example: "--data 3,4" to generate two shards with 3 and 4 '
                             'servers in replicaset. Defaults to 3,3,3.')
    parser.add_argument('--cfg', dest='cfg', action='store', default=3,
                        help='Number of servers in config replicaset. Defaults to 3.')
    parser.add_argument('--mongos', dest='mongos', action='store', default=2,
                        help='Number of mongos instances. Defaults to 2.')
    parser.add_argument('--prefix', dest='prefix', action='store', default="",
                        help='Prefix for instance. Defaults to no prefix.')

    args = parser.parse_args()
    data_instances = [int(i) for i in args.data.split(",")]
    cfg_instances = int(args.cfg)
    mongos_instances = int(args.mongos)
    prefix = args.prefix

    compose_file = ""
    flags = []  # flags for bootstrap script

    compose_file += VERSION_BLOCK
    compose_file += NETWORKS_BLOCK
    compose_file += SERVICES_BLOCK_HEADER

    for data_instance, data_servers in enumerate(data_instances):
        flag = []
        for data_server in range(data_servers):
            server_number = f'{data_instance}{data_server}'
            compose_file += BLOCK.format(
                prefix=prefix,
                type="data",
                instance_number=server_number,
                mongo_version=MONGO_VERSION,
                command=COMMANDS["data"].format(datars_number=data_instance, prefix=prefix),
                network=NETWORK,
            )
            flag.append(f'{prefix}data{server_number}:{MONGO_PORT}')
        flags.append(f'--dataSet={prefix}data{data_instance}rs/' + ','.join(flag) + " ")

    flag = []
    for cfg_number in range(cfg_instances):
        compose_file += BLOCK.format(
            prefix=prefix,
            type="cfg",
            instance_number=cfg_number,
            mongo_version=MONGO_VERSION,
            command=COMMANDS["cfg"].format(prefix=prefix),
            network=NETWORK,
        )
        flag.append(f'{prefix}cfg{cfg_number}:{MONGO_PORT}')
    cfgrs = f'{prefix}cfgrs/' + ','.join(flag)
    flags.append(f'--configSet={prefix}cfgrs/' + ','.join(flag) + " ")

    flag = []
    for mongos_number in range(mongos_instances):
        compose_file += BLOCK.format(
            prefix=prefix,
            type="mongos",
            instance_number=mongos_number,
            mongo_version=MONGO_VERSION,
            command=COMMANDS["mongos"].format(cfgrs=cfgrs),
            network=NETWORK,
        )
        flag.append(f'{prefix}mongos{mongos_number}:{MONGO_PORT}')
    flags.append(f'--mongos=' + ','.join(flag))

    with open('docker-compose.yml', 'w') as file:
        file.write(compose_file)

    with open('bootstrap_cmd', 'w') as file:
        file.write(''.join(flags))


main()
