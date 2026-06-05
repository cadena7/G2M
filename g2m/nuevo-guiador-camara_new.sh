#! /bin/bash

# Script p. ejec. los programas de control del guiador 2m
# 2026 
# E.O.C.Z. 24 abril, 2026, nueva camara
###

mkdir -p /tmp/gsc-tmp
mkdir -p /tmp/home/observa/instrumentacion/bin/

export INSTRUMENTACION=$HOME/instrumentacion
export LD_LIBRARY_PATH=$HOME/instrumentacion/lib/

rm /tmp/autoguiado.log

# Checa si esta viva la camara del guiador
CAMG2M=192.168.0.201

## -------------------------------------------------------------------------------

i=0
CAMARA_OK=0

while test $i -lt 10
do
  ping -w 1 -c 1 $CAMG2M
  EDOPING=$?
  if test $EDOPING -ne 0
  then
    echo "No esta vivo el controlador de la camara del guiador"
    # exit 0
  else
     kill $!     #Mata el wish de bienvenida
     break
  fi
  let i=$[$i+1]
  sleep 2
done # el test $i -lt 5

if test  $i -eq 10
then
  kill $!     #Mata el wish de bienvenida
  echo "error no hay com con el control de camara del guiador"
  echo "?? ESTA ENCENDIDO EL CONTROL DE CAMARA DEL GUIADOR ??"
  wish  $INSTRUMENTACION/bin/g2m-err.tk
  exit 0
fi

## ------------------------------------------------------------------------------
#ELFAUCET=$INSTRUMENTACION/bin/g2m-faucet

#/usr/bin/killall -KILL $ELFAUCET

## ------------------------------------------------------------------------------

cd /home/observa/chava/g2m
./kill-g2m-cam.sh
sleep 2

cd /home/observa/chava/test_epl/epls/scripts
./ejec_camguiador_d.sh stop
sleep 1
./ejec_camguiador_d.sh start
sleep 1
cd /home/observa/chava/test_epl/uiepls/scripts
#./ejec_camguiaui.sh > /dev/null &
./ejec_camguiaui.sh
echo kk6
sleep 1







