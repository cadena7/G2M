#!/bin/env bash


# Activar el entorno virtual
cd /home/guiador/venv/bin/
source activate

# Ir al directorio de los scripts
cd /home/guiador/dist/

# Ejecutar el script de Python
python g2mdrvmqtt.py

