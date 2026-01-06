#!/usr/bin/env python
import os
import schedule
import time


def reload_supervisor():
    # Ejecuta el comando con privilegios de superusuario
    os.system("sudo supervisorctl restart mqtt")


# Programa la tarea para que se ejecute todos los días a las 9 AM PST (17:00 GMT)
schedule.every().day.at("17:00").do(reload_supervisor)

# Imprime un mensaje indicando que el script ha iniciado correctamente
print("El script ha iniciado correctamente y se ejecutará todos los días a las 17:00 GMT.")

while True:
    # Ejecuta las tareas programadas
    schedule.run_pending()
    time.sleep(30)
