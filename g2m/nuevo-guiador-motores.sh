#! /bin/bash

# Script p. ejec. los programas de control del guiador 2m
# 2025 
# E.O.C.Z. 22 julio, 2025
# F. Diaz 5 agosto, 2025 mendaje de ayuda para cuando se demora en abrir la ventana
# E.O.C.Z. 20 febrero, 2026, separar camara de motores como en otros telescopios
## mkdir -p  

mkdir -p /tmp/gsc-tmp
mkdir -p /tmp/home/observa/instrumentacion/bin/

export INSTRUMENTACION=$HOME/instrumentacion
export LD_LIBRARY_PATH=$HOME/instrumentacion/lib/

rm /tmp/autoguiado.log

# Checa si esta vivo el controlador del guiador
MOTG2M=192.168.0.205

## -------------------------------------------------------------------------------
## Checa con el ping a ver si esta vivo el control de motores
i=0
MOTORES_OK=0

while test $i -lt 10
do
  ping -w 1 -c 1 $MOTG2M
  EDOPING=$?
  if test $EDOPING -ne 0
  then
    echo "No esta vivo el controlador de motores del guiador"
    # exit 0
  else
    MOTORES_OK=1
    break
  fi
  let i=$[$i+1]
  sleep 2
done # el test $i -lt 5 

if test $i -eq 10
then
  echo "error no hay com con el control del guiador"
  echo "?? ESTA ENCENDIDO EL CONTROL DE MOTORES DEL GUIADOR ??"
  kill $!
  wish  $INSTRUMENTACION/bin/g2m-err.tk
  exit 0
fi

## -------------------------------------------------------------------------------

cd /home/observa/chava/g2m
./kill-g2m-gscui.sh
sleep 2

cd /home/observa/chava/test_epl/epls/scripts
./ejec_gsc_d.sh stop
./ejec_consola_d.sh stop
sleep 1
./corre_serv_gsc_2m.sh
sleep 1
cd /home/observa/chava/test_epl/uiepls/scripts
./ejec_gscui.sh > /dev/null &
sleep 1
./ejec_mot_guiadorui-2m.sh > /dev/null &
echo kk6
sleep 1





