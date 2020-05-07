#!/usr/bin/env bash

docker network create --attachable --ingress --driver overlay ingress || true
docker network create --attachable --driver overlay primary_net || true