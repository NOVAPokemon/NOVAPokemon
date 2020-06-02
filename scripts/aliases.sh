#!/bin/bash

NOVAPOKEMON_DIR="~/git/NOVAPokemon"
NOVAPOKEMON_SCRIPTS_DIR="$NOVAPOKEMON_DIR/scripts"
NOVAPOKEMON_TEST_FILE="test.sh"

cdToDir="cd ${NOVAPOKEMON_DIR}"

alias testNOVA="$cdToDir; bash $NOVAPOKEMON_SCRIPTS_DIR/$NOVAPOKEMON_TEST_FILE; cd -"
alias pullNOVA="$cdToDir; bash $NOVAPOKEMON_SCRIPTS_DIR/pull.sh; cd -"
alias pushNOVA="$cdToDir; bash $NOVAPOKEMON_SCRIPTS_DIR/push.sh; cd -"
alias buildNOVA="$cdToDir; bash $NOVAPOKEMON_SCRIPTS_DIR/build_binaries.sh; cd -"
alias runNOVA="$cdToDir; bash $NOVAPOKEMON_SCRIPTS_DIR/run_servers.sh; cd -"
alias masterNOVA="$cdToDir; bash $NOVAPOKEMON_SCRIPTS_DIR/checkout.sh; cd -"
