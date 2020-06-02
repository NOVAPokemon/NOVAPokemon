#!/bin/bash

if [ "$(go env GOPATH)" == "" ]; then
	go env -w GOPATH="$HOME/go"
	echo "GOPATH set to $(go env GOPATH)"
fi

if [ "$(go env GOBIN)" == "" ]; then
	go env -w GOBIN="$(go env GOPATH)/bin"
	echo "GOBIN set to $(go env GOBIN)"
fi
