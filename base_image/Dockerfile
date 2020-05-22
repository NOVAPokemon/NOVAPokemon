FROM debian:latest

RUN mkdir /logs && mkdir /service
WORKDIR /service

COPY dockerize .
RUN chmod +x dockerize