 
'''
SCRIPT PARA LEER EL MQTT DEL GUIADOR DEL 2M Y ALMACENAR LOS DATOS EN UNA BASE
DE DATOS SQLITE3 PARA DETERMINAR SI EL GUIADOR TIENE OSCILACION DURANTE LAS OPERACIONES
NOCTURNAS DEL TELESCOPIO

LAS HORAS DE MUESTREO SON AJUSTABLES EN LA VARIABLE GLOBAL DURATION_HOURS

AUTOR: EDGAR OMAR CADENA ZEPEDA
FECHA: 26 DE JUNIO DE 2025

Dependencias:
pip install paho-mqtt


Para mantenerlo corriendo en segundo plano (y que no dependa de la terminal):


nohup python3 mqtt_logger.py &

'''


import sqlite3
import json
import time
import datetime
import signal
import sys
import paho.mqtt.client as mqtt # Importamos la librería paho-mqtt
import os # Para obtener la ruta del directorio de ejecución

# --- Configuración ---
DATABASE_NAME = "mqtt_data.db"
TABLE_NAME = "sensor_readings"
MQTT_BROKER_HOST = "192.168.0.1"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "oan/control/2m/guiador/motores/status"
DURATION_HOURS = 12
SAMPLING_INTERVAL_SECONDS = 1 # Esto ahora se manejará con la recepción de mensajes, no con un sleep fijo

# Variable global para controlar la terminación del script
running = True
mqtt_client = None # Para almacenar la instancia del cliente MQTT
last_data_received_time = None # Para controlar el tiempo de muestreo

def signal_handler(sig, frame):
    """Maneja las señales para un cierre elegante."""
    global running, mqtt_client
    print(f"\nSeñal {sig} recibida. Deteniendo la captura de datos...")
    running = False
    if mqtt_client:
        mqtt_client.loop_stop() # Detener el bucle del cliente MQTT
        mqtt_client.disconnect() # Desconectar del broker
    sys.exit(0)

def setup_database():
    """Configura la base de datos SQLite y la tabla."""
    # os.path.join asegura que la ruta sea correcta en cualquier SO
    db_path = os.path.join(os.getcwd(), DATABASE_NAME)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            ar REAL,
            dec REAL,
            foco REAL,
            zoom REAL
        )
    ''')
    conn.commit()
    conn.close()
    print(f"Base de datos '{db_path}' y tabla '{TABLE_NAME}' configuradas.")

def insert_data(ar, dec, foco, zoom):
    """Inserta los datos en la base de datos."""
    db_path = os.path.join(os.getcwd(), DATABASE_NAME)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    cursor.execute(f'''
        INSERT INTO {TABLE_NAME} (timestamp, ar, dec, foco, zoom)
        VALUES (?, ?, ?, ?, ?)
    ''', (timestamp, ar, dec, foco, zoom))
    conn.commit()
    conn.close()

# --- Callbacks de Paho-MQTT ---
def on_connect(client, userdata, flags, rc):
    """Callback cuando el cliente se conecta al broker."""
    if rc == 0:
        print("Conectado exitosamente al broker MQTT.")
        client.subscribe(MQTT_TOPIC)
        print(f"Suscrito al tópico: '{MQTT_TOPIC}'")
    else:
        print(f"Fallo al conectar, código de retorno: {rc}")

def on_message(client, userdata, msg):
    """Callback cuando se recibe un mensaje del tópico suscrito."""
    global last_data_received_time
    current_time = datetime.datetime.now()

    # Si ha pasado menos de 1 segundo desde la última vez que procesamos datos
    if last_data_received_time and (current_time - last_data_received_time).total_seconds() < SAMPLING_INTERVAL_SECONDS:
        # print("Demasiado rápido, ignorando este mensaje para respetar el intervalo de 1 segundo.")
        return

    try:
        payload_str = msg.payload.decode('utf-8')
        data = json.loads(payload_str)

        ar = data.get("AR")
        dec = data.get("DEC")
        foco = data.get("FOCO")
        zoom = data.get("ZOOM")

        if all(x is not None for x in [ar, dec, foco, zoom]):
            insert_data(ar, dec, foco, zoom)
            print(f"[{current_time.strftime('%H:%M:%S')}] Datos recibidos e insertados: AR={ar}, DEC={dec}, FOCO={foco}, ZOOM={zoom}")
            last_data_received_time = current_time # Actualizar el tiempo del último dato insertado
        else:
            print(f"Advertencia: JSON recibido no contiene todos los campos esperados: {payload_str}")

    except json.JSONDecodeError:
        print(f"Error: Mensaje MQTT no es un JSON válido: {msg.payload.decode('utf-8')}")
    except Exception as e:
        print(f"Error al procesar o insertar datos MQTT: {e}")

def main():
    global running, mqtt_client
    signal.signal(signal.SIGINT, signal_handler)  # Captura Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler) # Captura SIGTERM

    setup_database()

    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    try:
        mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
        mqtt_client.loop_start() # Iniciar el bucle de procesamiento de mensajes en un hilo separado
    except Exception as e:
        print(f"No se pudo conectar al broker MQTT en {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}. Error: {e}")
        sys.exit(1)

    start_time = datetime.datetime.now()
    end_time = start_time + datetime.timedelta(hours=DURATION_HOURS)

    print(f"Iniciando la captura de datos MQTT. Se ejecutará por {DURATION_HOURS} horas.")
    print(f"Hora de inicio: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Hora de finalización estimada: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

    while running and datetime.datetime.now() < end_time:
        # El bucle principal solo necesita mantenerse vivo
        # La recepción de mensajes es manejada por mqtt_client.loop_start()
        time.sleep(1) # Pequeña pausa para no consumir CPU innecesariamente

    print("Tiempo de ejecución terminado o script detenido por señal.")
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
    print("Desconectado del broker y script finalizado.")


if __name__ == "__main__":
    # Asegurarse de que paho-mqtt esté instalado
    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        print("La librería 'paho-mqtt' no está instalada.")
        print("Por favor, instálala ejecutando: pip install paho-mqtt")
        sys.exit(1)
    main()