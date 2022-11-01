#!/bin/bash

#
# Script for automatic flashing of pile of OGN CUBE trackers.
# Needs to be executed with sudo.
#

#
#   CONFIGURATION
#

PORT="rfcomm0"

#
#   THE MEAT!
#

currentUser=`whoami`
if [ "$currentUser" != "root" ]
then
  echo "This script needs to be executed under root!"
  exit 1
fi

#
# Select one firmware from the list of .bin files
#

files=($(ls -f ./bin-files/*bin))

echo "List of available firmwares:"
i=0
for file in "${files[@]}"
do
  i=$((i+1))
  echo -e "  [$i]\t$file"
done

read -p "Choose one <1, $i>: " i

i=$((i--))
fwFile=${files[$i]}

echo "Chosen fw: $fwFile"

#
# .. and let's do the stuff!
#

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
    echo "LINE: $line"

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

    #./flashFirmware.sh /dev/$PORT $fwFile $ognId
    ./flashFirmware.sh /dev/$PORT $fwFile $ognId 1024 # f103
#    ./flashFirmware.sh /dev/$PORT $fwFile $ognId 256  # l152

    # sleep 2
    # /usr/local/bin/miniterm.py $PORT 115200
done
