#!/bin/bash

cd authentication
go test github.com/NOVAPokemon/authentication/...

cd ../battles
go test github.com/NOVAPokemon/battles/...

cd ../client
go test github.com/NOVAPokemon/client/...

cd ../generator
go test github.com/NOVAPokemon/generator/...

cd ../trades
go test github.com/NOVAPokemon/trades/...

cd ../utils
go test github.com/NOVAPokemon/utils/...

cd ..
