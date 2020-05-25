#!/bin/bash

logs_dir=/tmp/logs_prometheusAlertManager
dirname=~/logs_prometheusAlertManager_$(date +%d_%m_%Y__%H_%M_%S)
mkdir "$dirname" && mv "$logs_dir"/* "$dirname"/
echo "saved logs to: ${dirname}"

logs_dir=/tmp/logs_prometheusServer
dirname=~/logs_prometheusServer_$(date +%d_%m_%Y__%H_%M_%S)
mkdir "$dirname" && mv "$logs_dir"/* "$dirname"/
echo "saved logs to: ${dirname}"