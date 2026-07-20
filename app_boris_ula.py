import streamlit as st
import folium
import requests #requests de Python, nos permite hacer consultas a internet.
from streamlit_folium import st_folium
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

# 1. Configuración de la página (debe ser el primer comando de Streamlit)
st.set_page_config(page_title="Dimensionamiento FV - Proyecto de Titulo por Boris Nahuelhueique", layout="centered")

# 2. Título y descripción
st.title("☀️ Calculadora Solar ULagos")
st.markdown("""
Bienvenido/a. Esta herramienta te guiará paso a paso para dimensionar tu sistema solar fotovoltaico. 
Para comenzar, necesitamos conocer la ubicación exacta de tu proyecto.
""")

# ─────────────────────────────────────────────────────────────
# MARCO NORMATIVO APLICADO EN ESTA HERRAMIENTA
# ─────────────────────────────────────────────────────────────
with st.expander("📜 Marco Normativo Aplicado en esta Herramienta"):
    st.markdown("""
    Esta aplicación no fija sus parámetros de forma arbitraria: varios de los valores que verás
    a lo largo del dimensionamiento están definidos —o acotados— por la normativa eléctrica
    chilena vigente, administrada por la Superintendencia de Electricidad y Combustibles (SEC).
    A continuación se resumen los instrumentos normativos que la aplicación utiliza como base
    de sus cálculos:

    | Instrumento | ¿Qué establece? | ¿Dónde se aplica en la app? |
    |---|---|---|
    | **Ley N° 21.118** (Net Billing) | Marco legal de generación distribuida para autoconsumo residencial. | Habilita el modo **On-Grid** y el concepto de "prosumidor". |
    | **D.S. N° 57/2020** | Límites de potencia y condiciones de conexión para autoconsumo. | Justifica el alcance de la app a instalaciones de hasta **10 kW**. |
    | **RGR N° 02/2024** (SEC) | Exige certificación **IEC 61215 / IEC 61730** en los módulos fotovoltaicos. | Todos los paneles de la lista desplegable cumplen esta exigencia. |
    | **RGR N° 06/2024** (SEC), Anexo D | Profundidad de descarga (DoD) máxima por tecnología de batería: **90 % ion-litio**, **80 % plomo-ácido**. | Determina automáticamente el DoD usado en el cálculo de la capacidad del banco de baterías (sistemas Off-Grid). |
    | **ITG N° 9.1/2021** (SEC) | Requisitos técnicos para sistemas fotovoltaicos aislados de la red. | Rige el modo **Off-Grid** de la aplicación. |

    📌 *Nota:* la eficiencia global del sistema (η = 80 % On-Grid / 75 % Off-Grid) **no** proviene
    de estos instrumentos, sino de literatura técnica de referencia (Masters, *Renewable and
    Efficient Electric Power Systems*) para sistemas residenciales. Esta distinción se mantiene
    en cada paso de la herramienta para no atribuir a la normativa valores que no establece.
    """)

# 3. Variables de estado (Session State)
# Esto guarda la información para que no se borre cuando cambiemos de pestaña o página
if 'latitud' not in st.session_state:
    st.session_state['latitud'] = -41.4693 # Por defecto: Puerto Montt
if 'longitud' not in st.session_state:
    st.session_state['longitud'] = -72.9423

# 4. Organización por pestañas para las dos opciones que pediste
tab_mapa, tab_manual = st.tabs(["🗺️ Seleccionar en el Mapa", "✍️ Ingreso Manual"])

# --- OPCIÓN 1: MAPA INTERACTIVO ---
with tab_mapa:
    st.write("Haz clic en tu ubicación exacta sobre el mapa. Usa el ratón para acercar o alejar.")
    
    # Crear el mapa base
    m = folium.Map(location=[st.session_state['latitud'], st.session_state['longitud']], zoom_start=11)
    
    # Agregar la herramienta para capturar clics
    m.add_child(folium.LatLngPopup())
    
    # Mostrar el mapa en Streamlit y capturar los datos
    map_data = st_folium(m, height=400, width=700)
    
    # Si el usuario hace clic en un punto nuevo, actualizamos las variables
    if map_data['last_clicked']:
        st.session_state['latitud'] = map_data['last_clicked']['lat']
        st.session_state['longitud'] = map_data['last_clicked']['lng']
        st.success("¡Ubicación capturada correctamente del mapa!")

# --- OPCIÓN 2: INGRESO MANUAL ---
with tab_manual:
    st.write("Si conoces tus coordenadas exactas, puedes ingresarlas aquí:")
    col1, col2 = st.columns(2)
    
    with col1:
        # El valor por defecto será lo que esté guardado en el estado
        nueva_lat = st.number_input("Latitud", value=st.session_state['latitud'], format="%.4f")
    with col2:
        nueva_lon = st.number_input("Longitud", value=st.session_state['longitud'], format="%.4f")
        
    # Actualizar estado si el usuario escribe manualmente
    st.session_state['latitud'] = nueva_lat
    st.session_state['longitud'] = nueva_lon

# 5. Resumen visible para el usuario
st.divider()
st.info(f"**📍 Coordenadas actuales del proyecto:** Latitud: `{st.session_state['latitud']:.4f}` | Longitud: `{st.session_state['longitud']:.4f}`")

# --- 6. CÁLCULO AUTOMÁTICO DE INCLINACIÓN Y AZIMUT ---
st.divider() # Línea separadora
st.header("📐 Orientación e Inclinación del Sistema")

# Cálculo de valores óptimos
# La inclinación es el valor absoluto de la latitud
inclinacion_optima = abs(st.session_state['latitud'])

# Determinar el hemisferio y azimut
if st.session_state['latitud'] < 0:
    # Hemisferio Sur -> Mirar al Norte
    azimut_optimo = 0.0
    orientacion_texto = "Norte"
else:
    # Hemisferio Norte -> Mirar al Sur
    azimut_optimo = 180.0
    orientacion_texto = "Sur"

st.markdown("""
Basado en tu ubicación, el sistema ha calculado la orientación e inclinación ideales para **maximizar la generación de energía anual**. 
Si tu techo tiene una disposición diferente y no usarás estructuras ajustables, puedes modificar estos valores manuales.
""")

# Crear dos columnas para los inputs
col3, col4 = st.columns(2)

with col3:
    # Usamos st.number_input permitiendo al usuario cambiar el valor si lo desea
    inclinacion_usuario = st.number_input(
        "Inclinación de los paneles (°)", 
        value=float(round(inclinacion_optima, 1)), # Redondeamos a 1 decimal
        min_value=0.0, 
        max_value=90.0, 
        step=1.0,
        help="Ángulo de inclinación del panel respecto al suelo. El valor óptimo anual equivale a tu latitud."
    )
    
with col4:
    azimut_usuario = st.number_input(
        "Azimut (°)", 
        value=float(azimut_optimo), 
        min_value=0.0, 
        max_value=359.0, 
        step=1.0,
        help="Orientación respecto al Norte geográfico. 0° = Norte, 90° = Este, 180° = Sur, 270° = Oeste."
    )

# Guardamos estos datos en el Session State para usarlos en futuros cálculos de la app
st.session_state['inclinacion'] = inclinacion_usuario
st.session_state['azimut'] = azimut_usuario

# --- 7. EXPLICACIÓN DIDÁCTICA (TOOLTIP / EXPANDER) ---
# Esto cumple el objetivo didáctico de tu tesis
with st.expander("💡 ¿Por qué el sistema sugiere estos valores?"):
    st.write(f"""
    * **Inclinación sugerida ({round(inclinacion_optima, 1)}°):** Para maximizar la captación de energía durante todo el año, la regla de ingeniería solar establece que la inclinación de los módulos debe ser lo más cercana posible a la latitud geográfica del lugar de instalación.
    * **Azimut sugerido ({azimut_optimo}° - {orientacion_texto}):** Como la ubicación ingresada se encuentra en el hemisferio {'sur' if st.session_state['latitud'] < 0 else 'norte'}, los paneles deben apuntar hacia el {orientacion_texto} geográfico. Esto asegura que los paneles reciban la mayor cantidad de radiación solar directa durante el recorrido del sol a lo largo del día.
    """)

# --- 8. CONSUMO ELÉCTRICO ---
st.divider()
st.header("⚡ Consumo Eléctrico")
st.markdown("""
Para dimensionar tu sistema fotovoltaico (paneles e inversores), necesitamos estimar cuánta energía consumes. 
Puedes ingresar un promedio si ya lo conoces, o detallar tu consumo mes a mes viendo tus últimas boletas de electricidad.
""")

# Inicializamos la variable de consumo en el Session State si no existe
# Asumimos 250 kWh/mes como un valor promedio típico residencial en Chile
if 'consumo_mensual_promedio' not in st.session_state:
    st.session_state['consumo_mensual_promedio'] = 250.0

# Botones de selección para la modalidad de ingreso
opcion_consumo = st.radio(
    "¿Cómo prefieres ingresar tus datos de consumo?",
    ("Ingreso Rápido (Promedio Mensual)", "Ingreso Detallado (Mes a Mes)")
)

