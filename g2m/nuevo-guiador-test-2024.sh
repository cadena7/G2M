#! /bin/bash

# Script p. ejec. los programas de control del guiador 2m
# 2024 
# E.O.C.Z. 19 septiembre, 2024

## mkdir -p  

mkdir -p /tmp/gsc-tmp
mkdir -p /tmp/home/observa/instrumentacion/bin/

export INSTRUMENTACION=$HOME/instrumentacion
export LD_LIBRARY_PATH=$HOME/instrumentacion/lib/

rm /tmp/autoguiado.log

QUE_SEC=`wish $INSTRUMENTACION/bin/g2m-pide-sec.tk`

echo $QUE_SEC

if [ "$QUE_SEC" = "sec=0" ]
then
 echo SECUNDARIO=75
 SECUNDARIO=75
 ESCALA_PLACA="0.0"
fi

if [ "$QUE_SEC" = "sec=1" ]
then
 echo SECUNDARIO=135
 SECUNDARIO=135
 ESCALA_PLACA="-0.016"
fi


if [ "$QUE_SEC" = "sec=2" ]
then
 echo SECUNDARIO=30
 SECUNDARIO=30
 ESCALA_PLACA="0.116"
fi



# primero verifica que no este corriendo el prog. de g2m




# $INSTRUMENTACION/bin/checag2m
#$INSTRUMENTACION/bin/g2m-checa_ui_motores



if test  1 -eq $?
then
  echo "Ya esta ejecutandose el programa de guiador 2M (El TIJUANO)"
wish $INSTRUMENTACION/bin/g2m-ejec.tk
  exit 0
fi



if test -z "$SECUNDARIO"
then
 SECUNDARIO=135
fi


if test -z "$ESCALA_PLACA"
then
  ESCALA_PLACA="-0.016"
fi



# Desp. el msg. de bienvenida

#wish $INSTRUMENTACION/bin/g2m-bv.tk &

#sleep 3

# Checa si esta vivo el controlador del guiador
MOTG2M=192.168.0.205
CAMG2M=192.168.0.206
# MOTG2M=localhost
# CAMG2M=localhost


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
  echo "?? ESTA ENCENDIDO EL CONTROL DE CAMARA MOTORES DEL GUIADOR ??"
  wish  $INSTRUMENTACION/bin/g2m-err.tk
  exit 0
fi


## ------------------------------------------------------------------------------



ELFAUCET=$INSTRUMENTACION/bin/g2m-faucet

/usr/bin/killall -KILL $ELFAUCET

## ------------------------------------------------------------------------------

LA_CAM=" --pto_camara=4950 --host_camara=192.168.0.206 "


SAL=`$INSTRUMENTACION/bin/configcamguiador.sh  $SECUNDARIO | grep SECUNDARIO`

## SAL=`./configcamguiador.sh  $SECTEL | grep SECUNDARIO `

echo "SALIDA DE CONFIGCAMGUIADOR $SAL"

SECUND="-i0"

if  test "$SAL"  == "SECUNDARIO:75"
then
    SECUND="-i0"
fi  
 
if  test "$SAL"  == "SECUNDARIO:135"
then
    SECUND="-i1"
fi

if  test "$SAL"  == "SECUNDARIO:30"
then
    SECUND="-i2"
fi


echo "EL SECUNDARIO ACTUAL = $SECUND "


## $INSTRUMENTACION/bin/g2m -s $LA_CAM $SECUND


## Ejecuta la ventana para utilizar valores kp separados
## Estos valores los lee de los archivos VALORKP
cd /usr/local/instrumentacion/bin
./kill-g2m-gscui.sh
sleep 2

cd /home/observa/instrumentacion/bin
python cambiakp.py &
sleep 1

cd /home/observa/chava/test_epl/epls/scripts
./ejec_gsc_d.sh stop
./ejec_consola_d.sh stop
sleep 1
./corre_serv_gsc_2m.sh

cd /home/observa/chava/test_epl/uiepls/scripts
./ejec_gscui.sh > /dev/null &
sleep 1
./ejec_mot_guiadorui-2m.sh > /dev/null &
sleep 1

$INSTRUMENTACION/bin/camguiador -p4950 -h192.168.0.206 $SECUND &
#p1=$!
#$INSTRUMENTACION/bin/g_gsc  -e &
#p2=$!
#$INSTRUMENTACION/bin/ui_motores -p4955 -h192.168.0.205 $SECUND -j$ESCALA_PLACA






#kill -KILL $p1
#kill -KILL $p2





