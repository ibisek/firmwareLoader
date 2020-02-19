#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "USAGE:"
    echo " ./flashFirmware.sh <PORT> <FILENAME> <OGNID>"
    exit 1
fi


export PYTHONPATH=./src/:$PYTHONPATH
python3 ./src/ognLoader.py $1 $2 $3

