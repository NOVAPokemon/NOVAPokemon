FROM golang:latest

RUN mkdir /logs
RUN mkdir /service
WORKDIR /service

COPY dockerize .
RUN chmod +x dockerize