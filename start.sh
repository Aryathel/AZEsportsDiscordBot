#!/bin/sh

TIMEOUT="5s"

while : ; do
    pipenv run python3.9 main.py
    echo "Restarting in $TIMEOUT"
    sleep $TIMEOUT
done