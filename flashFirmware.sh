#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "USAGE:"
    echo " ./flashFirmware.sh <FILENAME> <OGNID>"
    exit 1
fi


export PYTHONPATH=./src/:$PYTHONPATH
python3 ./src/ognLoader.py $1 $2

