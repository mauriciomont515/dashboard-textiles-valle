import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="BI Textil - Auditoría Creativa", page_icon="🧵", layout="wide")

st.title("🧵 Laboratorio Creativo: Textiles del Valle")
st.markdown("Plataforma de Business Intelligence para auditar el rendimiento y planificar el contenido.")

# --- CONEXIÓN A GOOGLE SHEETS ---
@st.cache_data(ttl=600)
def cargar_datos():
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    ruta_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_json = os.path.join(ruta_actual, 'credenciales_google.json')
    credenciales = Credentials.from_service_account_file(ruta_json, scopes=scopes)
    cliente = gspread.authorize(credenciales)
    
    # ⚠️ REEMPLAZA ESTA URL CON LA DEL EXCEL DE LA FÁBRICA
    url_excel = 'https://docs.google.com/spreadsheets/d/1qdYoi0NrtW-tr_gNboY6rbOHf_u05tbiYsAANcF4BJY/edit'
    hoja = cliente.open_by_url(url_excel).worksheet('Auditoria_Creativos')
    
    datos = hoja.get_all_records()
    df = pd.DataFrame(datos)
    
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    columnas_numericas = ['Alcance', 'Likes', 'Comentarios', 'Guardados']
    for col in columnas_numericas:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
    # 🧠 NUEVA INTELIGENCIA: El Índice de Efectividad (Evitamos división por cero)
    df['Efectividad (%)'] = df.apply(
        lambda row: (row['Guardados'] / row['Alcance'] * 100) if row['Alcance'] > 0 else 0, 
        axis=1
    )
        
    return df

try:
    df = cargar_datos()
except Exception as e:
    st.error(f"🚨 Error conectando a la base de datos: {e}")
    st.stop()

# --- PANEL DE CONTROL ---
st.sidebar.header("Filtros de Análisis")
formatos_disponibles = df['Formato'].unique().tolist()
formato_seleccionado = st.sidebar.multiselect("Filtrar por Formato:", formatos_disponibles, default=formatos_disponibles)

df_filtrado = df[df['Formato'].isin(formato_seleccionado)]

if df_filtrado.empty:
    st.warning("No hay datos para los filtros seleccionados.")
    st.stop()

# --- MÉTRICAS PRINCIPALES ---
st.markdown("### 🎯 Rendimiento Global (Últimos 50 posts)")
col1, col2, col3, col4 = st.columns(4)

total_alcance = int(df_filtrado['Alcance'].sum())
total_guardados = int(df_filtrado['Guardados'].sum())
total_interacciones = int(df_filtrado['Likes'].sum() + df_filtrado['Comentarios'].sum() + df_filtrado['Guardados'].sum())
mejor_formato = df_filtrado.groupby('Formato')['Alcance'].mean().idxmax() if not df_filtrado.empty else "N/A"

col1.metric("Alcance Total Acumulado", f"{total_alcance:,}")
col2.metric("Super Engagement (Guardados)", f"{total_guardados:,}")
col3.metric("Interacciones Totales", f"{total_interacciones:,}")
col4.metric("Formato más Viral", mejor_formato)

st.markdown("---")

