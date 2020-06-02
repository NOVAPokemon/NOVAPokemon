#!/bin/sh
#
# Setup a work space called `work` with two windows
# first window has 3 panes.
# The first pane set at 65%, split horizontally, set to api root and running vim
# pane 2 is split at 25% and running redis-server
# pane 3 is set to api root and bash prompt.
# note: `api` aliased to `cd ~/path/to/work`
#
session="clients"
cdToClient="cd ~/go/src/github.com/NOVAPokemon/client"
cdToRepo="cd ~/go/src/github.com/NOVAPokemon/"
lazygit="gg"
runGoClient="go run github.com/NOVAPokemon/client"

# Set Session Name
SESSIONEXISTS=$(tmux list-sessions | grep ${session})

# Only create tmux session if it doesn't already exist
if [ "$SESSIONEXISTS" != "" ]; then
  tmux kill-session -t ${session}
fi

# set up tmux
tmux start-server

# create a new tmux session
tmux new-session -s ${session} -d -x "$(tput cols)" -y "$(tput lines)"

tmux rename-window -t ${session}:0 clients

tmux splitw -h -p 50
tmux setw synchronize-panes on

tmux send-keys "$cdToClient;$runGoClient" C-m

tmux setw synchronize-panes off

tmux new-window -t ${session}:1 -n git
tmux send-keys "$cdToRepo;$lazygit" C-m
tmux splitw -h -p 50
tmux send-keys "$cdToRepo" C-m

tmux selectw -t ${session}:0

tmux attach-session -t ${session}
