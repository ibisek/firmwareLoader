#!/bin/bash

#
# Script for automatic flashing of pile of OGN CUBE trackers.
# Needs to be run in sudo.
#

#
#   CONFIGURATION
#

PORT="rfcomm0"

#FILE="./bin-files/ognCube3.f103-2019-06-18-GLD-0x2800.bin"
#FILE="./bin-files/ognCube3.f103-2019-06-18-TOW-0x2800.bin"
#FILE="./bin-files/ognCube3.f103-2019-07-03-GLD-36MHz-0x2800.bin"
#FILE="./bin-files/ognCube-experimental.bin"
#FILE="./bin-files/ognCube3.f103-2020-02-07-UAV-36MHz-0x2800.bin"
FILE="./bin-files/ognCube.bin"

#
#   THE MEAT!
#

currentUser=`whoami`
if [ "$currentUser" != "root" ]
then
  echo "This script needs to be executed under root!"
  exit 1
fi

echo "Searching for BT devices.."

available="`hcitool scan`"
# available="$(hcitool scan)"

# read -d '' available << EOF
# Ahoj vole!
# Scanning ...
#         C2:2C:1B:07:18:D9       OGN CUBE 145928
# EOF

readarray -t lines <<<"$available"
lines=`echo $lines| grep OGN`

macAddr="null"
ognId="null"
regex="([A-F:0-9:]+)\s+OGN CUBE\s([A-F0-9]+)"
for line in "${lines[@]}"
do
    # echo "LINE: $line"

    if [[ $line =~ $regex ]]
    then
        macAddr="${BASH_REMATCH[1]}"
        ognId="${BASH_REMATCH[2]}"

    else
      continue
    fi

    echo -e "\nFound OGN CUBE tracker ID [$ognId] with BT MAC addr [$macAddr]"

    rfcomm unbind $PORT 2>&1 > /dev/null
    rfcomm bind $PORT $macAddr

    #echo -e "--------------------------\nAllright, let's get ready!\n\n(1) Power cycle (OFF->ON) the tracker\n then\n(2) count to three, or (optimally) after ONE long LED flash\n and finally"
    #read -p "(3) press ENTER"

    ./flashFirmware.sh /dev/$PORT $FILE $ognId

    # sleep 2
    # /usr/local/bin/miniterm.py $PORT 115200
done
