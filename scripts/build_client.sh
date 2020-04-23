#!/bin/bash

set -e

cd client || exit

echo "------------------------------ BUILDING $dirname_stripped ------------------------------"

#remove previous binary if already exists
if [ -e executable ]; then
  rm executable
fi

# build new binary
echo "Building binary..."
go build -o executable .

cd .. || exit

docker build client -t client