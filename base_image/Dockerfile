FROM alpine:3.7

RUN mkdir /logs
RUN mkdir /service
WORKDIR /service

COPY dockerize .
RUN chmod +x dockerize