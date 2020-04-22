NOVAPOKEMON_DIR="$(go env GOPATH)/src/github.com/NOVAPokemon"
NOVAPOKEMON_SCRIPTS_DIR="$NOVAPOKEMON_DIR/scripts"
NOVAPOKEMON_TEST_FILE="test.sh"

cdToDir="cd $HOME/go/src/github.com/NOVAPokemon"

alias testNOVA="$cdToDir; bash $NOVAPOKEMON_SCRIPTS_DIR/$NOVAPOKEMON_TEST_FILE; cd -"
alias pullNOVA="$cdToDir; bash $NOVAPOKEMON_SCRIPTS_DIR/pull.sh; cd -"
alias pushNOVA="$cdToDir; bash $NOVAPOKEMON_SCRIPTS_DIR/push.sh; cd -"
alias buildNOVA="$cdToDir; bash $NOVAPOKEMON_SCRIPTS_DIR/build_binaries.sh; cd -"
alias runNOVA="$cdToDir; bash $NOVAPOKEMON_SCRIPTS_DIR/run_servers.sh; cd -"
