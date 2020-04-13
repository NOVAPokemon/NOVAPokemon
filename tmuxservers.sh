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

# set up tmux
tmux start-server

# create a new tmux session
tmux new-session -d -s $session

# Select pane 1
name="authentication"
tmux send-keys "$cdToRepo$name;$runGoPkg$name"
tmux splitw -v

# Select pane 1
name="notifications"
tmux send-keys "$cdToRepo$name;$runGoPkg$name" 
tmux splitw -v

# Select pane 1
name="trades"
tmux send-keys "$cdToRepo$name;$runGoPkg$name" 
tmux splitw -v

# Select pane 1
name="trainers"
tmux send-keys "$cdToRepo$name;$runGoPkg$name" 
tmux splitw -v

# Select pane 1
name="microtransactions"
tmux send-keys "$cdToRepo$name;$runGoPkg$name" 
tmux splitw -v

# Select pane 1
name="store"
tmux send-keys "$cdToRepo$name;$runGoPkg$name" 
tmux splitw -v

# Select pane 1
name="generator"
tmux send-keys "$cdToRepo$name;$runGoPkg$name" 
tmux splitw -v

tmux attach-session -t $session
