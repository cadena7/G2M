#!/bin/bash

j=0

function manda_comando () {
 ( ping -q -w 1 -c 1 192.168.$1.2 > /dev/null ) || return
 echo  "$2" | nc  -q0 192.168.$1.2 9095
}

while true
do

for i in 7 8 9 10;
do
 # echo $i
 ./pide_estado.sh $i | grep "X=" &
 manda_comando $i "X= $(($j+$i)) " &
 j=$((j+4))
done

res1=$(netstat |grep 9095| wc )


echo -e "\n\n\t\t>>>>NETSTAT<<<<<\n\t\t${res1}\n"
sleep 1

done
