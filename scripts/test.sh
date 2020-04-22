#!/bin/bash

ignored="scripts/"

for d in */; do
  if [ "$d" == $ignored ]; then
    continue
  fi
  cd "$d" || exit
  go test github.com/NOVAPokemon/"$d"/...
  cd .. || exit
done
