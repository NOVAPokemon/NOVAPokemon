#!/bin/bash

echo "------------------------------ BUILDING CLIENT ------------------------------"

clientDir="$NOVAPOKEMON/client"

#remove previous binary if already exists
if [[ -e executable ]]; then
  rm "$clientDir"/executable
fi

test_race=false

while getopts 'r' flag; do
  case "${flag}" in
  r)
    test_race=true
    ;;
  *)
    print_usage
    exit 1
    ;;
  esac
done

# build new binary
race_flag=""

rm "$clientDir"/locations.json
rm "$clientDir"/lats.txt
rm "$clientDir"/location_tags.json
rm "$clientDir"/delays_config.json
rm "$clientDir"/client_delays.json
rm "$clientDir"/cells_to_region.json

if [[ $test_race == true ]]; then
  race_flag="--race"
  export GOOS=""
  export GOARCH=""
  echo "Building binary with RACE DETECTION..."
  echo "WARNING: BE CAREFUL, THIS BUILDS WITHOUT OS AND ARCH FLAGS DUE TO INCOMPATIBILITY"
else
  export GOOS=linux
  export GOARCH=amd64
  echo "Building binary..."
fi

(
  cd "$clientDir" || exit

  CGO_ENABLED=0 go build $race_flag -o executable .

  cd multiclient || exit
  rm ./multiclient
  echo "Building multiclient"

  CGO_ENABLED=0 go build -o multiclient create_thread_clients.go
)

cp "$NOVAPOKEMON"/location_tags.json "$clientDir"/
cp "$NOVAPOKEMON"/delays_config.json "$clientDir"/
cp "$NOVAPOKEMON"/client_delays.json "$clientDir"/
cp "$NOVAPOKEMON"/cells_to_region.json "$clientDir"/
cp "$NOVAPOKEMON"/lats.txt "$clientDir"/
cp "$NOVAPOKEMON"/locations.json "$clientDir"/
