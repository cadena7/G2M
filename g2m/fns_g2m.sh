#!/bin/bash


IPMOTG2M="192.168.0.205"
PTOMOTG2M=9055

ejezoom () {
  echo "EJEZOOM $@  FCMD" | nc -q0 $IPMOTG2M $PTOMOTG2M
}

ejear () {
 echo "EJEAR $@  FCMD" | nc -q0 $IPMOTG2M $PTOMOTG2M
}

ejedec () {
 echo "EJEDEC $@  FCMD" | nc -q0 $IPMOTG2M $PTOMOTG2M
}

ejefoco () {
 echo "EJEFOCO $@  FCMD" | nc -q0 $IPMOTG2M $PTOMOTG2M
}

cierra_lazos_g2m () {
    ejear CONTROL_PIDX
    ejefoco CONTROL_PIDX
    ejezoom CONTROL_PIDX
    ejedec CONTROL_PIDX
}

abre_lazos_g2m () {
    ejear DAX 0
    ejefoco DAX 0
    ejezoom DAX 0
    ejedec DAX 0
    }


edog2m () {
  echo "EG? EGJ" | nc -q0 $IPMOTG2M $PTOMOTG2M
}

edog2mj () {
echo "EGJ" | nc -q0 $IPMOTG2M $PTOMOTG2M | tr  "," "\n"
    }

ag2m () {
   echo "$@" | nc -q0 $IPMOTG2M $PTOMOTG2M  
}
