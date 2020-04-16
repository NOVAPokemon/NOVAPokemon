#!/bin/sh
#
# Setup a work space called `work` with two windows
# first window has 3 panes.
# The first pane set at 65%, split horizontally, set to api root and running vim
# pane 2 is split at 25% and running redis-server
# pane 3 is set to api root and bash prompt.
# note: `api` aliased to `cd ~/path/to/work`
#
session="servers"
cdToRepo="cd ~/go/src/github.com/NOVAPokemon/"
runGoPkg="go run github.com/NOVAPokemon/"
runMongo="docker run -p 27017:27017 mongo"

# Set Session Name
SESSIONEXISTS=$(tmux list-sessions | grep $session)

# Only create tmux session if it doesn't already exist
if [ "$SESSIONEXISTS" != "" ]; then
  tmux kill-session -t $session
fi

# set up tmux
tmux start-server

# create a new tmux session
tmux new-session -s $session -d -x "$(tput cols)" -y "$(tput lines)"

# create a new window called scratch
tmux rename-window -t $session:0 mongo
tmux send-keys "$runMongo" C-m

# create a new window called scratch
tmux new-window -t $session:1 -n servers

name="authentication"
tmux send-keys "$cdToRepo$name;$runGoPkg$name"
tmux splitw -v -p 50

name="notifications"
tmux send-keys "$cdToRepo$name;$runGoPkg$name"
tmux selectp -t 1
tmux splitw -v -p 50

name="trades"
tmux send-keys "$cdToRepo$name;$runGoPkg$name"
tmux selectp -t 1
tmux splitw -v -p 50

name="trainers"
tmux send-keys "$cdToRepo$name;$runGoPkg$name"
tmux selectp -t 3
tmux splitw -v -p 50

name="microtransactions"
tmux send-keys "$cdToRepo$name;$runGoPkg$name"
tmux selectp -t 0
tmux splitw -v -p 50

name="store"
tmux send-keys "$cdToRepo$name;$runGoPkg$name"
tmux selectp -t 0
tmux splitw -v -p 50

name="generator"
tmux send-keys "$cdToRepo$name;$runGoPkg$name"
tmux selectp -t 2
tmux splitw -v -p 50

name="location"
tmux send-keys "$cdToRepo$name;$runGoPkg$name"

tmux select-layout even-vertical
tmux setw synchronize-panes on
tmux send-keys C-m
tmux setw synchronize-panes off

tmux attach-session -t $session
