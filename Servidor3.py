# -*- coding: utf-8 -*-
"""
Created on Sun Mar 17 20:03:20 2024

autor: Ivan Camilo Leiton Murcia
"""
from sqlalchemy import create_engine
import socket
import random
import time
import json
import threading
import pandas as pd
import numpy as np

PORT = 8889
IP = "127.0.0.1"  # Cambiar a 127.0.0.1 para escuchar en la interfaz de loopback local

def handler(client_soc):
    client_soc.send(b"a")
    print("Peticion enviada")
    time.sleep(20)
    global df

    try:
        data = client_soc.recv(65536).decode()
        print(f"Datos recibidos: {data}\n")
        if len(data) > 4:
            j = json.loads(data)
            print("Datos JSON recibidos:", j)
            # Agregar fecha y hora actual al JSON
            j["time"] = pd.to_datetime('now')

            # Actualizar DataFrame global
            df = pd.concat([df, pd.DataFrame([j])], ignore_index=True)
            df2 = pd.DataFrame([j])
            df2 = df2.rename(columns={
                'Device': 'device',
                'IP': 'ip',
                'LUX': 'lux',
                'NH3': 'nh3',
                'HS': 'hs',
                'H': 'h',
                'T': 't',
                'time': 'time'
            })
            
            # Convertir la columna 'time' a tipo datetime
            df2['time'] = pd.to_datetime(df2['time'])
            # Modificar la condición para que se generen datos cada minuto
            condicion = df2['time'].apply(lambda x: x.second <= 10)

            # Filtrar el DataFrame usando la condición
            df2_filtrado = df2[condicion]
            print(f"Datos filtrados: {df2_filtrado}")

            # Guardar DataFrame en un archivo Excel
            df.to_excel("data_test_15.xlsx", sheet_name='sheet1', index=False)

            # Generar datos de prueba
            random_lux = random.uniform(110.0, 200.0)
            random_nh3 = random.uniform(5.0, 15.0)
            random_hs = random.uniform(40.0, 310.0)
            random_h = random.uniform(60.0, 80.0)
            random_t = random.uniform(20.0, 40.0)

            # Extraer los primeros valores de df2 para evitar pasar Series
            device_value = df2['device'].values[0]
            ip_value = df2['ip'].values[0]
            time_value = df2['time'].values[0]

            # Crear DataFrame de prueba
            df_test = pd.DataFrame({
                'device': [device_value],
                'ip': [ip_value],
                'lux': [random_lux],
                'nh3': [random_nh3],
                'hs': [random_hs],
                'h': [random_h],
                't': [random_t],
                'time': [time_value]
            })

            # Enviar datos a la base de datos
            send_to_db(df2)
            print("Datos enviados a la base de datos")

    except Exception as e:
        print(f"Error en el handler: {e}")
    
    client_soc.close()

def send_to_db(df):
    try:
        # Conexión a la base de datos PostgreSQL
        engine = create_engine('postgresql+psycopg2://postgres:12345@localhost:5432/backup')
        
        # Insertar datos en la tabla 'sensors3'
        df.to_sql('sensors3', engine, if_exists='append', index=False)
        print("Datos insertados en la base de datos")
    except Exception as e:
        print(f"Error al enviar datos a la base de datos: {e}")

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    global df
    df = pd.DataFrame()
    
    with s:
        s.bind((IP, PORT))
        s.listen(True)
        print(f"Servidor escuchando en {IP}:{PORT}")
        while True:
            client_soc, client_address = s.accept()
            print(f"Conexión aceptada de {client_address}")
            client_soc.settimeout(25)
            threading.Thread(target=handler, args=(client_soc,), daemon=True).start()

if __name__ == "__main__": 
    print("Servidor ON")
    main()
