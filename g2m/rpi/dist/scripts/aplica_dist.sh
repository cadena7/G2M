#!/bin/bash

bash config_ips_g2m.sh

sleep 1


#bash checa_ping.sh

echo "al dir de python"
cd ..

#python servg2m.py &> /dev/null &
#python servg2m.py > /dev/null &
sleep 1



#source /home/guiador/venv/bin/activate
#python g2mdrvmqtt_edgar.py &> /dev/null &
#python g2mdrvmqtt.py &> /dev/null &
#python g2mdrvmqtt.py &> /dev/shm/g2mdrv.log &

echo "Fin $0" 
