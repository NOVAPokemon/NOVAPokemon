#!/usr/bin/bash

curr_dir=$(pwd)

set -e

for image in ~/go/src/github.com/NOVAPokemon/images/*; do
  echo "Loading image $image..."
  docker load <$image
done

cd "$curr_dir"