if opcion_consumo == "Ingreso Rápido (Promedio Mensual)":
    # --- OPCIÓN A: PROMEDIO DIRECTO ---
    st.write("Ingresa el consumo promedio mensual de tu vivienda:")
    consumo_rapido = st.number_input(
        "Consumo (kWh/mes)",
        value=float(st.session_state['consumo_mensual_promedio']),
        min_value=1.0,
        step=10.0,
        help="Suele aparecer en tu boleta de luz como 'Consumo del mes' o 'Promedio'."
    )
    # Actualizamos la memoria (y limpiamos lista detallada si existía)
    st.session_state['consumo_mensual_promedio'] = consumo_rapido
    st.session_state['consumos_mensuales_reales'] = None

else:
    # --- OPCIÓN B: MES A MES ---
    st.write("Ingresa el consumo en kWh para cada mes (puedes aproximar):")
    
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    consumos_meses = []
    
    # Creamos una cuadrícula de 3 columnas para que sea visualmente agradable
    cols = st.columns(3)
    
    for i, mes in enumerate(meses):
        with cols[i % 3]: # Esto distribuye los meses equitativamente en las 3 columnas
            val = st.number_input(
                mes, 
                value=250.0, 
                min_value=0.0, 
                step=10.0, 
                key=f"mes_{i}" # El key es importante para que Streamlit no confunda las cajas de texto
            )
            consumos_meses.append(val)
            
    # Calculamos la suma total y el promedio
    consumo_anual_total = sum(consumos_meses)
    promedio_calculado = consumo_anual_total / 12
    
    # Actualizamos la memoria con el promedio calculado y la lista mes a mes
    st.session_state['consumo_mensual_promedio'] = promedio_calculado
    st.session_state['consumos_mensuales_reales'] = [round(c, 1) for c in consumos_meses]
    
    # Le mostramos al usuario el resultado de su ingreso
    st.success(f"📊 **Resumen de tu ingreso:**")
    st.write(f"- Consumo Total Anual: **{round(consumo_anual_total, 1)} kWh/año**")
    st.write(f"- Consumo Promedio Mensual: **{round(promedio_calculado, 1)} kWh/mes**")

# --- EXPLICACIÓN DIDÁCTICA ---
with st.expander("💡 ¿Por qué es fundamental este dato?"):
    st.write("""
    El dimensionamiento de un sistema fotovoltaico se basa en un balance energético. 
    * Si el sistema está **conectado a la red (On-Grid)** bajo la Ley de Netbilling, el objetivo es cubrir este consumo promedio para reducir la cuenta de luz a cero (pagando solo los cargos fijos).
    * Si el sistema es **aislado (Off-Grid)** o con baterías, subestimar este valor significaría quedarte sin energía durante los días nublados o por las noches.
    """)

# --- 9. DATOS CLIMÁTICOS Y ANÁLISIS MENSUAL (NASA POWER) ---
st.divider()
st.header("🌤️ Recurso Solar (Horas de Sol Pico)")
st.markdown("""
Para asegurar un diseño preciso, consultamos la base de datos satelital de la **NASA** utilizando un registro histórico de **40 años (1984 - 2024)**. 
Este periodo extenso permite obtener promedios estadísticamente robustos y confiables para el dimensionamiento fotovoltaico.
""")

if st.button("🛰️ Obtener y analizar datos de radiación"):
    with st.spinner('Procesando 40 años de datos meteorológicos...'):
        try:
            lat = st.session_state['latitud']
            lon = st.session_state['longitud']
            
            # 1. URL: Periodo 1984 - 2024
            url = f"https://power.larc.nasa.gov/api/temporal/monthly/point?parameters=ALLSKY_SFC_SW_DWN&community=RE&longitude={lon}&latitude={lat}&format=JSON&start=1984&end=2024"
            
            respuesta = requests.get(url)
            datos_nasa = respuesta.json()
            radiacion_historica = datos_nasa['properties']['parameter']['ALLSKY_SFC_SW_DWN']
            
            # 2. PROCESAMIENTO Y ORDENAMIENTO CRONOLÓGICO
            df_crudo = pd.DataFrame(list(radiacion_historica.items()), columns=['Fecha', 'HSP'])
            df_crudo = df_crudo[~df_crudo['Fecha'].str.endswith('13')] # Quitar promedios anuales
            df_crudo = df_crudo[df_crudo['HSP'] != -999.0]            # Quitar errores
            
            # Ordenamos por número de mes (1 al 12)
            df_crudo['Mes_Num'] = df_crudo['Fecha'].str[-2:].astype(int)
            promedios_mensuales = df_crudo.groupby('Mes_Num')['HSP'].mean().sort_index()
            
            st.session_state['hsp'] = promedios_mensuales.mean()
            
            # 3. PREPARACIÓN DE DATOS PARA LA INTERFAZ
            meses_nombres = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
            df_radiacion = pd.DataFrame({
                'Mes': meses_nombres,
                'HSP (kWh/m²/día)': promedios_mensuales.values
            })
            st.session_state['hsp_mensual'] = df_radiacion
            
            # 4. LÓGICA DE INTERPRETACIÓN (Detección de mejores/peor mes)
            df_ordenado = df_radiacion.sort_values(by='HSP (kWh/m²/día)', ascending=False)
            mejores_meses = df_ordenado['Mes'].head(3).tolist()
            peor_mes = df_ordenado['Mes'].iloc[-1]
            
            # --- INTERFAZ VISUAL (COMO EN TU FOTO) ---
            st.success(f"¡Análisis del periodo 1984-2024 completado con éxito!")
            
            col_a, col_b = st.columns([1, 2])
            
            with col_a:
                # Métrica igual a la foto
                st.metric("Promedio Anual", f"{round(st.session_state['hsp'], 2)} HSP")
                
                # Interpretación con el texto exacto de la foto
                st.info(f"""
                **💡 Interpretación de la App:**
                
                Tu sistema tendrá su máxima generación de energía durante los meses de **{mejores_meses[0]}, {mejores_meses[1]} y {mejores_meses[2]}**.
                
                Por el contrario, el dimensionamiento de tus baterías (si las usas) deberá soportar el mes más crítico, que es **{peor_mes}**.
                """)
            
            with col_b:
                fig_hsp = go.Figure(go.Bar(
                    x=df_radiacion['Mes'],
                    y=df_radiacion['HSP (kWh/m²/día)'],
                    marker_color='#FFC300',
                ))
                fig_hsp.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    yaxis_title='HSP (kWh/m²/día)',
                    margin=dict(t=10, b=10, l=10, r=10),
                    height=320,
                )
                st.plotly_chart(fig_hsp, use_container_width=True)
                
        except Exception as e:
            st.error(f"Hubo un problema al conectar con la NASA. Detalles: {e}")

# Mantener resultados visibles al cambiar de pestaña
elif 'hsp' in st.session_state:
    st.info(f"✅ Recurso Solar configurado: Promedio de **{round(st.session_state['hsp'], 2)} HSP**")
    with st.expander("Ver gráfico de radiación guardado"):
        _df_hsp_saved = st.session_state['hsp_mensual']
        fig_hsp2 = go.Figure(go.Bar(
            x=_df_hsp_saved['Mes'],
            y=_df_hsp_saved['HSP (kWh/m²/día)'],
            marker_color='#FFC300',
        ))
        fig_hsp2.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis_title='HSP (kWh/m²/día)',
            margin=dict(t=10, b=10, l=10, r=10),
            height=320,
        )
        st.plotly_chart(fig_hsp2, use_container_width=True)

# --- EXPLICACIÓN DIDÁCTICA ---
with st.expander("💡 ¿Qué es este parámetro y por qué usamos la NASA?"):
    st.write("""
    * **¿Qué son las HSP?** Las Horas de Sol Pico (HSP) representan la cantidad de energía solar que recibe un metro cuadrado de superficie en un día. Es el equivalente a tomar todas las horas de sol del día (con distintas intensidades) y comprimirlas en horas de sol "perfecto" a 1000 W/m².
    * **El parámetro de la NASA:** En la API utilizamos `ALLSKY_SFC_SW_DWN` (All Sky Surface Shortwave Downward Irradiance). En términos de ingeniería fotovoltaica, este valor se traduce directamente a las HSP diarias.
    * **Justificación de Diseño:** Obtener datos satelitales en tiempo real evita que el usuario tenga que buscar en tablas o mapas solares complejos, reduciendo el margen de error humano en el dimensionamiento.
    """)

# ─────────────────────────────────────────────────────────────
# MÓDULO 10: SELECCIÓN DEL TIPO DE SISTEMA
# ─────────────────────────────────────────────────────────────
st.divider()
st.header("⚙️ Tipo de Sistema")
st.markdown("Selecciona el tipo de instalación fotovoltaica que deseas dimensionar.")

tipo_sistema = st.radio(
    "Tipo de sistema:",
    ("On-Grid (Conectado a la red)", "Off-Grid (Aislado con baterías)")
)

