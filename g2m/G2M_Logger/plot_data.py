'''
SCRIPT PARA LEER LA BASE DE DATOS GENERARA CON EL LOGGER
Y GRAFICARLA


AUTOR: EDGAR OMAR CADENA ZEPEDA
FECHA: 26 DE JUNIO DE 2025

Dependencias:
pip3 install pandas matplotlib seaborn
'''


 
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os
import datetime

# --- Configuración ---
DATABASE_NAME = "mqtt_data.db"
TABLE_NAME = "sensor_readings"

def plot_sensor_data():
    """
    Lee los datos de la base de datos SQLite y los grafica.
    """
    db_path = os.path.join(os.getcwd(), DATABASE_NAME)

    if not os.path.exists(db_path):
        print(f"Error: La base de datos '{DATABASE_NAME}' no se encontró en '{os.getcwd()}'.")
        print("Asegúrate de que el script 'mqtt_logger.py' haya creado la base de datos.")
        return

    try:
        conn = sqlite3.connect(db_path)
        # Leer los datos de la tabla en un DataFrame de pandas
        df = pd.read_sql_query(f"SELECT timestamp, ar, dec, foco, zoom FROM {TABLE_NAME} ORDER BY timestamp", conn)
        conn.close()

        if df.empty:
            print("La tabla está vacía. No hay datos para graficar.")
            return

        # Convertir la columna 'timestamp' a formato datetime para poder graficarla correctamente
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # --- Crear los gráficos ---

        plt.style.use('seaborn-v0_8-darkgrid') # Un estilo visual agradable
        fig, axes = plt.subplots(nrows=4, ncols=1, figsize=(12, 16), sharex=True) # 4 subplots, compartiendo el eje X

        # Gráfico para AR
        axes[0].plot(df['timestamp'], df['ar'], label='AR', color='blue')
        axes[0].set_title('Valores de AR a lo largo del tiempo')
        axes[0].set_ylabel('AR')
        axes[0].legend()

        # Gráfico para DEC
        axes[1].plot(df['timestamp'], df['dec'], label='DEC', color='green')
        axes[1].set_title('Valores de DEC a lo largo del tiempo')
        axes[1].set_ylabel('DEC')
        axes[1].legend()

        # Gráfico para FOCO
        axes[2].plot(df['timestamp'], df['foco'], label='FOCO', color='red')
        axes[2].set_title('Valores de FOCO a lo largo del tiempo')
        axes[2].set_ylabel('FOCO')
        axes[2].legend()

        # Gráfico para ZOOM
        axes[3].plot(df['timestamp'], df['zoom'], label='ZOOM', color='purple')
        axes[3].set_title('Valores de ZOOM a lo largo del tiempo')
        axes[3].set_ylabel('ZOOM')
        axes[3].set_xlabel('Tiempo') # El eje X solo en el último subplot
        axes[3].legend()

        # Ajustar el diseño para evitar superposiciones
        plt.tight_layout()

        # Mostrar el gráfico
        plt.show()

    except sqlite3.Error as e:
        print(f"Error de base de datos: {e}")
    except Exception as e:
        print(f"Ocurrió un error inesperado al graficar: {e}")

if __name__ == "__main__":
    # Asegurarse de que las librerías necesarias estén instaladas
    try:
        import pandas as pd
        import matplotlib.pyplot as plt
    except ImportError:
        print("Las librerías 'pandas' y 'matplotlib' no están instaladas.")
        print("Por favor, instálalas ejecutando:")
        print("pip install pandas matplotlib seaborn") # Incluimos seaborn para el estilo
        sys.exit(1)
    plot_sensor_data()