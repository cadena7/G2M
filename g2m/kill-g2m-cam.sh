#! /bin/bash

# Manual script to kill orphan processes left by nuevo-guiador-test-2024.sh
# This is only a temporal script while the final solution is implemented


for pid in $(ps -ef | grep "python ./eguiador.py" | awk '{print $2}'); do kill -15 $pid; done

for pid in $(ps -ef | grep "python cambiakp.py" | awk '{print $2}'); do kill -15 $pid; done

for pid in $(ps -ef | grep "/home/observa/instrumentacion/bin/camguiador -p4950 -h192.168.0.206 -i0" | awk '{print $2}'); do kill -15 $pid; done

for pid in $(ps -ef | grep "/home/observa/instrumentacion/bin/camguiador -p4950 -h192.168.0.206 -i1" | awk '{print $2}'); do kill -15 $pid; done

for pid in $(ps -ef | grep "/home/observa/instrumentacion/bin/camguiador -p4950 -h192.168.0.206 -i2" | awk '{print $2}'); do kill -15 $pid; done

for pid in $(ps -ef | grep "python ./eguiador.py" | awk '{print $2}'); do kill -15 $pid; done

for pid in $(ps -ef | grep "/bin/bash ./ejec_camguiaui.sh" | awk '{print $2}'); do kill -15 $pid; done

for pid in $(ps -ef | grep "/usr/bin/wish -f /usr/share/saods9/library/ds9.tcl -title CGUIAGC3" | awk '{print $2}'); do kill -15 $pid; done

for pid in $(ps -ef | grep "python guiacamepl.py --debug=0 --caja=80 --binning=4 --host=192.168.0.237 --port=1883 --urljpeg=http://localhost:8081/ --cols=3448 --rengs=2574" | awk '{print $2}'); do kill -15 $pid; done

for pid in $(ps -ef | grep "python guiacamepl.py --debug=0 --caja=80 --binning=4 --host=192.168.0.237 --port=1883 --urljpeg=http://localhost:8081/ --cols=3448 --rengs=2574" | awk '{print $2}'); do kill -15 $pid; done

for pid in $(ps -ef | grep "python -m camguiad.camgd --host_mqtt=192.168.0.237 --port_mqtt=1883 --host 192.168.0.201 --port 4950" | awk '{print $2}'); do kill -15 $pid; done