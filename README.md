# NOVAPokemon

A location-based, Pokémon-style **microservices game** built as a realistic workload for
distributed-systems research — used to benchmark deployment frameworks (client↔server latency
and QoS) for geo-distributed and cloud-edge environments. This is the umbrella repository: each
service is a Go submodule, wired together here with deployment charts, build tooling, and the
geo/latency configuration that drives the benchmark.

## Gameplay → workload

The game's player operations generate varied, realistic traffic across the services:

- Register / Login
- Catch a Pokémon
- Buy an item
- Battle (real-time)
- Trade (real-time)

## Services

Each service lives in its own submodule:

| Service | Responsibility |
|---------|----------------|
| `authentication` | Login and token-based auth |
| `trainers` | Trainer profiles, Pokémon collections, bags, levels and coins |
| `battles` | Real-time Pokémon battles |
| `gym` | Gyms and gym-leader battles |
| `trades` | Real-time trading of Pokémon between players |
| `store` | Buying items |
| `microtransactions` | In-game currency / purchases |
| `location` | Location tracking and region/cell-based Pokémon spawning |
| `map-viewer` | Visualisation of the world map and nodes |
| `notifications` | Notifications between players |
| `client` | Test client / load driver (config-file driven) |
| `utils` | Shared library code (data types, clients, helpers) |

## Architecture

- **Services** — Go microservices that expose HTTP and WebSocket APIs (WebSockets for the
  real-time battle/gym/trade flows) and exchange events over **Kafka**.
- **Storage** — **MongoDB**, one logical database per service (`novapokemon` prefix).
- **Observability** — **Prometheus** (with Alertmanager) and **Grafana** for metrics, and an
  **EFK** logging pipeline (**Fluentd → Elasticsearch**).
- **Geo-distribution** — services are placed across locations/cells (S2-style cell IDs); the
  `location`/`map-viewer` services and the `*_delays`/`location_tags`/`cells_to_region` configs
  plus `scripts/control_traffic.sh` let the workload model client proximity and inter-node
  latency — the basis for the cloud-edge deployment benchmark.

## Deployment

- **Kubernetes** via the Helm chart in `deployment-chart/` (a subchart per service, deployed as
  StatefulSets; bundles MongoDB, Kafka, Prometheus, Grafana, Elasticsearch/Fluentd and the
  Kubernetes dashboard).
- **Docker Compose / Swarm** via `docker-compose.yml` and `docker-compose-swarm.yml`.
- **base_image/** provides the common base Docker image; `scripts/` holds the Python/Bash
  tooling to build the service and client images, deploy, shape traffic, and collect logs.

## Repository layout

```
authentication/ battles/ client/ gym/ location/ map-viewer/   ← service submodules
microtransactions/ notifications/ store/ trades/ trainers/ utils/
base_image/          ← shared base Docker image
deployment-chart/    ← Helm chart (Kubernetes)
scripts/             ← build / deploy / traffic-control / log tooling
docker-compose*.yml  ← Compose / Swarm deployment
*.json, *.config     ← geo, cell and client-delay configuration
```

## Getting started

Clone with submodules:

```bash
git clone --recursive https://github.com/NOVAPokemon/NOVAPokemon
# or, in an existing checkout:
git submodule update --init --recursive
```

Build the images and deploy with Helm (Kubernetes) or Docker Compose:

```bash
# build base image + all service images + the client
./scripts/build_service_images.sh
./scripts/build_client.sh

# Kubernetes (Helm)
helm install novapokemon ./deployment-chart

# or local Docker Compose
docker compose up
```

See `scripts/` and `useful_commands.txt` for the full set of build, deploy and benchmarking
commands.
