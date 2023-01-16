#!/bin/bash

if [ "$#" -ne 4 ]; then
    echo "USAGE:"
    echo " ./flashFirmware.sh <PORT> <FILENAME> <OGNID> <BLOCK_SIZE>"
    exit 1
fi

source ./venv/bin/activate
export PYTHONPATH=./src/:$PYTHONPATH
python3 ./src/ognLoader.py $1 $2 $3 $4
deactivate

