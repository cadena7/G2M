
mkdir /tmp/uiepls
cp -v -r  /home/chava/workspace/test_oan_mqtt_b1/uiepls/scripts /tmp/uiepls/scripts
cp -r -v /home/chava/workspace/test_oan_mqtt_b1/uiepls/motoresui /tmp/uiepls/motoresui
mkdir /tmp/rpi
cp -r -v /home/chava/trabajo/trabajo_2023/rpi/guiador2m /tmp/rpi/guiador2m

cd /tmp
tar -z -cvf /tmp/respg2m_mqtt.tgz uiepls/ rpi/

echo "Respaldo en " /tmp/respg2m_mqtt.tgz
