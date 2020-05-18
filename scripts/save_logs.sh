#!/bin/bash

dirname=~/logs_$(date +%d_%m_%Y__%H_%M_%S)
mkdir "$dirname"
mv -R ~/logs/* ~/"$dirname"/