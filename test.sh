#!/bin/bash

for d in */; do
  cd "$d" || exit
  go test github.com/NOVAPokemon/"$d"/...
  cd .. || exit
done
