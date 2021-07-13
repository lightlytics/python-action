#!/bin/sh -l

echo "Hello $1"
ls
time=$(date)
echo "::set-output name=time::$time"
