FROM debian:latest

RUN mkdir /logs && mkdir /service
WORKDIR /service

COPY dockerize .
RUN chmod +x dockerize

COPY location_tags.json .
COPY delays_config.json .
COPY client_delays.json .
COPY cells_to_region.json .
COPY lat.txt .
COPY locations.json .
