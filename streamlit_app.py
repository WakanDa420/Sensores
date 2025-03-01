import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
import datetime
import time
import numpy as np
from plotly.subplots import make_subplots

# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Monitoreo de Sensores",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #E5E7EB;
    }
    .card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .metric-title {
        font-size: 1rem;
        font-weight: 600;
        color: #4B5563;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1E3A8A;
    }
    .status-good {
        color: #059669;
        font-weight: 600;
    }
    .status-warning {
        color: #D97706;
        font-weight: 600;
    }
    .status-alert {
        color: #DC2626;
        font-weight: 600;
    }
    .last-update {
        font-size: 0.8rem;
        color: #6B7280;
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

# Función para conectar a la base de datos
@st.cache_resource
def get_connection():
    try:
        conn = create_engine('postgresql+psycopg2://postgres:12345@localhost:5432/backup')
        return conn
    except Exception as e:
        st.error(f"Error de conexión a la base de datos: {e}")
        return None

# Función para obtener datos de la base de datos
def get_sensor_data(hours=1):
    conn = get_connection()
    if conn:
        try:
            # Consulta para obtener datos recientes basados en las horas especificadas
            query = f"""
            SELECT * FROM sensores3 
            WHERE time >= NOW() - INTERVAL '{hours} hours'
            ORDER BY time ASC
            """
            df = pd.read_sql_query(query, conn)
            return df
        except Exception as e:
            st.error(f"Error al consultar datos: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

# Función para obtener los datos más recientes por dispositivo
def get_latest_readings():
    conn = get_connection()
    if conn:
        try:
            query = """
            SELECT DISTINCT ON (device) *
            FROM sensores3
            ORDER BY device, time DESC
            """
            return pd.read_sql_query(query, conn)
        except Exception as e:
            st.error(f"Error al obtener lecturas recientes: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

# Función para evaluar el estado de una lectura
def evaluate_status(value, sensor_type):
    if sensor_type == 'lux':
        if value < 150:
            return "Baja", "status-warning"
        elif value > 450:
            return "Alta", "status-warning"
        else:
            return "Normal", "status-good"
    elif sensor_type == 'nh3':
        if value > 15:
            return "Alta", "status-alert"
        elif value > 10:
            return "Moderada", "status-warning"
        else:
            return "Normal", "status-good"
    elif sensor_type == 'hs':
        if value > 250:
            return "Alta", "status-alert"
        elif value > 150:
            return "Moderada", "status-warning"
        else:
            return "Normal", "status-good"
    elif sensor_type == 'h':
        if value < 60:
            return "Baja", "status-warning"
        elif value > 85:
            return "Alta", "status-warning"
        else:
            return "Normal", "status-good"
    elif sensor_type == 't':
        if value > 30:
            return "Alta", "status-alert"
        elif value < 20:
            return "Baja", "status-warning"
        else:
            return "Normal", "status-good"
    else:
        return "Desconocido", ""

# Función para crear una tarjeta de métricas
def metric_card(title, value, unit, status, status_class):
    return f"""
    <div class="card">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value} {unit}</div>
        <div class="{status_class}">Estado: {status}</div>
    </div>
    """

# Barra lateral
st.sidebar.title("Configuración")
update_interval = st.sidebar.slider("Intervalo de actualización (seg)", 5, 60, 10)
time_range = st.sidebar.selectbox(
    "Rango de tiempo para visualización",
    ["1 hora", "6 horas", "12 horas", "24 horas"],
    index=0
)

# Convertir selección a horas
time_dict = {"1 hora": 1, "6 horas": 6, "12 horas": 12, "24 horas": 24}
hours = time_dict[time_range]

selected_devices = st.sidebar.multiselect(
    "Filtrar por dispositivos",
    ["ESP32-Sensor1", "ESP32-Sensor2", "ESP32-Sensor3"],
    default=["ESP32-Sensor1", "ESP32-Sensor2", "ESP32-Sensor3"]
)

# Encabezado principal
st.markdown('<div class="main-header">Dashboard de Monitoreo de Sensores</div>', unsafe_allow_html=True)

# Inicializar el estado de la sesión para el contador de actualizaciones
if 'update_counter' not in st.session_state:
    st.session_state.update_counter = 0
if 'last_update_time' not in st.session_state:
    st.session_state.last_update_time = datetime.datetime.now()

# Contenedor de actualización
update_container = st.container()

# Función principal
def main():
    while True:
        # Obtener datos más recientes
        latest_data = get_latest_readings()
        if latest_data.empty:
            st.warning("No se encontraron datos de sensores. Verifica la conexión a la base de datos.")
            st.stop()
            
        # Incrementar contador de actualizaciones y actualizar timestamp
        st.session_state.update_counter += 1
        st.session_state.last_update_time = datetime.datetime.now()
        
        with update_container:
            col_info1, col_info2 = st.columns([3, 1])
            with col_info1:
                st.subheader("Estado actual de los sensores")
            with col_info2:
                st.markdown(f'<div class="last-update">Última actualización: {st.session_state.last_update_time.strftime("%H:%M:%S")} | Actualizaciones: {st.session_state.update_counter}</div>', unsafe_allow_html=True)

            # Filtrar dispositivos seleccionados
            filtered_latest = latest_data[latest_data['device'].isin(selected_devices)]
            
            # Mostrar tarjetas de estado para cada dispositivo
            devices_count = len(filtered_latest)
            cols = st.columns(devices_count)
            
            for i, (_, device_data) in enumerate(filtered_latest.iterrows()):
                with cols[i]:
                    st.markdown(f"### {device_data['device']}")
                    st.markdown(f"**IP:** {device_data['ip']}")
                    st.markdown(f"**Última lectura:** {device_data['time'].strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # Crear tarjetas para cada sensor
                    for sensor_type, unit in [
                        ('lux', 'lux'), ('nh3', 'ppm'), 
                        ('hs', 'ppm'), ('h', '%'), ('t', '°C')
                    ]:
                        value = device_data[sensor_type]
                        status, status_class = evaluate_status(value, sensor_type)
                        
                        # Títulos más descriptivos
                        titles = {
                            'lux': 'Luminosidad', 
                            'nh3': 'Amoniaco', 
                            'hs': 'Sulfuro de Hidrógeno',
                            'h': 'Humedad',
                            't': 'Temperatura'
                        }
                        
                        st.markdown(
                            metric_card(titles[sensor_type], round(value, 1), unit, status, status_class),
                            unsafe_allow_html=True
                        )
            
            # Obtener datos históricos
            df = get_sensor_data(hours=hours)
            if not df.empty and len(df) > 1:
                # Convertir la columna time a datetime si no lo es
                if not pd.api.types.is_datetime64_any_dtype(df['time']):
                    df['time'] = pd.to_datetime(df['time'])
                
                # Filtrar por dispositivos seleccionados
                df = df[df['device'].isin(selected_devices)]
                
                # Crear pestañas para diferentes visualizaciones
                tab1, tab2, tab3 = st.tabs(["Tendencias en tiempo real", "Comparación entre sensores", "Datos en tabla"])
                
                with tab1:
                    st.subheader(f"Tendencias de las últimas {hours} horas")
                    
                    # Crear gráficos de línea para cada tipo de sensor
                    for sensor_type, title, unit in [
                        ('t', 'Temperatura', '°C'),
                        ('h', 'Humedad', '%'),
                        ('lux', 'Luminosidad', 'lux'),
                        ('nh3', 'Amoniaco', 'ppm'),
                        ('hs', 'Sulfuro de Hidrógeno', 'ppm')
                    ]:
                        fig = px.line(
                            df, x='time', y=sensor_type, color='device',
                            title=f"{title} ({unit})",
                            labels={'time': 'Tiempo', sensor_type: f'{title} ({unit})'},
                            height=350
                        )
                        
                        fig.update_layout(
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                            margin=dict(l=20, r=20, t=40, b=20),
                            hovermode="x unified"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                
                with tab2:
                    st.subheader("Comparación entre sensores")
                    
                    # Selector de variable para comparación
                    compare_var = st.selectbox(
                        "Variable a comparar",
                        [
                            ('t', 'Temperatura (°C)'),
                            ('h', 'Humedad (%)'),
                            ('lux', 'Luminosidad (lux)'),
                            ('nh3', 'Amoniaco (ppm)'),
                            ('hs', 'Sulfuro de Hidrógeno (ppm)')
                        ],
                        format_func=lambda x: x[1]
                    )
                    
                    # Crear gráfico de comparación de barras
                    latest_compare = latest_data[latest_data['device'].isin(selected_devices)]
                    if not latest_compare.empty:
                        fig = px.bar(
                            latest_compare, 
                            x='device', 
                            y=compare_var[0],
                            title=f"Comparación de {compare_var[1]} entre dispositivos",
                            labels={'device': 'Dispositivo', compare_var[0]: compare_var[1]},
                            color='device',
                            height=400
                        )
                        
                        fig.update_layout(
                            xaxis_title="Dispositivo",
                            yaxis_title=compare_var[1],
                            showlegend=False
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Gráfico radar para comparar todos los sensores a la vez
                    if len(latest_compare) > 1:
                        # Normalizar los datos para el gráfico radar
                        radar_vars = ['lux', 'nh3', 'hs', 'h', 't']
                        radar_titles = ['Luminosidad', 'Amoniaco', 'Sulfuro H', 'Humedad', 'Temperatura']
                        
                        # Crear figura con subplots
                        fig = make_subplots(rows=1, cols=1, specs=[[{'type': 'polar'}]])
                        
                        # Normalizar valores para el radar
                        max_vals = {var: df[var].max() for var in radar_vars}
                        min_vals = {var: df[var].min() for var in radar_vars}
                        
                        for _, device_row in latest_compare.iterrows():
                            normalized_vals = []
                            for var in radar_vars:
                                # Evitar división por cero
                                if max_vals[var] - min_vals[var] > 0:
                                    norm_val = (device_row[var] - min_vals[var]) / (max_vals[var] - min_vals[var])
                                else:
                                    norm_val = 0.5
                                normalized_vals.append(norm_val)
                            
                            # Cerrar el polígono
                            normalized_vals.append(normalized_vals[0])
                            radar_titles_closed = radar_titles + [radar_titles[0]]
                            
                            fig.add_trace(go.Scatterpolar(
                                r=normalized_vals,
                                theta=radar_titles_closed,
                                fill='toself',
                                name=device_row['device']
                            ))
                        
                        fig.update_layout(
                            polar=dict(
                                radialaxis=dict(
                                    visible=True,
                                    range=[0, 1]
                                )
                            ),
                            showlegend=True,
                            height=500,
                            title="Perfil comparativo de sensores (normalizado)"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                
                with tab3:
                    st.subheader("Datos en tabla")
                    
                    # Añadir filtros para la tabla
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        n_rows = st.slider("Número de filas a mostrar", 10, 1000, 100, 10)
                    
                    with col2:
                        sort_by = st.selectbox(
                            "Ordenar por",
                            ["time", "device", "lux", "nh3", "hs", "h", "t"],
                            index=0
                        )
                    
                    # Preparar y mostrar la tabla con formato
                    table_df = df.sort_values(by=sort_by, ascending=False).head(n_rows).copy()
                    
                    # Formatear valores numéricos y fechas para mejor visualización
                    for col in ['lux', 'nh3', 'hs', 'h', 't']:
                        table_df[col] = table_df[col].round(2)
                    
                    table_df['time'] = table_df['time'].dt.strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Renombrar columnas para mejor visualización
                    table_df.columns = [
                        'ID', 'Dispositivo', 'IP', 'Luminosidad (lux)', 
                        'Amoniaco (ppm)', 'Sulfuro H (ppm)', 
                        'Humedad (%)', 'Temperatura (°C)', 'Timestamp'
                    ]
                    
                    st.dataframe(table_df, use_container_width=True)
                    
                    # Opción para descargar datos
                    csv = table_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "Descargar datos como CSV",
                        csv,
                        "datos_sensores.csv",
                        "text/csv",
                        key='download-csv'
                    )
            
            else:
                st.info(f"No hay suficientes datos para el rango de tiempo seleccionado ({hours} horas). Espera a que se recolecten más datos.")
        
        # Esperar el intervalo especificado antes de actualizar
        time.sleep(update_interval)
        st.rerun()

if __name__ == "__main__":
    main()