# ─────────────────────────────────────────────────────────────
# MÓDULO 11: SELECCIÓN DEL PANEL FOTOVOLTAICO
# ─────────────────────────────────────────────────────────────
st.divider()
st.header("🔆 Selección del Panel Fotovoltaico")
st.markdown("""
Selecciona el panel solar que deseas instalar. Todos los modelos disponibles cuentan con
certificación **IEC 61215** e **IEC 61730**, exigida por la Instrucción Técnica RGR N°02/2024 de la SEC.
Los parámetros se cargarán automáticamente al seleccionar el modelo.
""")

# Base de datos de paneles (valores STC para dimensionamiento)
paneles_db = {
    "Raytech BPDMJ60H(S)-380": {
        "P_stc": 380, "Voc_stc": 41.82, "Isc_stc": 11.53,
        "Voc_nmot": 39.1, "Isc_nmot": 9.30,
        "eficiencia": 20.6, "area": 1.84, "tecnologia": "Mono P-type Bifacial"
    },
    "Sunpro SP540-144M10": {
        "P_stc": 540, "Voc_stc": 49.58, "Isc_stc": 13.84,
        "Voc_nmot": 49.8, "Isc_nmot": 11.05,
        "eficiencia": 20.89, "area": 2.58, "tecnologia": "Mono PERC Half-Cell"
    },
    "Canadian Solar CS6R-410MS": {
        "P_stc": 410, "Voc_stc": 37.2, "Isc_stc": 14.01,
        "Voc_nmot": 35.1, "Isc_nmot": 11.28,
        "eficiencia": 21.0, "area": 1.95, "tecnologia": "Mono PERC HiKu6"
    },
    "Jinko Solar JKM415M-54HL4": {
        "P_stc": 415, "Voc_stc": 37.31, "Isc_stc": 14.01,
        "Voc_nmot": 35.21, "Isc_nmot": 11.32,
        "eficiencia": 21.25, "area": 1.95, "tecnologia": "Mono P-type MBB HC"
    },
    "Longi Solar LR5-54HTH-415M": {
        "P_stc": 415, "Voc_stc": 38.53, "Isc_stc": 13.92,
        "Voc_nmot": 36.18, "Isc_nmot": 11.24,
        "eficiencia": 21.3, "area": 1.95, "tecnologia": "Mono Hi-MO6"
    },
    "Risen Energy RSM40-8-395M": {
        "P_stc": 395, "Voc_stc": 38.12, "Isc_stc": 10.76,
        "Voc_nmot": 35.07, "Isc_nmot": 10.98,
        "eficiencia": 20.4, "area": 1.92, "tecnologia": "Mono PERC Titan S"
    },
    "Trina Solar TSM-NE19R.70-610": {
        "P_stc": 610, "Voc_stc": 48.4, "Isc_stc": 15.80,
        "Voc_nmot": 46.0, "Isc_nmot": 12.73,
        "eficiencia": 22.2, "area": 2.70, "tecnologia": "N-type i-TOPCon"
    },
    "Astronergy CHSM54M(BL)-HC-400": {
        "P_stc": 400, "Voc_stc": 37.00, "Isc_stc": 13.65,
        "Voc_nmot": 34.97, "Isc_nmot": 11.07,
        "eficiencia": 20.5, "area": 1.95, "tecnologia": "Mono PERC+ HC Astro 5s"
    },
    "JA Solar JAM72S10-395/MR": {
        "P_stc": 395, "Voc_stc": 49.30, "Isc_stc": 10.28,
        "Voc_nmot": 45.90, "Isc_nmot": 8.15,
        "eficiencia": 19.7, "area": 2.00, "tecnologia": "Mono MBB Half-Cell"
    },
    "Seraphim SRP-600-BMB-HV": {
        "P_stc": 600, "Voc_stc": 41.69, "Isc_stc": 18.40,
        "Voc_nmot": 39.61, "Isc_nmot": 14.72,
        "eficiencia": 21.20, "area": 2.83, "tecnologia": "Mono PERC Seco 210mm"
    },
    "Canadian Solar CS3W-450MS": {
        "P_stc": 450, "Voc_stc": 49.1, "Isc_stc": 11.60,
        "Voc_nmot": 46.2, "Isc_nmot": 9.36,
        "eficiencia": 20.40, "area": 2.2, "tecnologia": "Mono PERC HiKu"
    },
}

# Lista desplegable — sin key para evitar conflicto con session_state
modelo_seleccionado = st.selectbox(
    "Selecciona el modelo de panel solar:",
    options=list(paneles_db.keys())
)

# Extraer parámetros del panel seleccionado y guardar en session_state
panel = paneles_db[modelo_seleccionado]
st.session_state['panel'] = panel

# Mostrar ficha técnica
st.info(f"""
**📋 Ficha Técnica – {modelo_seleccionado}**

| Parámetro | Valor STC | Valor NMOT |
|---|---|---|
| Potencia nominal | **{panel['P_stc']} W** | — |
| Tensión circuito abierto (Voc) | {panel['Voc_stc']} V | {panel['Voc_nmot']} V |
| Corriente cortocircuito (Isc) | {panel['Isc_stc']} A | {panel['Isc_nmot']} A |
| Eficiencia | {panel['eficiencia']} % | — |
| Área del módulo | {panel['area']} m² | — |
| Tecnología | {panel['tecnologia']} | — |
""")

with st.expander("💡 ¿Qué significan estos parámetros?"):
    st.write("""
    * **STC:** Condiciones estándar de laboratorio: 1.000 W/m², 25°C, AM 1.5. Valor de referencia para el dimensionamiento.
    * **NMOT:** Condiciones reales de operación al aire libre: 800 W/m², 20°C, viento 1 m/s.
    * **Voc:** Tensión máxima del panel sin carga conectada. Importante para el diseño del string.
    * **Isc:** Corriente máxima con bornes cortocircuitados. Determina el calibre de conductores y protecciones.
    """)

# ─────────────────────────────────────────────────────────────
# MÓDULO 12: SELECCIÓN DEL MES DE DISEÑO
# ─────────────────────────────────────────────────────────────
st.divider()
st.header("📅 Mes de Diseño")

if 'hsp_mensual' in st.session_state:
    df_hsp = st.session_state['hsp_mensual']

    st.markdown("""
    El mes de diseño define el nivel de irradiancia con el que se dimensionará el campo solar.
    Se recomienda usar el **mes crítico** (menor HSP) para garantizar que el sistema cubra el
    consumo incluso en las peores condiciones del año.
    """)

    # Índice del mes con menor HSP para sugerirlo por defecto
    idx_critico = int(df_hsp['HSP (kWh/m²/día)'].idxmin())

    mes_seleccionado = st.selectbox(
        "Selecciona el mes de diseño:",
        options=df_hsp['Mes'].tolist(),
        index=idx_critico
    )

    hsp_diseno = float(df_hsp[df_hsp['Mes'] == mes_seleccionado]['HSP (kWh/m²/día)'].values[0])
    st.session_state['hsp_diseno'] = hsp_diseno
    st.session_state['mes_diseno'] = mes_seleccionado

    st.success(f"📌 Mes seleccionado: **{mes_seleccionado}** → HSP = **{round(hsp_diseno, 2)} kWh/m²/día**")

    # ── Porcentaje de cobertura deseado ──────────────────────────
    st.markdown("---")
    st.markdown("##### ⚙️ Proporción de cobertura deseada")
    st.markdown(f"""
    Define qué porcentaje del consumo de **{mes_seleccionado}** quieres cubrir con el sistema fotovoltaico.
    Un 100% significa que el sistema generará suficiente energía para cubrir completamente el consumo
    de ese mes. Reducir este valor resulta en un sistema más pequeño, con menor inversión inicial,
    pero que no cubrirá la totalidad del consumo.
    """)

    cobertura_deseada = st.slider(
        "Porcentaje de cobertura del mes de diseño:",
        min_value=10,
        max_value=100,
        value=st.session_state.get('cobertura_deseada', 100),
        step=5,
        format="%d%%"
    )
    st.session_state['cobertura_deseada'] = cobertura_deseada

    if cobertura_deseada == 100:
        st.info(f"✅ El sistema cubrirá el **100%** del consumo de {mes_seleccionado}. Diseño conservador recomendado.")
    elif cobertura_deseada >= 70:
        st.info(f"⚡ El sistema cubrirá el **{cobertura_deseada}%** del consumo de {mes_seleccionado}. El resto será tomado de la red.")
    else:
        st.warning(f"⚠️ El sistema cubrirá solo el **{cobertura_deseada}%** del consumo de {mes_seleccionado}. Considera si esto es suficiente para tus objetivos.")

else:
    st.warning("⚠️ Primero debes obtener los datos de radiación solar en la sección anterior.")

