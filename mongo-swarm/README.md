# mongo swarm

- Generate `source.yml` and `dest.yml`: `python3 generate-compose.py __optional_flags__`
- Create docker network: `docker network create primary_net`
- Start source: `GITHUB_TOKEN=__GITHUB_TOKEN__ docker-compose -f source.yml up`
- Start destination: `GITHUB_TOKEN=__GITHUB_TOKEN__ docker-compose -f dest.yml up`
- Bootstrap source: `./local-bootstrap.sh`
