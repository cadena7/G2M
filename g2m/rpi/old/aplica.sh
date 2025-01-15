#!/bin/bash

export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/games:/usr/games

dt=$(pwd)

cd /home/guiador

sudo mount -o ro /dev/mmcblk0p3 mntp3

sleep 1

cd mntp3/app

dt=$(pwd)

if [ -e dist.tgz ]
then
  echo "Ok"
else
 echo "No existe dist.tgz" 
 return 0
fi




cd /dev/shm
tar xvfz ${dt}/dist.tgz

cp ${dt}/guiador2m.cfg /dev/shm/dist

function check_ipaddr () {
  # Here we look for an IP(v4|v6) address when doing ip addr
  # Note we're filtering out 127.0.0.1 and ::1/128 which are the "localhost" ip addresses
  # I'm also removing fe80: which is the "link local" prefix

  ip addr | \
  grep -v 127.0.0.1 | \
  grep -v '::1/128' | \
  grep -v 'inet6 fe80:' | \
  grep -E "inet [[:digit:]]+\.[[:digit:]]+\.[[:digit:]]+\.[[:digit:]]+|inet6" | \
  wc -l
}

until [ `check_ipaddr` -gt 1 ]; 
do
  echo "esperando"
  sleep 2
done

if [ -e dist/scripts/aplica_dist.sh ]
then
  cd dist/scripts
  bash aplica_dist.sh
fi


