import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import requests

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="HPC TSP Dashboard", layout="wide")
st.title("⚙️ Análisis de Rendimiento - Clúster TSP (Branch & Bound)")
st.markdown("Visualización de métricas de escalabilidad, tiempos teóricos vs reales y eficiencia de nodos.")

# --- CARGA DE DATOS ---
@st.cache_data
def load_data():
    # Opción A: Cargar desde un archivo JSON local (recomendado para pruebas rápidas)
    #try:
    #    with open("resultados_tsp.json", "r") as file:
    #        data = json.load(file)
    #        return pd.json_normalize(data)
    #except FileNotFoundError:
    #    st.error("No se encontró el archivo 'resultados_tsp.json'. Asegúrate de que esté en la misma carpeta.")
    #    return pd.DataFrame()
    
    # Opción B: Si tienes el servidor Go corriendo, descomenta estas líneas para usar la API:
    # import requests
     response = requests.get("http://localhost:8080/api/results")
     return pd.json_normalize(response.json())

df = load_data()

if not df.empty:
    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("Parámetros del Clúster")
    
    # Filtrar por Instancia de Nodos (Ciudades)
    instancias_disponibles = sorted(df["instance_nodes"].astype(int).unique())
    instancia_seleccionada = st.sidebar.selectbox(
        "Seleccione la Instancia (Cantidad de Nodos/Ciudades):", 
        instancias_disponibles
    )

    # Aplicar filtro
    df_filtrado = df[df["instance_nodes"] == str(instancia_seleccionada)].sort_values(by="processors")

    # --- MÉTRICAS PRINCIPALES ---
    st.markdown(f"### Resultados para Instancia de **{instancia_seleccionada} Nodos**")
    
    # Mostrar el tiempo secuencial base (Ts)
    ts_base = df_filtrado["Ts"].iloc[0] if not df_filtrado.empty else 0
    st.info(f"⏱️ **Tiempo Secuencial Base ($T_s$):** {ts_base} segundos")

    # --- GRÁFICAS ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Análisis de Tiempos: Real vs Teórico")
        fig_times = go.Figure()
        
        # Tiempo Real (Tp)
        fig_times.add_trace(go.Scatter(
            x=df_filtrado["processors"], 
            y=df_filtrado["Tp"],
            mode='lines+markers',
            name='Tiempo Real ($T_p$)',
            line=dict(color='red', width=2)
        ))
        
        # Tiempo Teórico Ideal (Tp_theo)
        fig_times.add_trace(go.Scatter(
            x=df_filtrado["processors"], 
            y=df_filtrado["Tp_theo"],
            mode='lines+markers',
            name='Tiempo Teórico Ideal',
            line=dict(color='green', width=2, dash='dash')
        ))
        
        fig_times.update_layout(
            xaxis_title="Número de Procesadores",
            yaxis_title="Tiempo (segundos)",
            hovermode="x unified"
        )
        st.plotly_chart(fig_times, use_container_width=True)

    with col2:
        st.subheader("Eficiencia y Aceleración (Speedup)")
        fig_metrics = go.Figure()
        
        # Speedup
        fig_metrics.add_trace(go.Scatter(
            x=df_filtrado["processors"], 
            y=df_filtrado["speedup_score"],
            mode='lines+markers',
            name='Speedup (Multiplicador)',
            line=dict(color='blue', width=2)
        ))
        
        # Eficiencia
        fig_metrics.add_trace(go.Scatter(
            x=df_filtrado["processors"], 
            y=df_filtrado["eficency_score"],
            mode='lines+markers',
            name='Eficiencia (0 a 1)',
            line=dict(color='orange', width=2)
        ))
        
        fig_metrics.update_layout(
            xaxis_title="Número de Procesadores",
            yaxis_title="Puntuación",
            hovermode="x unified"
        )
        st.plotly_chart(fig_metrics, use_container_width=True)

    # --- TABLA DE DATOS CRUDOS ---
    st.subheader("Datos Experimentales Detallados")
    # Formatear la tabla para mostrar solo columnas relevantes
    columnas_mostrar = ["processors", "Ts", "Tp", "Tp_theo", "energy", "speedup_score", "eficency_score"]
    df_mostrar = df_filtrado[columnas_mostrar].rename(columns={
        "processors": "Procesadores",
        "Ts": "T. Secuencial (s)",
        "Tp": "T. Paralelo Real (s)",
        "Tp_theo": "T. Paralelo Teórico (s)",
        "energy": "Energía Consumida",
        "speedup_score": "Speedup",
        "eficency_score": "Eficiencia"
    })
    
    st.dataframe(df_mostrar.style.format({
        "T. Secuencial (s)": "{:.3f}",
        "T. Paralelo Real (s)": "{:.3f}",
        "T. Paralelo Teórico (s)": "{:.3f}",
        "Energía Consumida": "{:.4f}",
        "Speedup": "{:.3f}",
        "Eficiencia": "{:.3f}"
    }), use_container_width=True)