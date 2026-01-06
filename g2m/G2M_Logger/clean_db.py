 
import sqlite3
import os
import datetime

# --- Configuración ---
DATABASE_NAME = "mqtt_data.db"
TABLE_NAME = "sensor_readings"

def delete_old_data(cutoff_date_str):
    """
    Borra registros de la base de datos anteriores a una fecha específica.
    Args:
        cutoff_date_str (str): La fecha límite en formato 'YYYY-MM-DD'.
    """
    db_path = os.path.join(os.getcwd(), DATABASE_NAME)

    if not os.path.exists(db_path):
        print(f"Error: La base de datos '{DATABASE_NAME}' no se encontró en '{os.getcwd()}'.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Convertir la fecha de corte a un objeto datetime para validación
        try:
            cutoff_datetime = datetime.datetime.strptime(cutoff_date_str, "%Y-%m-%d")
        except ValueError:
            print("Error: Formato de fecha inválido. Por favor, usa 'YYYY-MM-DD'.")
            return

        # Para asegurar que borramos "antes de" la fecha, convertimos la fecha límite
        # a una cadena de texto que SQLite pueda comparar con el campo TEXT de timestamp.
        # Por ejemplo, si cutoff_date_str es '2025-01-01', borraremos todo lo que sea
        # menor a '2025-01-01 00:00:00.000000'.
        sql_cutoff_string = cutoff_datetime.strftime("%Y-%m-%d %H:%M:%S.%f")

        print(f"Conectando a la base de datos: {db_path}")
        print(f"Borrando registros de '{TABLE_NAME}' anteriores a: {cutoff_date_str}")

        # Ejecutar la eliminación
        cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE timestamp < ?", (sql_cutoff_string,))
        rows_deleted = cursor.rowcount

        conn.commit()
        conn.close()

        print(f"Proceso completado. Se eliminaron {rows_deleted} registros.")

    except sqlite3.Error as e:
        print(f"Error de base de datos: {e}")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

if __name__ == "__main__":
    # --- Ejemplo de uso ---
    # Define la fecha límite para borrar datos.
    # Todos los registros con timestamp anterior a esta fecha serán eliminados.
    date_to_delete_before = "2025-06-01" # Por ejemplo, borra todo antes del 1 de Junio de 2025

    delete_old_data(date_to_delete_before)

    print("\nPara ejecutar esto, guarda el código en un archivo (ej. clean_db.py) y corre:")
    print("python3 clean_db.py")