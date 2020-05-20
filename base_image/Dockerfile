FROM alpine:3.7

RUN apk add iproute2
RUN mkdir /logs && mkdir /service
WORKDIR /service

COPY dockerize .
RUN chmod +x dockerize