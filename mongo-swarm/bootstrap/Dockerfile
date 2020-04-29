FROM golang:1.12.9-alpine as builder
# FROM golang:latest as builder

ARG APP_VERSION=unknown

RUN mkdir /root/build
WORKDIR /root/build

# copy code
ADD . /root/build

RUN apk add --no-cache git

RUN go mod download

# ENTRYPOINT go run -v github.com/achan-ns/mongo-swarm/bootstrap
RUN go build -o /tmp/bootstrap .

# RUN echo "done"

FROM alpine:latest

COPY --from=builder /tmp/bootstrap /mongo-swarm/bootstrap

RUN chmod 777 /mongo-swarm/bootstrap

EXPOSE 9090
WORKDIR /mongo-swarm
ENTRYPOINT ["/mongo-swarm/bootstrap"]
