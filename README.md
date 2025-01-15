# G2M
Guiador del 2m

Fecha   10 enero 2024

*****************
## en la version de edgar aqui es el directorio de trabajo
El directorio en el pi de estos archivos es: /home/guiador/dist

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
el programa que lee el archivo de entonacion guiador2m.cfg se llama instruccionesguiador.py

el archivo guiador2m.cfg guarda la entonacion deseada de cada eje, los comandos estan descritos en el reporte tecnico de chava de servoPB

*****************
el archivo de configuracion de supervisor se encuentra en
/etc/supervisor/conf.d

*****************
Para enviar comandos al guiador desde sonaja:

hacer source desde la consola del siguiente scripts
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
#DEC	192.168.9.2
#AR	    192.168.10.2
#FOCO	192.168.8.2
#ZOOM	192.168.7.2


#Checa estado de cada beaglebone
echo ESTADO | nc 192.168.7.2 9095
echo ESTADO | nc 192.168.8.2 9095
echo ESTADO | nc 192.168.9.2 9095
echo ESTADO | nc 192.168.10.2 9095

#Monitorear un estado de una beaglebone continuamente
while sleep 1; do echo ESTADO | nc 192.168.9.2 9095; done

*****************
