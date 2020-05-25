#!/bin/bash

set -e

helm uninstall novapokemon
bash scripts/save_logs.sh
bash scripts/save_logs_prometheus.sh
