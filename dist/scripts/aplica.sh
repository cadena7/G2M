#!/bin/bash

export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/games:/usr/games

dt=$(pwd)


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

#until [ `check_ipaddr` -gt 1 ]; 
#do
#  echo "esperando"
#  sleep 2
#done

echo "tengo ip"
sleep 4

cd /home/guiador

if [ -e /home/guiador/dist/scripts/aplica_dist.sh ]
then
  cd dist/scripts
  echo "corriendo aplica_dist.sh"
  bash aplica_dist.sh
fi


