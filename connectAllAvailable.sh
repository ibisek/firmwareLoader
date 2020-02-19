#!/bin/bash

#
# Connects all available CUBE units to /dev/rfcomm{$i} where i>=0
#

RED='\033[1;31m'
GREEN='\033[1;32m'
BLUE='\033[1;34m'
PURPLE='\033[1;35m'
CYAN='\033[1;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

echo -e "\n${WHITE}Searching for BT devices..${NC}"

available="`hcitool scan`"
readarray -t lines <<<"$available"
lines=`echo $lines| grep OGN`

i=0
macAddr="null"
ognId="null"
regex="([A-F:0-9:]+)\s+OGN CUBE\s([A-F0-9]+)"
for line in "${lines[@]}"
do
    if [[ $line =~ $regex ]]
    then
        macAddr="${BASH_REMATCH[1]}"
        ognId="${BASH_REMATCH[2]}"

    else
      continue
    fi

    echo -e "Found OGN CUBE tracker ID ${GREEN}$ognId${NC} with BT MAC addr ${GREEN}$macAddr${NC}"
    port="/dev/rfcomm$i"

    sudo rfcomm unbind $port 2>&1 > /dev/null
    sudo rfcomm bind $port $macAddr
    echo -e "  bound $ognId to ${GREEN}$port${NC}"

    ((i++))
done


