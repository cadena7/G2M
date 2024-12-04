#!/bin/bash

ping -q -w 1 -c 1 192.168.$1.2 || exit

res=$(echo ESTADO | nc  -q0 192.168.$1.2 9095)
echo  "EDO 192.168.$1.2 >> ${res}"
