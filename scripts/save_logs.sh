#!/bin/bash

time=$(date +%d_%m_%Y__%H_%M_%S)

logs_dir=/tmp/logs_elastic_2
dirname=~/logs_${time}
mkdir "$dirname" && mv "$logs_dir"/* "$dirname"/

echo "saved logs to: ${dirname}"

logs_dir=/tmp/logs_prometheusAlertManager
dirname=~/logs_prometheusAlertManager_${time}
mkdir "$dirname" && mv "$logs_dir"/* "$dirname"/
echo "saved logs to: ${dirname}"

logs_dir=/tmp/logs_prometheusServer
dirname=~/logs_prometheusServer_${time}
mkdir "$dirname" && mv "$logs_dir"/* "$dirname"/
echo "saved logs to: ${dirname}"
