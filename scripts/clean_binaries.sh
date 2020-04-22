#!/bin/bash

ignored_utils="utils"
ignored_scripts="scripts"

#build images
for d in */; do
  dirname_stripped=$(basename "$d")

  if [ "$dirname_stripped" == $ignored_utils ] || [ "$dirname_stripped" == $ignored_scripts ]; then
    continue
  fi

  echo "------------------------------ CLEAN $dirname_stripped ------------------------------"

  cd "$d" || exit

  echo "Cleaning binary..."

  #remove previous binary if already exists
  if [ -e "$dirname_stripped" ]; then
    rm "$dirname_stripped"
  fi

  cd .. || exit
done
