 
  
'''
SCRIPT PARA LEER LA BASE DE DATOS GENERARA CON EL LOGGER
Y CONVERTIRLA EN FORMATO DE EXCEL


AUTOR: EDGAR OMAR CADENA ZEPEDA
FECHA: 26 DE JUNIO DE 2025

Dependencias:
pip3 install pandas
pip3 install openpyxl

python3 data2excel.py

'''

 
import sqlite3
import pandas as pd

conn = sqlite3.connect('mqtt_data.db')
df = pd.read_sql_query("SELECT * FROM sensor_readings", conn)
conn.close()
print(df.head())
# Para guardar en Excel:
df.to_excel("sensor_data.xlsx", index=False)
print("Datos guardados en sensor_data.xlsx")