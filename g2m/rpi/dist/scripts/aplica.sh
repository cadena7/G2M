#!/bin/bash

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



if [ -e dist/scripts/aplica_dist.sh ]
then
  cd dist/scripts
  bash aplica_dist.sh
fi