# ─────────────────────────────────────────────────────────────
# MÓDULO 13: PARÁMETROS OFF-GRID (solo si aplica)
# ─────────────────────────────────────────────────────────────
if tipo_sistema == "Off-Grid (Aislado con baterías)":
    st.divider()
    st.header("🔋 Parámetros del Sistema de Almacenamiento")
    st.markdown("Define la tecnología de baterías y los días de autonomía requeridos.")

    col_bat1, col_bat2 = st.columns(2)

    with col_bat1:
        tecnologia_bat = st.selectbox(
            "Tecnología de batería:",
            ("Ion-Litio (LiFePO₄)", "Plomo-Ácido")
        )

    with col_bat2:
        dias_autonomia = st.number_input(
            "Días de autonomía:",
            min_value=1, max_value=5, value=2, step=1,
            help="Número de días que el sistema debe operar sin generación solar."
        )

    # DoD según tecnología (RGR N°06/2024, Anexo D)
    dod = 0.90 if tecnologia_bat == "Ion-Litio (LiFePO₄)" else 0.80
    v_bat = 48  # V

    # Guardar en session_state
    st.session_state['tecnologia_bat'] = tecnologia_bat
    st.session_state['dias_autonomia'] = dias_autonomia
    st.session_state['dod'] = dod
    st.session_state['v_bat'] = v_bat

    with st.expander("💡 ¿Qué es la profundidad de descarga (DoD)?"):
        st.write(f"""
        La **profundidad de descarga (DoD)** define el porcentaje máximo de la capacidad nominal
        de la batería que puede utilizarse en cada ciclo.

        * **Ion-Litio (LiFePO₄):** DoD = 90%
        * **Plomo-Ácido:** DoD = 80% → Descargar más reduce significativamente la vida útil.

        Para la tecnología seleccionada (**{tecnologia_bat}**), se aplica un DoD de **{int(dod*100)}%**.

        📜 *Valores máximos según el Anexo D de la Instrucción Técnica RGR N°06/2024 de la SEC,
        salvo que el fabricante de la batería indique un límite distinto.*
        """)

# ─────────────────────────────────────────────────────────────
# MÓDULO 14: CÁLCULO Y RESULTADOS DEL DIMENSIONAMIENTO
# ─────────────────────────────────────────────────────────────
st.divider()
st.header("📊 Resultados del Dimensionamiento")

datos_listos = (
    'hsp_diseno' in st.session_state and
    'panel' in st.session_state and
    'consumo_mensual_promedio' in st.session_state and
    'mes_diseno' in st.session_state
)

