#! /bin/bash

# Manual script to kill orphan processes left by nuevo-guiador-test-2024.sh
# This is only a temporal script while the final solution is implemented


for pid in $(ps -ef | grep "python gscui.py --port 1883 --host 192.168.0.237 --debug=1 --tel=2m" | awk '{print $2}'); do kill -15 $pid; done

for pid in $(ps -ef | grep "/bin/bash ./ejec_gscui.sh" | awk '{print $2}'); do kill -15 $pid; done

for pid in $(ps -ef | grep "python motgui-2m.py --port 1883 --host 192.168.0.237 --debug=2" | awk '{print $2}'); do kill -15 $pid; done

for pid in $(ps -ef | grep "/bin/bash ./ejec_mot_guiadorui-2m.sh" | awk '{print $2}'); do kill -15 $pid; done

for pid in $(ps -ef | grep "python gscui.py" | awk '{print $2}'); do kill -15 $pid; done

for pid in $(ps -ef | grep "python motgui-2m.py" | awk '{print $2}'); do kill -15 $pid; done

for pid in $(ps -ef | grep "python gscd.py --host 192.168.0.237 --port 1883 --tel 2m" | awk '{print $2}'); do kill -15 $pid; done
