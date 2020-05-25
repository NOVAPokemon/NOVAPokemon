#!/bin/bash

logs_dir=/tmp/logs_elastic
dirname=~/logs_$(date +%d_%m_%Y__%H_%M_%S)
mkdir "$dirname" && mv "$logs_dir"/* "$dirname"/

echo "saved logs to: ${dirname}"