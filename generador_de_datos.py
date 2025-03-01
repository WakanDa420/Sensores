# Ejecuta este script para generar datos de prueba directamente en PostgreSQL
import pandas as pd
import numpy as np
import random
import time
from sqlalchemy import create_engine, text
import datetime

# Configuración de conexión
engine = create_engine('postgresql+psycopg2://postgres:12345@localhost:5432/backup')

# Crea la tabla si no existe (asegúrate de que se llame sensores3)
with engine.connect() as conn:
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS sensores3 (
        id SERIAL PRIMARY KEY,
        device VARCHAR(50),
        ip VARCHAR(50),
        lux FLOAT,
        nh3 FLOAT,
        hs FLOAT,
        h FLOAT,
        t FLOAT,
        time TIMESTAMP
    )
    """))
    conn.commit()

# Bucle para generar datos continuamente
print("Generando datos para la tabla sensores3...")
try:
    while True:
        # Genera datos para tres dispositivos
        for device in ["ESP32-Sensor1", "ESP32-Sensor2", "ESP32-Sensor3"]:
            data = {
                "device": device,
                "ip": "192.168.1.100",
                "lux": round(random.uniform(100.0, 500.0), 2),
                "nh3": round(random.uniform(5.0, 20.0), 2),
                "hs": round(random.uniform(30.0, 350.0), 2),
                "h": round(random.uniform(50.0, 90.0), 2),
                "t": round(random.uniform(18.0, 35.0), 2),
                "time": datetime.datetime.now()
            }
            df = pd.DataFrame([data])
            
            # Inserta en la base de datos
            df.to_sql('sensores3', engine, if_exists='append', index=False)
            print(f"Datos insertados para {device}: {data}")
        
        # Espera antes de la siguiente inserción
        wait_time = random.randint(5, 15)
        print(f"Esperando {wait_time} segundos...")
        time.sleep(wait_time)
except KeyboardInterrupt:
    print("\nGeneración de datos detenida por el usuario")