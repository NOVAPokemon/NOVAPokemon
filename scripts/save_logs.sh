#!/bin/bash

logs_dir=/tmp/logs_elastic
dirname=~/logs_${time}
mkdir "$dirname" && mv "$logs_dir"/* "$dirname"/
echo "saved logs to: ${dirname}"