# --- GRÁFICAS ESTRATÉGICAS ---
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    st.markdown("#### 🔬 Radar de Eficiencia (Alcance vs Tasa de Interés)")
    # Ahora graficamos Alcance vs Efectividad. Las burbujas grandes son más guardados.
    fig_scatter = px.scatter(
        df_filtrado, 
        x='Alcance', 
        y='Efectividad (%)', 
        size='Guardados',
        color='Formato',
        hover_data=['Fecha', 'Likes'],
        title="Buscando el Cuadrante Mágico (Alto Alcance + Alta Efectividad)",
        template="plotly_white",
        size_max=30
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with col_graf2:
    st.markdown("#### 📊 Alcance Promedio por Formato")
    df_promedio = df_filtrado.groupby('Formato', as_index=False)['Alcance'].mean()
    fig_barras = px.bar(
        df_promedio, 
        x='Formato', 
        y='Alcance', 
        color='Formato',
        text_auto='.0f',
        title="¿Qué formato empuja más el algoritmo?",
        template="plotly_white"
    )
    st.plotly_chart(fig_barras, use_container_width=True)

st.markdown("---")

# --- SIMULADOR DE ESTRATEGIA (LA JOYA DE LA CORONA) ---
st.markdown("### 🕹️ Simulador de Impacto (Planeación del Mes)")
st.info("Ajusta la cantidad de piezas que el equipo creativo va a producir esta semana/mes para proyectar los resultados.")

# Calculamos promedios reales para el simulador
promedios = df.groupby('Formato')[['Alcance', 'Guardados']].mean().fillna(0).to_dict('index')

col_sim1, col_sim2 = st.columns([1, 2])

with col_sim1:
    st.markdown("**Plan de Producción:**")
    # Creamos sliders dinámicos basados en los formatos que existen
    plan_produccion = {}
    for formato in formatos_disponibles:
        plan_produccion[formato] = st.slider(f"Cantidad de {formato}s", min_value=0, max_value=20, value=5)

with col_sim2:
    # Calculamos la proyección en tiempo real
    alcance_proyectado = sum(plan_produccion[f] * promedios.get(f, {}).get('Alcance', 0) for f in formatos_disponibles)
    guardados_proyectados = sum(plan_produccion[f] * promedios.get(f, {}).get('Guardados', 0) for f in formatos_disponibles)
    eficiencia_proyectada = (guardados_proyectados / alcance_proyectado * 100) if alcance_proyectado > 0 else 0
    
    st.markdown("**Proyección de Resultados:**")
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("Alcance Estimado", f"{int(alcance_proyectado):,}")
    sc2.metric("Guardados Estimados", f"{int(guardados_proyectados):,}")
    sc3.metric("Eficiencia Global", f"{eficiencia_proyectada:.2f}%")
    
    # El Traductor Bitácora Automático
    if eficiencia_proyectada > 3.0:
        st.success("💡 **Diagnóstico:** Esta es una mezcla de alto valor. Estás priorizando formatos que generan mucha retención y guardados. ¡Excelente plan!")
    elif eficiencia_proyectada > 1.5:
        st.warning("💡 **Diagnóstico:** Mezcla estándar. Vas a tener buen alcance, pero podrías subir los guardados si cambias algunas imágenes por videos.")
    else:
        st.error("💡 **Diagnóstico:** Alerta. Esta mezcla prioriza alcance vacío. La gente lo verá pero no guardará el contenido. Aumenta la producción de Video.")

st.markdown("---")

# --- TABLA DE LOS MEJORES POSTS ---
st.markdown("### 🏆 Top 5: El Estándar a Replicar")
st.markdown("Estos son los contenidos con mayor cantidad de guardados. **Pide al equipo creativo que estudie estos enlaces.**")

df_top = df_filtrado.sort_values(by='Guardados', ascending=False).head(5)
st.dataframe(
    df_top[['Fecha', 'Formato', 'Alcance', 'Guardados', 'Efectividad (%)', 'Link']],
    use_container_width=True,
    hide_index=True
)

st.markdown("---")

# --- CIERRE GERENCIAL Y RETO DEL EQUIPO ---
col_final1, col_final2 = st.columns([2, 1])

with col_final1:
    st.markdown("### 🎯 El Reto de la Semana para el Equipo")
    if not df_top.empty:
        mejor_alcance = int(df_top['Alcance'].max())
        mejor_guardado = int(df_top['Guardados'].max())
        formato_estrella = df_top.iloc[0]['Formato']
        
        st.info(f"""
        **Directriz basada en datos:**
        Nuestro contenido récord actual logró **{mejor_guardado} guardados** y alcanzó a **{mejor_alcance} cuentas** usando formato **{formato_estrella}**.
        
        **Misión del Equipo Creativo:** No usen IA. Reúnanse, analicen por qué ese {formato_estrella} conectó tanto con la audiencia, y diseñen una pieza original esta semana que tenga el objetivo de superar la barrera de los **{int(mejor_guardado * 1.1)} guardados** (crecimiento del 10%).
        """)
    else:
        st.info("Filtra los datos para ver el récord actual.")

with col_final2:
    st.markdown("### 📥 Reporte Gerencial")
    st.markdown("Descarga la base de datos limpia con los filtros actuales para presentar en comité.")
    
    # Lógica para descargar el CSV
    csv = df_filtrado.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Descargar Data en CSV",
        data=csv,
        file_name="Reporte_Creativo_Textiles.csv",
        mime="text/csv",
        use_container_width=True
    )