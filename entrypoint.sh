#!/bin/sh -l

echo "Hello $1"
echo $(ls)
pwd
ls -la
time=$(date)
echo "::set-output name=time::$time"
