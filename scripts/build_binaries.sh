#!/bin/bash

ignored_utils="utils"
ignored_scripts="scripts"

#build images
for d in */; do
  dirname_stripped=$(basename "$d")

  if [ "$dirname_stripped" == $ignored_utils ] || [ "$dirname_stripped" == $ignored_scripts ]; then
    continue
  fi

  echo "------------------------------ BUILDING $dirname_stripped ------------------------------"

  cd "$d" || exit

  #remove previous binary if already exists
  if [ -e "$dirname_stripped" ]; then
    rm executable
  fi

  # build new binary
  echo "Building binary..."
  go build -o executable .

  cd .. || exit
done
