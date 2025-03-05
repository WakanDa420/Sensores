import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
import datetime
import time
import numpy as np
from plotly.subplots import make_subplots

# Configuración de la página con tema oscuro
st.set_page_config(
    page_title="Dashboard de Monitoreo de Sensores",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados con tema oscuro
st.markdown("""
<style>
    /* Tema oscuro general */
    .stApp {
        background-color: #121212;
        color: #E0E0E0;
    }
    
    /* Estilo para la barra lateral */
    .css-1d391kg, .css-1lcbmhc {
        background-color: #1E1E1E;
    }
    
    /* Encabezados */
    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF;
    }
    
    /* Tarjetas métricas */
    .metric-card {
        background-color: #1E1E1E;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        margin-bottom: 1rem;
        border-left: 4px solid #3366FF;
    }
    
    .metric-title {
        font-size: 0.9rem;
        font-weight: 600;
        color: #AAAAAA;
        margin-bottom: 8px;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 8px;
    }
    
    /* Estados */
    .status-good {
        color: #4CAF50;
        font-weight: 600;
    }
    
    .status-warning {
        color: #FFC107;
        font-weight: 600;
    }
    
    .status-alert {
        color: #F44336;
        font-weight: 600;
    }
    
    /* Última actualización */
    .last-update {
        font-size: 0.8rem;
        color: #AAAAAA;
        text-align: right;
    }
    
    /* Contenedor principal */
    .main-container {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
    }
    
    /* Encabezado principal */
    .main-header {
        font-size: 1.8rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 1rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #333333;
    }
    
    /* Pestañas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #333333;
        border-radius: 4px;
        padding: 8px 16px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #3366FF;
    }
    
    /* Botones */
    .stButton>button {
        background-color: #3366FF;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
    }
    
    /* Selectores y sliders */
    .stSelectbox>div>div, .stSlider>div>div {
        background-color: #333333;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Función para crear gráficos circulares tipo gauge
def create_gauge_chart(value, title, color_ranges, max_value=100):
    """
    Crea un gráfico circular tipo gauge (medidor)
    
    Args:
        value: Valor a mostrar (número)
        title: Título del gráfico
        color_ranges: Lista de tuplas (valor_min, valor_max, color)
        max_value: Valor máximo del medidor
    """
    # Determinar el color basado en el valor
    gauge_color = color_ranges[-1][2]  # Color por defecto (último en la lista)
    for min_val, max_val, color in color_ranges:
        if min_val <= value <= max_val:
            gauge_color = color
            break
    
    # Crear el gráfico
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'color': TEXT_COLOR, 'size': 16}},
        gauge={
            'axis': {'range': [None, max_value], 'tickwidth': 1, 'tickcolor': TEXT_COLOR},
            'bar': {'color': gauge_color},
            'bgcolor': 'rgba(50, 50, 50, 0.8)',
            'borderwidth': 2,
            'bordercolor': GRID_COLOR,
            'steps': [
                {'range': [min_val, max_val], 'color': 'rgba(50, 50, 50, 0.3)'} 
                for min_val, max_val, _ in color_ranges
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        },
        number={'font': {'color': TEXT_COLOR, 'size': 40}}
    ))
    
    # Aplicar tema oscuro
    fig.update_layout(
        paper_bgcolor=BACKGROUND_COLOR,
        plot_bgcolor=BACKGROUND_COLOR,
        height=250,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig

# Función para crear gráfico donut
def create_donut_chart(value, title, color, max_value=100):
    """
    Crea un gráfico circular tipo donut para mostrar un porcentaje
    
    Args:
        value: Valor a mostrar (porcentaje)
        title: Título del gráfico
        color: Color del segmento lleno
        max_value: Valor máximo (100 para porcentajes)
    """
    remaining = max_value - value
    
    fig = go.Figure(go.Pie(
        values=[value, remaining],
        hole=0.7,
        marker_colors=[color, GRID_COLOR],
        textinfo='none',
        hoverinfo='none',
        showlegend=False
    ))
    
    # Añadir texto en el centro
    fig.add_annotation(
        text=f"{value}%",
        font=dict(size=30, color=TEXT_COLOR),
        showarrow=False,
        x=0.5, y=0.5
    )
    
    # Añadir título
    fig.add_annotation(
        text=title,
        font=dict(size=14, color=TEXT_COLOR),
        showarrow=False,
        x=0.5, y=0.85
    )
    
    # Aplicar tema oscuro
    fig.update_layout(
        paper_bgcolor=BACKGROUND_COLOR,
        plot_bgcolor=BACKGROUND_COLOR,
        height=250,
        margin=dict(l=10, r=10, t=10, b=10)
    )
    
    return fig

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

# Función para crear una tarjeta de métricas con estilo mejorado
def metric_card(title, value, unit, status, status_class):
    return f"""
    <div class="metric-card">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value} {unit}</div>
        <div class="{status_class}">Estado: {status}</div>
    </div>
    """

# Configuración de colores para gráficos
CHART_COLORS = ['#3366FF', '#FF4081', '#00E676', '#FFEA00', '#FF9100']
BACKGROUND_COLOR = '#1E1E1E'
GRID_COLOR = '#333333'
TEXT_COLOR = '#FFFFFF'

# Función para configurar el estilo de los gráficos de Plotly
def configure_plotly_theme(fig):
    fig.update_layout(
        plot_bgcolor=BACKGROUND_COLOR,
        paper_bgcolor=BACKGROUND_COLOR,
        font=dict(color=TEXT_COLOR),
        title_font=dict(color=TEXT_COLOR, size=18),
        legend=dict(
            font=dict(color=TEXT_COLOR),
            bgcolor='rgba(0,0,0,0)',
            bordercolor='rgba(0,0,0,0)'
        ),
        xaxis=dict(
            gridcolor=GRID_COLOR,
            zerolinecolor=GRID_COLOR,
            tickfont=dict(color=TEXT_COLOR)
        ),
        yaxis=dict(
            gridcolor=GRID_COLOR,
            zerolinecolor=GRID_COLOR,
            tickfont=dict(color=TEXT_COLOR)
        ),
        margin=dict(l=20, r=20, t=40, b=20),
        hovermode="x unified"
    )
    return fig

# Barra lateral con estilo mejorado
st.sidebar.markdown('<h2 style="color: #FFFFFF;">Configuración</h2>', unsafe_allow_html=True)

# Añadir logo o imagen en la barra lateral (opcional)
st.sidebar.markdown('<div style="text-align: center; margin-bottom: 20px;"><h1 style="color: #3366FF;">📊</h1></div>', unsafe_allow_html=True)

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

# Encabezado principal con estilo mejorado
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
            # Contenedor principal con estilo mejorado
            st.markdown('<div class="main-container">', unsafe_allow_html=True)
            
            col_info1, col_info2 = st.columns([3, 1])
            with col_info1:
                st.markdown('<h3 style="color: #FFFFFF; margin-bottom: 15px;">Estado actual de los sensores</h3>', unsafe_allow_html=True)
            with col_info2:
                st.markdown(f'<div class="last-update">Última actualización: {st.session_state.last_update_time.strftime("%H:%M:%S")} | Actualizaciones: {st.session_state.update_counter}</div>', unsafe_allow_html=True)

            # Filtrar dispositivos seleccionados
            filtered_latest = latest_data[latest_data['device'].isin(selected_devices)]
            
            # Crear una fila de KPIs con valores destacados
            kpi_cols = st.columns(len(filtered_latest))
            
            for i, (_, device_data) in enumerate(filtered_latest.iterrows()):
                with kpi_cols[i]:
                    # Crear un KPI destacado para temperatura
                    temp_value = device_data['t']
                    temp_status, temp_class = evaluate_status(temp_value, 't')
                    
                    st.markdown(f"""
                    <div style="background-color: #252525; border-radius: 10px; padding: 15px; text-align: center; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);">
                        <div style="font-size: 1rem; color: #AAAAAA;">{device_data['device']}</div>
                        <div style="font-size: 2.5rem; font-weight: 700; color: #FFFFFF; margin: 10px 0;">{round(temp_value, 1)} °C</div>
                        <div class="{temp_class}">Temperatura: {temp_status}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Mostrar tarjetas de estado para cada dispositivo
            st.markdown("<br>", unsafe_allow_html=True)
            
            for _, device_data in filtered_latest.iterrows():
                st.markdown(f"""
                <div style="background-color: #252525; border-radius: 10px; padding: 15px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);">
                    <h4 style="color: #FFFFFF; margin-bottom: 10px;">{device_data['device']} <span style="color: #AAAAAA; font-size: 0.8rem;">IP: {device_data['ip']} | Última lectura: {device_data['time'].strftime('%Y-%m-%d %H:%M:%S')}</span></h4>
                    <div style="display: flex; flex-wrap: wrap; gap: 15px;">
                """, unsafe_allow_html=True)
                
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
                    
                    st.markdown(f"""
                    <div style="flex: 1; min-width: 150px;">
                        {metric_card(titles[sensor_type], round(value, 1), unit, status, status_class)}
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("</div></div>", unsafe_allow_html=True)
            
            # Añadir gráficos circulares para métricas clave
            st.markdown("<br><h3 style='color: #FFFFFF; margin: 15px 0;'>Métricas de Estado</h3>", unsafe_allow_html=True)
            
            # Crear una fila para los gráficos circulares
            gauge_cols = st.columns(len(filtered_latest) * 2)
            
            col_index = 0
            for _, device_data in filtered_latest.iterrows():
                # Calcular porcentajes para los gráficos
                # Por ejemplo, para humedad y temperatura normalizadas
                humidity = device_data['h']
                temp = device_data['t']
                
                # Normalizar temperatura entre 0-100% (asumiendo rango de 10-40°C)
                temp_percent = min(100, max(0, (temp - 10) / 30 * 100))
                
                # Crear gráfico donut para humedad
                with gauge_cols[col_index]:
                    # Definir rangos de colores para humedad
                    humidity_ranges = [
                        (0, 30, '#3366FF'),   # Azul para humedad baja
                        (30, 60, '#00E676'),  # Verde para humedad normal-baja
                        (60, 80, '#00E676'),  # Verde para humedad normal
                        (80, 100, '#FF9100')  # Naranja para humedad alta
                    ]
                    
                    humidity_fig = create_gauge_chart(
                        humidity, 
                        f"Humedad - {device_data['device']}", 
                        humidity_ranges
                    )
                    st.plotly_chart(humidity_fig, use_container_width=True)
                
                # Crear gráfico donut para temperatura
                with gauge_cols[col_index + 1]:
                    # Definir rangos de colores para temperatura
                    temp_ranges = [
                        (0, 20, '#3366FF'),    # Azul para temperatura baja
                        (20, 25, '#00E676'),   # Verde para temperatura normal
                        (25, 30, '#FF9100'),   # Naranja para temperatura moderada
                        (30, 100, '#F44336')   # Rojo para temperatura alta
                    ]
                    
                    temp_fig = create_gauge_chart(
                        temp, 
                        f"Temperatura - {device_data['device']}", 
                        temp_ranges, 
                        max_value=40
                    )
                    st.plotly_chart(temp_fig, use_container_width=True)
                
                col_index += 2
            
            # Añadir gráficos donut para estados generales
            st.markdown("<br><h3 style='color: #FFFFFF; margin: 15px 0;'>Estados del Sistema</h3>", unsafe_allow_html=True)
            
            donut_cols = st.columns(4)
            
            # Calcular algunos valores de ejemplo para los gráficos donut
            # En un caso real, estos valores vendrían de tus datos
            
            # Ejemplo: Porcentaje de sensores en estado normal
            with donut_cols[0]:
                # Contar cuántos sensores están en estado normal
                normal_count = 0
                total_sensors = 0
                
                for _, device_data in filtered_latest.iterrows():
                    for sensor_type in ['lux', 'nh3', 'hs', 'h', 't']:
                        total_sensors += 1
                        status, _ = evaluate_status(device_data[sensor_type], sensor_type)
                        if status == "Normal":
                            normal_count += 1
                
                normal_percent = int(normal_count / total_sensors * 100) if total_sensors > 0 else 0
                
                normal_fig = create_donut_chart(
                    normal_percent,
                    "Sensores Normales",
                    "#4CAF50"  # Verde
                )
                st.plotly_chart(normal_fig, use_container_width=True)
            
            # Ejemplo: Porcentaje de sensores en estado de advertencia
            with donut_cols[1]:
                warning_count = 0
                
                for _, device_data in filtered_latest.iterrows():
                    for sensor_type in ['lux', 'nh3', 'hs', 'h', 't']:
                        status, _ = evaluate_status(device_data[sensor_type], sensor_type)
                        if status in ["Alta", "Baja", "Moderada"]:
                            warning_count += 1
                
                warning_percent = int(warning_count / total_sensors * 100) if total_sensors > 0 else 0
                
                warning_fig = create_donut_chart(
                    warning_percent,
                    "Sensores en Advertencia",
                    "#FFC107"  # Amarillo
                )
                st.plotly_chart(warning_fig, use_container_width=True)
            
            # Ejemplo: Porcentaje de sensores en estado de alerta
            with donut_cols[2]:
                alert_count = 0
                
                for _, device_data in filtered_latest.iterrows():
                    for sensor_type in ['lux', 'nh3', 'hs', 'h', 't']:
                        status, _ = evaluate_status(device_data[sensor_type], sensor_type)
                        if status == "Alta" and sensor_type in ['nh3', 'hs', 't']:
                            alert_count += 1
                
                alert_percent = int(alert_count / total_sensors * 100) if total_sensors > 0 else 0
                
                alert_fig = create_donut_chart(
                    alert_percent,
                    "Sensores en Alerta",
                    "#F44336"  # Rojo
                )
                st.plotly_chart(alert_fig, use_container_width=True)
            
            # Ejemplo: Disponibilidad del sistema
            with donut_cols[3]:
                # Simular disponibilidad del sistema (en un caso real, esto vendría de tus datos)
                system_uptime = 98
                
                uptime_fig = create_donut_chart(
                    system_uptime,
                    "Disponibilidad",
                    "#3366FF"  # Azul
                )
                st.plotly_chart(uptime_fig, use_container_width=True)
            
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
                    st.markdown(f'<h3 style="color: #FFFFFF; margin: 15px 0;">Tendencias de las últimas {hours} horas</h3>', unsafe_allow_html=True)
                    
                    # Crear gráficos de línea para cada tipo de sensor y cada dispositivo
                    # Aquí es donde hacemos el cambio principal para separar los gráficos por dispositivo
                    for sensor_type, title, unit in [
                        ('t', 'Temperatura', '°C'),
                        ('h', 'Humedad', '%'),
                        ('lux', 'Luminosidad', 'lux'),
                        ('nh3', 'Amoniaco', 'ppm'),
                        ('hs', 'Sulfuro de Hidrógeno', 'ppm')
                    ]:
                        st.markdown(f'<h4 style="color: #FFFFFF; margin: 15px 0;">{title} ({unit})</h4>', unsafe_allow_html=True)
                        
                        # Crear una fila de columnas para cada dispositivo
                        device_cols = st.columns(len(selected_devices))
                        
                        for i, device in enumerate(selected_devices):
                            if device in df['device'].values:
                                with device_cols[i]:
                                    # Filtrar datos solo para este dispositivo
                                    device_df = df[df['device'] == device]
                                    
                                    # Crear gráfico solo para este dispositivo
                                    fig = px.line(
                                        device_df, 
                                        x='time', 
                                        y=sensor_type,
                                        title=f"{device}",
                                        labels={'time': 'Tiempo', sensor_type: f'{title} ({unit})'},
                                        height=300,
                                        color_discrete_sequence=[CHART_COLORS[i % len(CHART_COLORS)]]
                                    )
                                    
                                    # Aplicar tema oscuro al gráfico
                                    fig = configure_plotly_theme(fig)
                                    
                                    # Añadir líneas de referencia si es necesario
                                    if sensor_type == 't':
                                        fig.add_shape(type="line", x0=device_df['time'].min(), x1=device_df['time'].max(), y0=30, y1=30,
                                                    line=dict(color="#F44336", width=2, dash="dash"))
                                        fig.add_shape(type="line", x0=device_df['time'].min(), x1=device_df['time'].max(), y0=20, y1=20,
                                                    line=dict(color="#FFC107", width=2, dash="dash"))
                                    
                                    # Ocultar leyenda ya que solo hay una línea
                                    fig.update_layout(showlegend=False)
                                    
                                    st.plotly_chart(fig, use_container_width=True)
                
                with tab2:
                    st.markdown('<h3 style="color: #FFFFFF; margin: 15px 0;">Comparación entre sensores</h3>', unsafe_allow_html=True)
                    
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
                    
                    # Crear gráfico de comparación de barras con estilo mejorado
                    latest_compare = latest_data[latest_data['device'].isin(selected_devices)]
                    if not latest_compare.empty:
                        # Crear layout de dos columnas para los gráficos
                 
                        # Crear layout de dos columnas para los gráficos
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            fig = px.bar(
                                latest_compare, 
                                x='device', 
                                y=compare_var[0],
                                title=f"Comparación de {compare_var[1]} entre dispositivos",
                                labels={'device': 'Dispositivo', compare_var[0]: compare_var[1]},
                                color='device',
                                height=400,
                                color_discrete_sequence=CHART_COLORS
                            )
                            
                            # Aplicar tema oscuro al gráfico
                            fig = configure_plotly_theme(fig)
                            fig.update_layout(showlegend=False)
                            
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Gráfico radar para comparar todos los sensores a la vez
                        with col2:
                            if len(latest_compare) > 1:
                                # Normalizar los datos para el gráfico radar
                                radar_vars = ['lux', 'nh3', 'hs', 'h', 't']
                                radar_titles = ['Luminosidad', 'Amoniaco', 'Sulfuro H', 'Humedad', 'Temperatura']
                                
                                # Crear figura con subplots
                                fig = make_subplots(rows=1, cols=1, specs=[[{'type': 'polar'}]])
                                
                                # Normalizar valores para el radar
                                max_vals = {var: df[var].max() for var in radar_vars}
                                min_vals = {var: df[var].min() for var in radar_vars}
                                
                                for i, (_, device_row) in enumerate(latest_compare.iterrows()):
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
                                        name=device_row['device'],
                                        line_color=CHART_COLORS[i % len(CHART_COLORS)]
                                    ))
                                
                                fig.update_layout(
                                    polar=dict(
                                        radialaxis=dict(
                                            visible=True,
                                            range=[0, 1],
                                            color=TEXT_COLOR
                                        ),
                                        angularaxis=dict(
                                            color=TEXT_COLOR
                                        ),
                                        bgcolor=BACKGROUND_COLOR
                                    ),
                                    showlegend=True,
                                    legend=dict(
                                        font=dict(color=TEXT_COLOR),
                                        bgcolor='rgba(0,0,0,0)'
                                    ),
                                    paper_bgcolor=BACKGROUND_COLOR,
                                    plot_bgcolor=BACKGROUND_COLOR,
                                    height=400,
                                    title={
                                        'text': "Perfil comparativo de sensores (normalizado)",
                                        'font': {'color': TEXT_COLOR}
                                    }
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                    
                    # Añadir un mapa de calor para visualizar correlaciones
                    st.markdown('<h4 style="color: #FFFFFF; margin: 15px 0;">Mapa de calor de valores actuales</h4>', unsafe_allow_html=True)
                    
                    if not latest_compare.empty and len(latest_compare) > 1:
                        # Preparar datos para el mapa de calor
                        heatmap_data = latest_compare.set_index('device')[['lux', 'nh3', 'hs', 'h', 't']]
                        
                        # Renombrar columnas para mejor visualización
                        heatmap_data.columns = ['Luminosidad', 'Amoniaco', 'Sulfuro H', 'Humedad', 'Temperatura']
                        
                        # Crear mapa de calor
                        fig = px.imshow(
                            heatmap_data,
                            labels=dict(x="Sensor", y="Dispositivo", color="Valor"),
                            x=heatmap_data.columns,
                            y=heatmap_data.index,
                            color_continuous_scale='Viridis',
                            height=300
                        )
                        
                        # Aplicar tema oscuro al gráfico
                        fig = configure_plotly_theme(fig)
                        fig.update_layout(coloraxis_colorbar=dict(title="Valor", titleside="right"))
                        
                        st.plotly_chart(fig, use_container_width=True)
                
                with tab3:
                    st.markdown('<h3 style="color: #FFFFFF; margin: 15px 0;">Datos en tabla</h3>', unsafe_allow_html=True)
                    
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
                    
                    # Aplicar estilo a la tabla
                    st.dataframe(
                        table_df,
                        use_container_width=True,
                        hide_index=True
                    )
                    
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
            
            # Cerrar el contenedor principal
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Esperar el intervalo especificado antes de actualizar
        time.sleep(update_interval)
        st.rerun()

if __name__ == "__main__":
    main()