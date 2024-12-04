#!/bin/bash

bash config_ips_g2m.sh

sleep 1

echo "Conf el IP"
sudo ifconfig > /dev/shm/if.log
sudo ifconfig eth0 down
sudo ifconfig eth0 192.168.0.205 netmask 255.255.255.0 up
sudo route del default gw 192.168.0.253
sudo route add default gw 192.168.0.254 eth0
#sudo route add net 192.168.0.0 eth0
sudo ifconfig lo 127.0.0.1
sudo ifconfig >> /dev/shm/if.log


sleep 5
bash checa_ping.sh

echo "al dir de python"
cd ..

python servg2m.py > /dev/null &
sleep 1



source /home/guiador/venv/bin/activate
python g2mdrvmqtt.py &> /dev/shm/g2mdrv.log &

echo "Fin $0" 
