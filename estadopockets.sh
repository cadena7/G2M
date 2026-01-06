#!/bin/bash

# Colores
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # Sin color

# Diccionario de IPs con nombre de eje
declare -A EJE_IPS=(
  ["FOCO"]="192.168.8.2"
  ["DEC"]="192.168.9.2"
  ["AR"]="192.168.10.2"
  ["ZOOM"]="192.168.7.2"
)

PORT=9095

while true; do
    clear
    echo -e "${CYAN}====== ESTADO DE LOS BEAGLEBONES ======${NC}"
    DATE=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "🕒 $DATE"

    for EJE in "${!EJE_IPS[@]}"; do
        IP=${EJE_IPS[$EJE]}
        echo -e "\n🔧 ${CYAN}$EJE ($IP)${NC}"

        RESPONSE=$(echo ESTADO | nc -w 1 "$IP" "$PORT" 2>/dev/null)

        if [ $? -eq 0 ] && [ -n "$RESPONSE" ]; then
            echo -e "${GREEN}$RESPONSE${NC}"
        else
            echo -e "${RED}(Sin respuesta o fallo de conexión)${NC}"
        fi
    done

    sleep 1
done
