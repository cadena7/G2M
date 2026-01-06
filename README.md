Fecha   14 mayo 2025

*****************

## en la version de edgar aqui es el directorio de trabajo
El directorio en el pi de estos archivos es: /home/guiador/dist

#Para hacer una conexión con una terminal:
ssh guiador@192.168.0.205
contraseña p4guiador

#checar temperatura de la rpi
cat /sys/devices/virtual/thermal/thermal_zone0/temp


CONFIGURAR RPI CON IP PARA PODER COMUNICARSE CON LA POCKETBB

sudo ifconfig eth1 192.168.7.1/30 up   # cambiar el 7 por el numero asignado a la pocket

*****************

#En crontab arranca este comando:
# m h  dom mon dow   command
@reboot         sh -c "cd /home/guiador/dist/scripts;bash aplica.sh > /dev/null"

*****************
para editar el archivo de crontab se usa el comando:

crontab -e

y para ver que se haya guardado se usa
crontab -l

*****************

el archivo aplica.sh basicamente llama a otro archivo que se llama aplica_dist.sh y luego ese a su vez llama al archivo config_ips_g2m.sh
donde se encuentra la configuracion de las pocketbeagles en cuanto a cada eje, este archivo se debe modificar cuando se cambia
de pocketbeagle porque cada una tiene su identificador de hardware

*****************
#ubicacion del archivo de configuracion de PIDs
cat /home/guiador/dist/guiador2m.cfg

el programa que lee el archivo de entonacion guiador2m.cfg se llama instruccionesguiador.py

el archivo guiador2m.cfg guarda la entonacion deseada de cada eje, los comandos estan descritos en el reporte tecnico de chava de servoPB

En el archivo instruccionesguiador.py se describe la relacion entre cada IP de las pockets y cada Eje

*****************

el archivo de configuracion de supervisor se encuentra en
/etc/supervisor/conf.d

*****************

Para enviar comandos al guiador desde sonaja:

hacer source desde la consola del siguiente scripts:
cd /home/observa/chava/g2m
source fns_g2m.sh

#para enviar instrucciones a cada eje escribir primero:
ejedec  
ejear  
ejefoco  
ejezoom

#ejemplo mover libremente el eje dec
ejedec RST_S ERROR_MAXX 0
ejedec DAX -5000; sleep 5; ejedec DAX 0
ejedec DAX 5000; sleep 5; ejedec DAX 0


#ejemplo mover libremente el eje ar
ejear RST_S ERROR_MAXX 0
ejear DAX -5000; sleep 5; ejear DAX 0
ejear DAX 5000; sleep 5; ejear DAX 0


#ejemplo mover libremente el eje foco
ejefoco RST_S ERROR_MAXX 0
ejefoco DAX -5000; sleep 5; ejefoco DAX 0
ejefoco DAX 5000; sleep 5; ejefoco DAX 0


#ejemplo mover libremente el eje zoom
ejezoom RST_S ERROR_MAXX 0
ejezoom DAX -5000; sleep 5; ejezoom DAX 0
ejezoom DAX 5000; sleep 5; ejezoom DAX 0


*****************


#abrir un lazo de un eje
ejedec DAX 0

#cerrar un lazo de un eje
ejedec CONTROL_PIDX

#verifica estado de las variables
edog2mj

#ejemplos mover a posiciones fijas
ag2m DEC= 800  FCMD
ag2m AR= 500  FCMD
ag2m FOCO= 20  FCMD

#cambiar parametros del pid al vuelo
ejear KPX 8 KIX 0.001 KDX 0.1 ILX 400
ejear CGANX 5000 2
ejear CGANX 0 0
ejear AX= 0.025 VX= 2

#ejemplos busca inicios de ejes
ag2m RESTABLECE_BANDERA_ERR  FCMD
ag2m BUSCA_CENTRO_FOCO  FCMD
ag2m BUSCA_CENTRO_AR  FCMD
ag2m BUSCA_CENTRO_DEC  FCMD
ag2m BUSCA_CENTRO_ZOOM  FCMD


*****************

#Correspondencia de IP a eje, ping desde la pi
#ZOOM	192.168.7.2
#FOCO	192.168.8.2
#DEC	192.168.9.2
#AR	    192.168.10.2




#Checa estado de cada beaglebone
echo ESTADO | nc 192.168.7.2 9095
echo ESTADO | nc 192.168.8.2 9095
echo ESTADO | nc 192.168.9.2 9095
echo ESTADO | nc 192.168.10.2 9095


#Monitorear un estado de una beaglebone continuamente
while sleep 1; do echo ESTADO | nc 192.168.7.2 9095; done
while sleep 1; do echo ESTADO | nc 192.168.8.2 9095; done
while sleep 1; do echo ESTADO | nc 192.168.9.2 9095; done
while sleep 1; do echo ESTADO | nc 192.168.10.2 9095; done


#ejemplo mover libremente los ejes desde la pi
#DEC
echo RST_S ERROR_MAXX 0 | nc 192.168.9.2 9095
echo DAX 5000 | nc 192.168.9.2 9095; sleep 5; echo DAX 0 | nc 192.168.9.2 9095

#AR	
echo RST_S ERROR_MAXX 0 | nc 192.168.10.2 9095
echo DAX 5000 | nc 192.168.10.2 9095; sleep 5; echo DAX 0 | nc 192.168.10.2 9095

#FOCO
echo RST_S ERROR_MAXX 0 | nc 192.168.8.2 9095
echo DAX 5000 | nc 192.168.8.2 9095; sleep 5; echo DAX 0 | nc 192.168.8.2 9095

#ZOOM
echo RST_S ERROR_MAXX 0 | nc 192.168.7.2 9095
echo DAX 5000 | nc 192.168.7.2 9095; sleep 5; echo DAX 0 | nc 192.168.7.2 9095

*****************

#Para hacer una conexión con una terminal:
ssh -p 2276 debian@192.168.7.2
ssh -p 2276 debian@192.168.8.2
ssh -p 2276 debian@192.168.9.2
ssh -p 2276 debian@192.168.10.2
contraseña temppwd

su
root

#hacer un reset
echo b > /proc/sysrq-trigger


#Para editar los archivos en la pocketbeagle:
sudo mount -o remount,rw /
### editar archivos ###
scp -P 2276 servobb debian@192.168.10.2:/home/debian/chava2/servo/.
sudo mount -o remount,ro /
sync

*****************

#Ejemplo para entonar el eje DEC:
ejedec DAX 0 HABTASK RST FCMD
ejedec KPX 12 KIX 0.001 KDX 0.1 ILX 4000 FCMD
ejedec VX= 3 AX= .6  FCMD
ejedec ERROR_MAXX 6000 CONTROL_PIDX FCMD
ag84 DEC= 800  FCMD

*****************























