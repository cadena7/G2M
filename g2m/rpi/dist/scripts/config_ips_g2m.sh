#!/bin/bash

export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/games:/usr/games


id1=1736GPB20546
#id2=1741GPB20542
id3=1741GPB42111
id4=1741GPB20518

id2=1741GPB42035

ip1=192.168.7
ip2=192.168.10
ip3=192.168.8
ip4=192.168.9



function conf_ip () {
 IP=$3
 DEV=$2
 SERID=$1

 echo "IP=" $IP
 echo "DEV=" $DEV 
 echo "SERID=" $SERID
 sudo ifconfig $DEV ${IP}.1
 sudo route add -host ${IP}.2  gw ${IP}.1 ${DEV}
}



for i in {0..3};
do
 devid=eth$(($i+1))
 echo ${devid}
 res=$(udevadm info  /sys/class/net/${devid}|grep ID_USB_SERIAL_SHORT)
 echo "res=" $res
 id=$(echo ${res} | tr '=' ' '| awk '{print $3}' )

 [ "${id}"  == "${id1}" ] && conf_ip $id1 ${devid} ${ip1}

 [ "${id}"  == "${id2}" ] && conf_ip $id2 ${devid} ${ip2}

 [ "${id}"  == "${id3}" ] && conf_ip $id3 ${devid} ${ip3}

 [ "${id}"  == "${id4}" ] && conf_ip $id4 ${devid} ${ip4}  


done