if datos_listos:
    if st.button("⚡ Calcular dimensionamiento"):

        import math

        # ── Parámetros ──────────────────────────────────────────
        mes_diseno      = st.session_state['mes_diseno']
        hsp             = st.session_state['hsp_diseno']                # kWh/m²/día
        p_mod           = st.session_state['panel']['P_stc']            # W

        # Si el usuario ingresó consumo mes a mes, usar el consumo real del mes de diseño.
        # Si usó ingreso rápido (promedio), usar ese promedio.
        consumos_reales = st.session_state.get('consumos_mensuales_reales')
        meses_orden = ['Enero','Febrero','Marzo','Abril','Mayo','Junio',
                       'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
        if consumos_reales and len(consumos_reales) == 12:
            idx_mes_diseno = meses_orden.index(mes_diseno)
            consumo_mensual = consumos_reales[idx_mes_diseno]   # kWh del mes crítico real
        else:
            consumo_mensual = st.session_state['consumo_mensual_promedio']  # kWh/mes promedio

        # Aplicar porcentaje de cobertura deseado
        cobertura_deseada = st.session_state.get('cobertura_deseada', 100) / 100
        consumo_diseno = consumo_mensual * cobertura_deseada     # kWh a cubrir con FV

        eta = 0.80 if tipo_sistema == "On-Grid (Conectado a la red)" else 0.75

        dias_mes = {
            'Enero': 31, 'Febrero': 28, 'Marzo': 31, 'Abril': 30,
            'Mayo': 31, 'Junio': 30, 'Julio': 31, 'Agosto': 31,
            'Septiembre': 30, 'Octubre': 31, 'Noviembre': 30, 'Diciembre': 31
        }
        n_dias = dias_mes[mes_diseno]

        # ── Ecuaciones del modelo ────────────────────────────────
        e_cons_diario = (consumo_diseno * 1000) / n_dias    # Wh/día  (Ec. 2.2)
        p_fv          = e_cons_diario / (hsp * eta)          # W       (Ec. 2.3)
        n_mod         = math.ceil(p_fv / p_mod)              # unid.   (Ec. 2.4)
        p_instalada   = n_mod * p_mod                        # W       (Ec. 2.5a)
        e_gen         = hsp * p_instalada * eta              # Wh/día  (Ec. 2.5b)

        # ── Resultados ───────────────────────────────────────────
        st.success("✅ Dimensionamiento completado exitosamente.")

        col_r1, col_r2, col_r3 = st.columns(3)
        col_r1.metric("Módulos requeridos", f"{n_mod} unidades")
        col_r2.metric("Potencia instalada", f"{round(p_instalada/1000, 2)} kWp")
        col_r3.metric("Energía generada/día", f"{round(e_gen/1000, 2)} kWh/día")

        st.info(f"""
**📋 Resumen del dimensionamiento:**
- Consumo diario de diseño: **{round(e_cons_diario/1000, 2)} kWh/día**
- HSP del mes de diseño ({mes_diseno}): **{round(hsp, 2)} h/día**
- Potencia FV requerida: **{round(p_fv/1000, 2)} kWp**
- Panel seleccionado: **{modelo_seleccionado}** ({p_mod} W)
- Número de módulos: **{n_mod} paneles**
- Potencia total instalada: **{round(p_instalada/1000, 2)} kWp**
- Energía generada estimada: **{round(e_gen/1000, 2)} kWh/día**
- Eficiencia global del sistema (η): **{int(eta*100)}%**
        """)

        # ─────────────────────────────────────────────────────────
        # 🔍 PROCESO DE CÁLCULO PASO A PASO (didáctico)
        # ─────────────────────────────────────────────────────────
        with st.expander("🔍 Ver el proceso de cálculo paso a paso"):

            st.markdown("""
            A continuación se muestra el razonamiento de ingeniería que la aplicación realizó 
            para llegar a los resultados anteriores. Cada paso utiliza tus datos reales.
            """)

            # ── Paso 1: Eficiencia ──────────────────────────────
            st.markdown("#### Paso 1️⃣ — Eficiencia global del sistema (η)")
            st.write(f"""
            La eficiencia global incorpora las pérdidas por conversión en el inversor, 
            resistencia del cableado, temperatura de operación, sombreado y suciedad.
            Como tu sistema es **{tipo_sistema}**, se aplica:
            """)
            st.latex(r"\eta_{sistema} = " + f"{eta}" + r" \quad (" + 
                     (r"80\%" if eta == 0.80 else r"75\%") + ")")
            st.caption(f"ℹ️ Los sistemas Off-Grid tienen menor eficiencia (75%) por las pérdidas adicionales del ciclo de carga/descarga de las baterías.")

            st.divider()

            # ── Paso 2: Consumo diario ──────────────────────────
            st.markdown("#### Paso 2️⃣ — Consumo diario de diseño")
            consumos_reales_txt = st.session_state.get('consumos_mensuales_reales')
            cob_pct = st.session_state.get('cobertura_deseada', 100)
            if consumos_reales_txt and len(consumos_reales_txt) == 12:
                origen_consumo = f"consumo real de **{mes_diseno}**"
            else:
                origen_consumo = "consumo mensual promedio"

            if cob_pct < 100:
                nota_cobertura = f" (ajustado al **{cob_pct}%** de cobertura deseada → {round(consumo_diseno, 2)} kWh)"
            else:
                nota_cobertura = ""

            st.write(f"""
            Convertimos el {origen_consumo} ({consumo_mensual} kWh){nota_cobertura} a un consumo diario en Wh,
            dividiendo por los días que tiene **{mes_diseno}** ({n_dias} días):
            """)
            st.latex(r"E_{cons,diario} = \frac{E_{mes} \times 1000}{N_{días}}")
            st.latex(
                r"E_{cons,diario} = \frac{" + f"{consumo_mensual}" + r" \times 1000}{" + 
                f"{n_dias}" + r"} = " + f"{round(e_cons_diario, 2)}" + r"\ \text{Wh/día}"
            )
            st.success(f"➡️ Consumo diario de diseño: **{round(e_cons_diario/1000, 2)} kWh/día**")

            st.divider()

            # ── Paso 3: Potencia FV requerida ──────────────────
            st.markdown("#### Paso 3️⃣ — Potencia requerida del campo fotovoltaico")
            st.write(f"""
            Con el consumo diario y las **Horas de Sol Pico (HSP)** del mes de diseño obtenidas 
            desde NASA POWER, calculamos cuánta potencia debe tener el campo solar:
            """)
            st.latex(r"P_{FV} = \frac{E_{cons,diario}}{HSP_{mes} \times \eta_{sistema}}")
            st.latex(
                r"P_{FV} = \frac{" + f"{round(e_cons_diario, 2)}" + r"}{" + 
                f"{round(hsp, 4)}" + r" \times " + f"{eta}" + r"} = " + 
                f"{round(p_fv, 2)}" + r"\ \text{W}"
            )
            st.success(f"➡️ Potencia FV requerida: **{round(p_fv/1000, 2)} kWp**")
            st.caption(f"ℹ️ Si elegiste el mes crítico ({mes_diseno}), esta potencia garantiza cubrir el consumo incluso en las peores condiciones del año.")

            st.divider()

            # ── Paso 4: Número de módulos ──────────────────────
            st.markdown("#### Paso 4️⃣ — Número de módulos necesarios")
            st.write(f"""
            Dividimos la potencia requerida entre la potencia nominal del panel **{modelo_seleccionado}** 
            ({p_mod} W) y redondeamos hacia arriba (función techo ⌈ ⌉) para asegurar cobertura total:
            """)
            st.latex(r"N_{mod} = \left\lceil \frac{P_{FV}}{P_{mod}} \right\rceil")
            n_mod_exacto = p_fv / p_mod
            st.latex(
                r"N_{mod} = \left\lceil \frac{" + f"{round(p_fv, 2)}" + r"}{" + 
                f"{p_mod}" + r"} \right\rceil = \left\lceil " + 
                f"{round(n_mod_exacto, 2)}" + r" \right\rceil = " + f"{n_mod}"
            )
            st.success(f"➡️ Número de módulos: **{n_mod} paneles**")
            st.caption("ℹ️ Se redondea hacia arriba porque no se pueden instalar fracciones de panel. Esto introduce un ligero sobredimensionamiento que aporta margen de seguridad.")

            st.divider()

            # ── Paso 5: Potencia instalada y energía generada ──
            st.markdown("#### Paso 5️⃣ — Potencia instalada y energía generada")
            st.write(f"""
            Con el número definitivo de módulos, calculamos la potencia total instalada 
            y la energía eléctrica que el sistema generará en un día promedio del mes de diseño:
            """)
            st.latex(r"P_{instalada} = N_{mod} \times P_{mod}")
            st.latex(
                r"P_{instalada} = " + f"{n_mod}" + r" \times " + f"{p_mod}" + 
                r" = " + f"{p_instalada}" + r"\ \text{W} = " + 
                f"{round(p_instalada/1000, 2)}" + r"\ \text{kWp}"
            )
            st.latex(r"E_{gen} = HSP_{mes} \times P_{instalada} \times \eta_{sistema}")
            st.latex(
                r"E_{gen} = " + f"{round(hsp, 4)}" + r" \times " + f"{p_instalada}" + 
                r" \times " + f"{eta}" + r" = " + f"{round(e_gen, 2)}" + 
                r"\ \text{Wh/día}"
            )
            st.success(f"➡️ Potencia instalada: **{round(p_instalada/1000, 2)} kWp** | Energía generada: **{round(e_gen/1000, 2)} kWh/día**")

        # ─────────────────────────────────────────────────────────
        # 💡 INTERPRETACIÓN DE LOS RESULTADOS
        # ─────────────────────────────────────────────────────────
        st.divider()
        st.subheader("💡 Interpretación de tus resultados")

        # Cálculos para la interpretación
        cobertura_pct = (e_gen / e_cons_diario) * 100
        excedente_diario = (e_gen - e_cons_diario) / 1000  # kWh/día
        e_gen_anual_estimado = (e_gen / 1000) * 365  # kWh/año (estimación simple)

        # Consumo anual: si el usuario ingresó los 12 meses, usar la SUMA real
        # (no el consumo del mes de diseño x12, que sobre/sub-estima el año
        # cuando el mes crítico difiere del promedio anual real).
        if consumos_reales and len(consumos_reales) == 12:
            consumo_anual = sum(consumos_reales)  # kWh/año (suma real ingresada)
        else:
            consumo_anual = consumo_mensual * 12  # kWh/año (estimación desde promedio)

        # Diagnóstico de cobertura
        if cobertura_pct >= 100:
            diagnostico = "✅ **El sistema cubre completamente tu consumo** en el mes de diseño."
            color_diag = "success"
        else:
            diagnostico = f"⚠️ El sistema cubre el **{round(cobertura_pct, 1)}%** de tu consumo en {mes_diseno}."
            color_diag = "warning"

        if color_diag == "success":
            st.success(diagnostico)
        else:
            st.warning(diagnostico)

        st.markdown(f"""
Tu sistema fotovoltaico de **{round(p_instalada/1000, 2)} kWp** instalados con **{n_mod} paneles** 
generará aproximadamente **{round(e_gen/1000, 2)} kWh por día** durante **{mes_diseno}** 
(el mes utilizado para el dimensionamiento).

**¿Qué significa esto en la práctica?**

- 📊 **Cobertura del consumo:** En {mes_diseno}, generarás un **{round(cobertura_pct, 1)}%** 
  de tu consumo diario promedio ({round(e_cons_diario/1000, 2)} kWh/día).
- ☀️ **Mejores meses:** Durante los meses de mayor radiación, tu sistema producirá 
  considerablemente más energía que la calculada aquí, ya que el dimensionamiento 
  se basó en el mes crítico.
- 📈 **Estimación anual aproximada:** Si tu consumo se mantiene constante, este sistema 
  podría generar alrededor de **{round(e_gen_anual_estimado)} kWh/año**, frente a un 
  consumo anual estimado de **{round(consumo_anual)} kWh/año**.
        """)

        # Recomendación según tipo de sistema
        if tipo_sistema == "On-Grid (Conectado a la red)":
            st.info(f"""
**🔌 Recomendación para sistemas On-Grid:**
Al estar conectado a la red bajo la **Ley N° 21.118 (Net Billing)**, los excedentes 
generados en los meses de mayor sol se inyectan a la red y se descuentan de tu boleta. 
Esto significa que el sobredimensionamiento de los meses de mayor radiación 
**no se pierde**, sino que compensa los meses de menor generación.
            """)
        else:
            st.info(f"""
**🔋 Recomendación para sistemas Off-Grid:**
Al ser un sistema aislado, toda la energía generada debe gestionarse localmente. 
Verifica que el dimensionamiento del banco de baterías (más abajo) sea adecuado 
para los **días de autonomía** que definiste, considerando que en {mes_diseno} 
la generación será la mínima del año.
            """)

        # ── Baterías (solo Off-Grid) ─────────────────────────────
        if tipo_sistema == "Off-Grid (Aislado con baterías)":
            st.divider()
            st.subheader("🔋 Banco de Baterías")

            dod     = st.session_state['dod']
            v_bat   = st.session_state['v_bat']
            d_aut   = st.session_state['dias_autonomia']
            tec_bat = st.session_state['tecnologia_bat']

            c_bat = (e_cons_diario * d_aut) / (v_bat * dod)  # Ah (Ec. 2.6)

            col_b1, col_b2, col_b3 = st.columns(3)
            col_b1.metric("Capacidad banco", f"{round(c_bat, 1)} Ah")
            col_b2.metric("Energía almacenada", f"{round((c_bat * v_bat)/1000, 2)} kWh")
            col_b3.metric("Autonomía", f"{d_aut} día(s)")

            st.info(f"""
**📋 Detalle banco de baterías:**
- Tecnología: **{tec_bat}**
- Profundidad de descarga (DoD): **{int(dod*100)}%**
- Tensión nominal del banco: **{v_bat} V**
- Días de autonomía: **{d_aut} día(s)**
- Capacidad total requerida: **{round(c_bat, 1)} Ah ({round((c_bat*v_bat)/1000, 2)} kWh)**
            """)

            # ── Proceso de cálculo del banco de baterías ────────
            with st.expander("🔍 Ver el cálculo del banco de baterías paso a paso"):

                st.markdown("""
                El dimensionamiento del banco de baterías garantiza que el sistema pueda operar 
                durante los días sin generación solar, sin superar la profundidad de descarga (DoD) 
                permitida para la tecnología seleccionada.
                """)

                st.markdown("#### Fórmula aplicada (Ecuación 2.7)")
                st.latex(r"C_{bat} = \frac{E_{cons,diario} \times D_{aut}}{V_{bat} \times DoD}")

                st.markdown("#### Sustitución con tus datos")
                st.write(f"""
                - Consumo diario: **{round(e_cons_diario, 2)} Wh/día**
                - Días de autonomía: **{d_aut} día(s)**
                - Tensión del banco: **{v_bat} V**
                - Profundidad de descarga ({tec_bat}): **{dod} ({int(dod*100)}%)**
                """)

                st.latex(
                    r"C_{bat} = \frac{" + f"{round(e_cons_diario, 2)}" + r" \times " + 
                    f"{d_aut}" + r"}{" + f"{v_bat}" + r" \times " + f"{dod}" + 
                    r"} = " + f"{round(c_bat, 1)}" + r"\ \text{Ah}"
                )

                st.success(f"➡️ Capacidad requerida del banco: **{round(c_bat, 1)} Ah ({round((c_bat*v_bat)/1000, 2)} kWh)**")

                st.caption(f"""
                ℹ️ Esta capacidad considera que solo se utilizará el {int(dod*100)}% de la 
                energía total nominal del banco. Si descargaras al 100%, reducirías 
                drásticamente la vida útil de las baterías {tec_bat}.
                """)

            with st.expander("💡 ¿Cómo interpretar estos resultados?"):
                st.write(f"""
La capacidad calculada de **{round(c_bat, 1)} Ah** representa la energía mínima
que debe almacenar el banco para garantizar **{d_aut} día(s)** sin generación solar,
sin superar el {int(dod*100)}% de descarga permitido para baterías {tec_bat}.

Para seleccionar las baterías comerciales, divide la capacidad total
entre la capacidad nominal de cada unidad a **{v_bat} V**.
                """)

        # ──────────────────────────────────────────────────────────
        # 💾 GUARDAR RESULTADOS PARA EL REPORTE FINAL
        # ──────────────────────────────────────────────────────────
        # Los resultados se almacenan en session_state para que el reporte
        # siga visible aunque Streamlit recargue la página (por ejemplo, al
        # presionar el botón de descarga).

        # Energía anual estimada usando el HSP real de CADA mes obtenido de
        # NASA POWER. Es más preciso que multiplicar el mes de diseño por 365,
        # porque considera la variación estacional de la radiación solar.
        df_hsp_anual = st.session_state['hsp_mensual']
        dias_por_mes = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        energia_mensual_kwh = []
        for idx_mes in range(12):
            hsp_m = float(df_hsp_anual['HSP (kWh/m²/día)'].iloc[idx_mes])
            e_mes = (hsp_m * p_instalada * eta * dias_por_mes[idx_mes]) / 1000
            energia_mensual_kwh.append(round(e_mes, 1))

        e_gen_anual       = sum(energia_mensual_kwh)                  # kWh/año
        consumo_anual_kwh = consumo_anual                             # kWh/año (suma real si hay datos mes a mes)
        cobertura_anual   = (e_gen_anual / consumo_anual_kwh) * 100   # %
        factor_planta     = (e_gen_anual * 1000) / (p_instalada * 8760)  # adim.
        yield_especifico  = e_gen_anual / (p_instalada / 1000)        # kWh/kWp/año

        resultados = {
            'fecha':            datetime.now().strftime('%d-%m-%Y %H:%M'),
            'tipo_sistema':     tipo_sistema,
            'latitud':          st.session_state['latitud'],
            'longitud':         st.session_state['longitud'],
            'inclinacion':      st.session_state.get('inclinacion', 0.0),
            'azimut':           st.session_state.get('azimut', 0.0),
            'modelo_panel':     modelo_seleccionado,
            'p_mod':            p_mod,
            'eficiencia_panel': st.session_state['panel']['eficiencia'],
            'area_panel':       st.session_state['panel']['area'],
            'mes_diseno':       mes_diseno,
            'hsp_diseno':       hsp,
            'hsp_anual':        st.session_state['hsp'],
            'hsp_mensual_lista': [round(float(df_hsp_anual['HSP (kWh/m²/día)'].iloc[i]), 4) for i in range(12)],
            'eta':              eta,
            'consumo_mensual':  consumo_mensual,
            'consumo_diseno':   consumo_diseno,
            'cobertura_deseada': st.session_state.get('cobertura_deseada', 100),
            'consumo_anual':    consumo_anual_kwh,
            'consumos_mensuales_reales': st.session_state.get('consumos_mensuales_reales', None),
            'e_cons_diario':    e_cons_diario,
            'p_fv':             p_fv,
            'n_mod':            n_mod,
            'p_instalada':      p_instalada,
            'e_gen_diario':     e_gen,
            'cobertura_mes':    cobertura_pct,
            'cobertura_anual':  cobertura_anual,
            'e_gen_anual':      e_gen_anual,
            'energia_mensual':  energia_mensual_kwh,
            'factor_planta':    factor_planta,
            'yield_especifico': yield_especifico,
            'area_total':       n_mod * st.session_state['panel']['area'],
        }

        # Datos del banco de baterías (solo si el sistema es Off-Grid)
        if tipo_sistema == "Off-Grid (Aislado con baterías)":
            resultados['bateria'] = {
                'c_bat':              c_bat,
                'dod':                dod,
                'v_bat':              v_bat,
                'd_aut':              d_aut,
                'tec_bat':            tec_bat,
                'energia_almacenada': (c_bat * v_bat) / 1000,   # kWh
            }

        st.session_state['reporte'] = resultados

else:
    st.warning("⚠️ Para calcular necesitas completar: ubicación, consumo, datos NASA y selección de panel.")


# ═════════════════════════════════════════════════════════════
# MÓDULO 15: REPORTE FINAL DEL PROYECTO
# ═════════════════════════════════════════════════════════════
st.divider()
st.header("📄 Reporte Final del Proyecto")


# ─────────────────────────────────────────────────────────────
# Estilos del reporte HTML descargable (CSS puro, sin dependencias)
# ─────────────────────────────────────────────────────────────
ESTILO_REPORTE = """
body { font-family: 'Segoe UI', Arial, sans-serif; color:#1a1a1a; margin:0;
       padding:0; background:#ffffff; }
.contenedor { max-width:820px; margin:0 auto; padding:36px; }
.cabecera { border-bottom:4px solid #FFC300; padding-bottom:14px; margin-bottom:22px; }
.cabecera h1 { margin:0; font-size:22px; color:#0b3d62; }
.cabecera p { margin:5px 0 0; color:#666; font-size:12px; }
h2 { color:#0b3d62; font-size:16px; border-left:5px solid #FFC300;
     padding-left:10px; margin-top:30px; }
table { width:100%; border-collapse:collapse; margin-top:10px; font-size:13px; }
th, td { border:1px solid #ddd; padding:8px 11px; text-align:left; }
th { background:#0b3d62; color:#fff; }
tr:nth-child(even) { background:#f6f8fa; }
.kpis { display:flex; flex-wrap:wrap; gap:12px; margin-top:12px; }
.kpi { flex:1 1 150px; background:#f6f8fa; border:1px solid #e0e0e0;
       border-top:4px solid #FFC300; border-radius:6px; padding:14px; text-align:center; }
.kpi .valor { font-size:23px; font-weight:700; color:#0b3d62; }
.kpi .etiqueta { font-size:11px; color:#666; margin-top:5px;
                 letter-spacing:.3px; }
.grafico { display:flex; align-items:flex-end; gap:6px; height:170px;
           margin-top:18px; border-bottom:2px solid #999; }
.barra-col { flex:1; display:flex; flex-direction:column; align-items:center;
             justify-content:flex-end; height:100%; }
.barra { width:72%; background:#FFC300; border-radius:3px 3px 0 0; min-height:2px; }
.barra-mes { font-size:9px; color:#555; margin-top:4px; }
.barra-val { font-size:9px; color:#333; margin-bottom:2px; }
.nota { background:#fff8e1; border-left:4px solid #FFC300; padding:11px 15px;
        font-size:12px; margin-top:18px; line-height:1.5; }
.pie { margin-top:34px; border-top:1px solid #ddd; padding-top:12px;
       font-size:11px; color:#888; text-align:center; }
@media print { .contenedor { padding:14px; } h2 { page-break-after:avoid; } }
"""


def construir_reporte_html(r):
    """Genera un reporte HTML autocontenido, listo para imprimir o guardar como PDF."""
    meses_c = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
               'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    hemis = "Sur" if r['latitud'] < 0 else "Norte"

    # Gráfico de barras HSP mensual (CSS puro)
    hsp_lista = r.get('hsp_mensual_lista') or []
    # Fallback: si no viene en el reporte, reconstruir desde session_state
    if not hsp_lista or len(hsp_lista) != 12:
        try:
            import streamlit as _st
            df_hsp_fb = _st.session_state.get('hsp_mensual')
            if df_hsp_fb is not None:
                hsp_lista = [round(float(df_hsp_fb['HSP (kWh/m²/día)'].iloc[i]), 4) for i in range(12)]
        except Exception:
            hsp_lista = [0] * 12

    mes_diseno_abrev = r['mes_diseno'][:3]  # "Junio" → "Jun"
    max_hsp = max(hsp_lista) or 1
    barras_hsp = ""
    for i, hsp_val in enumerate(hsp_lista):
        h = (hsp_val / max_hsp) * 100
        color_barra = "#e67e22" if meses_c[i] == mes_diseno_abrev else "#FFC300"
        barras_hsp += (
            f'<div class="barra-col">'
            f'<div class="barra-val">{hsp_val:.2f}</div>'
            f'<div class="barra" style="height:{h:.1f}%;background:{color_barra};border-radius:2px 2px 0 0;min-height:2px;"></div>'
            f'<div class="barra-mes">{meses_c[i]}</div>'
            f'</div>'
        )
    grafico_hsp = (
        f'<div class="grafico" style="height:140px;">{barras_hsp}</div>'
        f'<div style="font-size:10px;color:#888;margin-top:4px;">'
        f'<span style="display:inline-block;width:10px;height:10px;background:#FFC300;margin-right:4px;border-radius:2px;"></span>HSP mensual&nbsp;&nbsp;'
        f'<span style="display:inline-block;width:10px;height:10px;background:#e67e22;margin-right:4px;border-radius:2px;"></span>Mes de diseño ({r["mes_diseno"]})'
        f'</div>'
    )

    # Gráfico de barras de generación mensual vs consumo (CSS puro)
    consumos_reales_html = r.get('consumos_mensuales_reales')
    consumos_graf = consumos_reales_html if consumos_reales_html and len(consumos_reales_html) == 12 \
                    else [r['consumo_mensual']] * 12

    # Etiqueta del consumo usado para el dimensionamiento: si el usuario ingresó
    # los 12 meses, r['consumo_mensual'] es el consumo REAL del mes de diseño
    # (no un promedio); si usó ingreso rápido, sí es el promedio mensual.
    hay_datos_mensuales = bool(consumos_reales_html and len(consumos_reales_html) == 12)
    etiqueta_consumo_mensual = (
        "Consumo del mes de diseño" if hay_datos_mensuales
        else "Consumo mensual promedio"
    )

    max_e = max(max(r['energia_mensual']), max(consumos_graf)) or 1
    barras = ""
    for i, e in enumerate(r['energia_mensual']):
        h_gen = (e / max_e) * 100
        h_con = (consumos_graf[i] / max_e) * 100
        barras += (
            f'<div class="barra-col">'
            f'<div style="display:flex;align-items:flex-end;gap:2px;justify-content:center;height:150px;">'
            f'<div style="display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%;">'
            f'<div class="barra-val">{int(round(e))}</div>'
            f'<div class="barra" style="height:{h_gen:.1f}%;background:#FFC300;width:14px;border-radius:2px 2px 0 0;min-height:2px;"></div>'
            f'</div>'
            f'<div style="display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%;">'
            f'<div class="barra-val" style="color:#0b3d62;">{int(round(consumos_graf[i]))}</div>'
            f'<div class="barra" style="height:{h_con:.1f}%;background:#0b3d62;width:14px;border-radius:2px 2px 0 0;min-height:2px;opacity:0.75;"></div>'
            f'</div>'
            f'</div>'
            f'<div class="barra-mes">{meses_c[i]}</div>'
            f'</div>'
        )

    # Leyenda del gráfico
    leyenda_graf = (
        '<div style="display:flex;gap:16px;margin-top:8px;font-size:11px;">'
        '<span><span style="display:inline-block;width:12px;height:12px;background:#FFC300;border-radius:2px;margin-right:4px;"></span>Generación (kWh)</span>'
        '<span><span style="display:inline-block;width:12px;height:12px;background:#0b3d62;border-radius:2px;margin-right:4px;opacity:0.75;"></span>Consumo (kWh)</span>'
        '</div>'
    )

    # Filas de la tabla de balance mensual
    filas_mes = ""
    for i in range(12):
        gen = r['energia_mensual'][i]
        con = consumos_reales_html[i] if consumos_reales_html and len(consumos_reales_html) == 12 else r['consumo_mensual']
        bal = gen - con
        color_bal = "#1b7f3a" if bal >= 0 else "#b00020"
        filas_mes += (
            f"<tr><td>{meses_c[i]}</td>"
            f"<td>{gen:.1f}</td>"
            f"<td>{con:.1f}</td>"
            f'<td style="color:{color_bal};font-weight:600;">{bal:+.1f}</td></tr>'
        )

    # Sección de baterías (solo aparece en sistemas Off-Grid)
    seccion_bateria = ""
    if 'bateria' in r:
        b = r['bateria']
        seccion_bateria = f"""
      <h2>6. Banco de baterías</h2>
      <table>
        <tr><th>Parámetro</th><th>Valor</th></tr>
        <tr><td>Tecnología</td><td>{b['tec_bat']}</td></tr>
        <tr><td>Profundidad de descarga (DoD)</td><td>{int(b['dod']*100)} %</td></tr>
        <tr><td>Tensión nominal del banco</td><td>{b['v_bat']} V</td></tr>
        <tr><td>Días de autonomía</td><td>{b['d_aut']} día(s)</td></tr>
        <tr><td>Capacidad requerida</td><td>{b['c_bat']:.1f} Ah</td></tr>
        <tr><td>Energía almacenada</td><td>{b['energia_almacenada']:.2f} kWh</td></tr>
      </table>
        """

    cuerpo = f"""
    <div class="contenedor">
      <div class="cabecera">
        <h1>Reporte de Dimensionamiento Fotovoltaico</h1>
        <p>Calculadora Solar &mdash; Universidad de Los Lagos &middot; Generado el {r['fecha']}</p>
      </div>

      <h2>1. Datos generales del proyecto</h2>
      <table>
        <tr><th>Parámetro</th><th>Valor</th></tr>
        <tr><td>Tipo de sistema</td><td>{r['tipo_sistema']}</td></tr>
        <tr><td>Ubicación (latitud, longitud)</td><td>{r['latitud']:.4f}, {r['longitud']:.4f}</td></tr>
        <tr><td>Hemisferio</td><td>{hemis}</td></tr>
        <tr><td>Inclinación de los módulos</td><td>{r['inclinacion']:.1f}°</td></tr>
        <tr><td>Azimut</td><td>{r['azimut']:.0f}°</td></tr>
      </table>

      <h2>2. Parámetros de entrada</h2>
      <table>
        <tr><th>Parámetro</th><th>Valor</th></tr>
        <tr><td>{etiqueta_consumo_mensual}</td><td>{r['consumo_mensual']:.1f} kWh/mes</td></tr>
        <tr><td>Consumo anual estimado</td><td>{r['consumo_anual']:.0f} kWh/año</td></tr>
        <tr><td>Cobertura de diseño utilizada</td><td>{r.get('cobertura_deseada', 100)} %</td></tr>
        <tr><td>Mes de diseño (mes crítico)</td><td>{r['mes_diseno']}</td></tr>
        <tr><td>HSP del mes de diseño</td><td>{r['hsp_diseno']:.2f} kWh/m²/día</td></tr>
        <tr><td>HSP promedio anual</td><td>{r['hsp_anual']:.2f} kWh/m²/día</td></tr>
        <tr><td>Eficiencia global del sistema (η)</td><td>{int(r['eta']*100)} %</td></tr>
      </table>

      <h3 style="margin-top:18px;font-size:13px;color:#0b3d62;">Irradiancia mensual — Promedio histórico NASA POWER (1984–2024)</h3>
      {grafico_hsp}

      <h2>3. Módulo fotovoltaico seleccionado</h2>
      <table>
        <tr><th>Parámetro</th><th>Valor</th></tr>
        <tr><td>Modelo</td><td>{r['modelo_panel']}</td></tr>
        <tr><td>Potencia nominal (STC)</td><td>{r['p_mod']} W</td></tr>
        <tr><td>Eficiencia del módulo</td><td>{r['eficiencia_panel']} %</td></tr>
        <tr><td>Área por módulo</td><td>{r['area_panel']} m²</td></tr>
      </table>

      <h2>4. Resultados del dimensionamiento</h2>
      <table>
        <tr><th>Resultado</th><th>Valor</th></tr>
        <tr><td>Consumo diario de diseño</td><td>{r['e_cons_diario']/1000:.2f} kWh/día</td></tr>
        <tr><td>Potencia FV requerida</td><td>{r['p_fv']/1000:.2f} kWp</td></tr>
        <tr><td>Número de módulos</td><td>{r['n_mod']} unidades</td></tr>
        <tr><td>Potencia instalada</td><td>{r['p_instalada']/1000:.2f} kWp</td></tr>
        <tr><td>Área total estimada del arreglo</td><td>{r['area_total']:.1f} m²</td></tr>
        <tr><td>Energía generada (mes de diseño)</td><td>{r['e_gen_diario']/1000:.2f} kWh/día</td></tr>
        <tr><td>Energía generada estimada anual</td><td>{r['e_gen_anual']:.0f} kWh/año</td></tr>
      </table>

      <h2>5. Indicadores de desempeño</h2>
      <div class="kpis">
        <div class="kpi"><div class="valor">{r['factor_planta']*100:.1f}%</div><div class="etiqueta">Factor de planta</div></div>
        <div class="kpi"><div class="valor">{r['yield_especifico']:.0f}</div><div class="etiqueta">kWh/kWp por año</div></div>
        <div class="kpi"><div class="valor">{r['cobertura_anual']:.1f}%</div><div class="etiqueta">Cobertura anual</div></div>
        <div class="kpi"><div class="valor">{int(r['eta']*100)}%</div><div class="etiqueta">Eficiencia global</div></div>
      </div>

      <h2>Generación mensual estimada</h2>
      <div class="grafico">{barras}</div>
      {leyenda_graf}
      <table>
        <tr><th>Mes</th><th>Generación (kWh)</th><th>Consumo (kWh)</th><th>Balance (kWh)</th></tr>
        {filas_mes}
        <tr style="font-weight:700;background:#eef2f5;">
          <td>Total anual</td><td>{r['e_gen_anual']:.0f}</td>
          <td>{r['consumo_anual']:.0f}</td>
          <td>{r['e_gen_anual']-r['consumo_anual']:+.0f}</td>
        </tr>
      </table>
      {seccion_bateria}
      <div class="nota">
        <strong>Nota normativa y académica:</strong> los módulos considerados cuentan con
        certificación IEC 61215 e IEC 61730 exigida por la Instrucción Técnica RGR N°02/2024
        de la SEC. En sistemas conectados a red aplica la Ley N°21.118 (Net Billing) y el
        inversor debe cumplir con la protección anti-isla establecida en la RGR N°06/2024.
        Este reporte tiene fines académicos y orientativos; el proyecto definitivo debe ser
        revisado y validado por un instalador eléctrico autorizado por la SEC.
      </div>

      <div class="pie">
        Documento generado automáticamente por la Calculadora Solar ULagos &middot;
        Trabajo de Titulación &middot; Datos de radiación solar: NASA POWER (1984&ndash;2024)
      </div>
    </div>
    """

    return (
        "<!DOCTYPE html><html lang='es'><head><meta charset='utf-8'>"
        "<title>Reporte de Dimensionamiento Fotovoltaico</title>"
        f"<style>{ESTILO_REPORTE}</style></head><body>{cuerpo}</body></html>"
    )


# ─────────────────────────────────────────────────────────────
# Renderizado del reporte en pantalla
# ─────────────────────────────────────────────────────────────
if 'reporte' not in st.session_state:
    st.info(
        "ℹ️ Todavía no hay un reporte disponible. Completa el dimensionamiento en la "
        "sección anterior presionando el botón **⚡ Calcular dimensionamiento** y el "
        "reporte se generará automáticamente en esta sección."
    )
else:
    r = st.session_state['reporte']

    st.markdown("""
    Esta sección reúne en un solo lugar los **parámetros de entrada**, los **resultados del
    dimensionamiento** y los **indicadores de desempeño** del sistema diseñado. Puedes
    revisarlo en pantalla y descargarlo para adjuntarlo a tu informe o presentación.
    """)
    st.caption(f"🕒 Reporte generado a partir del último cálculo realizado: {r['fecha']}")

    # ── Resumen ejecutivo ──────────────────────────────────────
    st.subheader("🧾 Resumen ejecutivo")
    cob_txt = f"cubriendo el **{r['cobertura_deseada']}%** del consumo de {r['mes_diseno']}" \
              if r.get('cobertura_deseada', 100) < 100 \
              else f"cubriendo el **100%** del consumo de {r['mes_diseno']}"
    st.markdown(f"""
Sistema fotovoltaico **{r['tipo_sistema']}** compuesto por **{r['n_mod']} módulos** del modelo
**{r['modelo_panel']}**, alcanzando una potencia instalada de **{round(r['p_instalada']/1000, 2)} kWp**.
El diseño se realizó utilizando el mes de diseño (**{r['mes_diseno']}**), {cob_txt}, y datos satelitales de
NASA POWER del periodo 1984–2024. Se estima una generación anual de
**{round(r['e_gen_anual'])} kWh**, equivalente al **{round(r['cobertura_anual'], 1)}%** del
consumo anual estimado (**{round(r['consumo_anual'])} kWh**).
    """)

    # ── Indicadores clave de desempeño (KPI) ───────────────────
    st.subheader("📈 Indicadores de desempeño (KPI)")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Factor de planta", f"{round(r['factor_planta']*100, 1)} %")
    k2.metric("Productividad", f"{round(r['yield_especifico'])} kWh/kWp")
    k3.metric("Cobertura anual", f"{round(r['cobertura_anual'], 1)} %")
    k4.metric("Eficiencia global", f"{int(r['eta']*100)} %")

    with st.expander("💡 ¿Qué significan estos indicadores?"):
        st.markdown(f"""
* **Factor de planta ({round(r['factor_planta']*100, 1)}%):** relación entre la energía que el
  sistema genera realmente en un año y la que generaría si funcionara a su potencia nominal
  durante las 8.760 horas del año. En instalaciones fotovoltaicas residenciales fijas suele
  situarse entre **15% y 22%**; un valor más alto indica un mejor recurso solar disponible.
* **Productividad o *yield* específico ({round(r['yield_especifico'])} kWh/kWp/año):** energía
  generada por cada kWp instalado durante un año. Es el indicador más práctico para
  **comparar tu diseño con software profesional** (PVsyst, Sunny Design) o con instalaciones
  ubicadas en otras zonas del país.
* **Cobertura anual ({round(r['cobertura_anual'], 1)}%):** porcentaje del consumo anual que el
  sistema logra abastecer. En sistemas *On-Grid* con Net Billing, valores cercanos o
  superiores al 100% indican que se inyectarán excedentes a la red eléctrica.
* **Eficiencia global ({int(r['eta']*100)}%):** rendimiento del sistema una vez descontadas
  las pérdidas por inversor, cableado, temperatura, suciedad y sombreado.
        """)

    # ── Balance energético anual ───────────────────────────────
    st.subheader("⚡ Balance energético anual")
    e1, e2, e3 = st.columns(3)
    e1.metric("Energía generada", f"{round(r['e_gen_anual'])} kWh/año")
    e2.metric("Consumo estimado", f"{round(r['consumo_anual'])} kWh/año")
    balance = r['e_gen_anual'] - r['consumo_anual']
    e3.metric("Balance neto", f"{round(balance)} kWh/año", delta=f"{round(balance)} kWh")

    meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
             'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

    # Usar consumos reales mes a mes si el usuario los ingresó en modo detallado
    consumos_reales = r.get('consumos_mensuales_reales')
    if consumos_reales and len(consumos_reales) == 12:
        consumo_grafico = consumos_reales
        caption_consumo = "consumo real ingresado mes a mes"
    else:
        consumo_grafico = [round(r['consumo_mensual'], 1)] * 12
        caption_consumo = "consumo mensual promedio"

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Generación (kWh)',
        x=meses,
        y=r['energia_mensual'],
        marker_color='#FFC300',
    ))
    fig.add_trace(go.Bar(
        name='Consumo (kWh)',
        x=meses,
        y=consumo_grafico,
        marker_color='#0b3d62',
    ))
    fig.update_layout(
        barmode='group',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(t=30, b=10, l=10, r=10),
        yaxis_title='kWh',
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        f"El gráfico compara la energía generada cada mes —calculada con el HSP real de NASA "
        f"para ese mes— frente al {caption_consumo}."
    )

    # ── Ficha resumen del dimensionamiento ─────────────────────
    st.subheader("📋 Ficha resumen del dimensionamiento")
    st.markdown(f"""
| Parámetro | Valor |
|---|---|
| Tipo de sistema | {r['tipo_sistema']} |
| Ubicación (lat, lon) | {r['latitud']:.4f}, {r['longitud']:.4f} |
| Inclinación / Azimut | {r['inclinacion']:.1f}° / {r['azimut']:.0f}° |
| Mes de diseño | {r['mes_diseno']} (HSP = {r['hsp_diseno']:.2f} kWh/m²/día) |
| Panel seleccionado | {r['modelo_panel']} ({r['p_mod']} W) |
| Número de módulos | {r['n_mod']} unidades |
| Potencia instalada | {round(r['p_instalada']/1000, 2)} kWp |
| Área total estimada | {r['area_total']:.1f} m² |
| Energía generada (mes de diseño) | {round(r['e_gen_diario']/1000, 2)} kWh/día |
| Energía generada (anual) | {round(r['e_gen_anual'])} kWh/año |
| Eficiencia global del sistema | {int(r['eta']*100)} % |
""")

    # ── Banco de baterías (solo Off-Grid) ──────────────────────
    if 'bateria' in r:
        b = r['bateria']
        st.markdown(f"""
**🔋 Banco de baterías**

| Parámetro | Valor |
|---|---|
| Tecnología | {b['tec_bat']} |
| Profundidad de descarga (DoD) | {int(b['dod']*100)} % |
| Tensión nominal del banco | {b['v_bat']} V |
| Días de autonomía | {b['d_aut']} día(s) |
| Capacidad requerida | {b['c_bat']:.1f} Ah ({b['energia_almacenada']:.2f} kWh) |
""")

    # ── Descarga del reporte ───────────────────────────────────
    st.divider()
    st.subheader("⬇️ Descargar reporte")

    reporte_html = construir_reporte_html(r)

    # Reconstruir df_balance para exportar CSV
    _meses_csv = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    _consumos_csv = r.get('consumos_mensuales_reales') or [round(r['consumo_mensual'], 1)] * 12
    df_balance = pd.DataFrame({
        'Mes': _meses_csv,
        'Generación (kWh)': r['energia_mensual'],
        'Consumo (kWh)': _consumos_csv,
    })
    csv_mensual = df_balance.to_csv(index=False).encode('utf-8')
    fecha_archivo = r['fecha'][:10].replace('-', '')

    d1, d2 = st.columns(2)
    with d1:
        st.download_button(
            "📄 Descargar reporte completo (HTML)",
            data=reporte_html,
            file_name=f"reporte_fotovoltaico_{fecha_archivo}.html",
            mime="text/html",
            use_container_width=True
        )
    with d2:
        st.download_button(
            "📊 Descargar datos mensuales (CSV)",
            data=csv_mensual,
            file_name=f"generacion_mensual_{fecha_archivo}.csv",
            mime="text/csv",
            use_container_width=True
        )

    st.caption(
        "💡 El reporte HTML está diseñado para imprimirse: ábrelo en tu navegador y usa "
        "**Imprimir → Guardar como PDF** para obtener un documento PDF "
    )
