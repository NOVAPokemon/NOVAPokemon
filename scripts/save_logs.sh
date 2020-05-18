#!/bin/bash

logs_dir=~/logs
dirname=~/logs_$(date +%d_%m_%Y__%H_%M_%S)
mkdir "$dirname" && mv "$logs_dir"/* "$dirname"/
