#!/bin/bash

#
# Script for automatic flashing of pile of OGN CUBE trackers.
# Needs to be run in sudo.
#

#
#   CONFIGURATION
#

PORT="rfcomm0"
FILE="./bin-files/ognCube3.f103-2019-03-12-4PK-0x2800.bin"

#
#   THE MEAT!
#

currentUser=`whoami`
if [ "$currentUser" != "root" ]
then
  echo "This script needs to be executed under root!"
  exit 1
fi

available="`hcitool scan`"
# available="$(hcitool scan)"

# read -d '' available << EOF
# Ahoj vole!
# Scanning ...
#         C2:2C:1B:07:18:D9       OGN CUBE 145928
# EOF

readarray -t lines <<<"$available"
lines=`echo $lines| grep OGN`

regex="([A-F:0-9:]+)\s+OGN CUBE\s([A-F0-9]+)"
for line in "${lines[@]}"
do
    # echo "LINE: $line"
    macAddr="null"
    ognId="null"

    if [[ $line =~ $regex ]]
    then
        macAddr="${BASH_REMATCH[1]}"
        ognId="${BASH_REMATCH[2]}"

    else
      continue
    fi

    echo "Found OGN CUBE tracker ID '$ognId' with BT MAC addr '$macAddr'"

    rfcomm unbind $PORT
    rfcomm bind $PORT $macAddr

    echo -e "\nPower cycle (OFF->ON) the tracker and .."
    read -p "AFTER one long flash press ENTER"

    ./flashFirmware.sh $FILE $ognId
done
