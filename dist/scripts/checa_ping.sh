

IPMQTT=192.168.0.1


i=0

while true
do
 if ping -c1 $IPMQTT 
 then
  echo "esta alive"
  break
 fi
 i=$(($i+1))
 if [ $i -gt 10 ]
 then
  echo "Error"
  break
 fi
done

