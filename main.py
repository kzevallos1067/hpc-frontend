
import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
import math
import json
from typing import Optional
import pandas as pd

from helpers.helpers import *

# ── Page config ────────────────────────────────────────────────
st.set_page_config(
    page_title="HPC TSP Analyzer",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load Custom CSS ────────────────────────────────────────────
def load_css(file_name):
    with open(file_name, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Llama a la función apuntando al archivo que acabas de crear
load_css("static/style.css")


# ── Mock data ───────────────────────────────────────────────────
MOCK_RESULTS = [
    {"instance_nodes": "5",  "minimal_distance": 7.0,  "secuence": {"sequence": [{"id":1,"distance":0},{"id":3,"distance":4},{"id":5,"distance":7}], "total_distance": 11.0},  "Ts":240,"Tp":43,  "energy":180, "processors":2,  "eficency_score":0.70,"speedup_score":5.6,  "consumption_score":180},
    {"instance_nodes": "5",  "minimal_distance": 7.0,  "secuence": {"sequence": [{"id":1,"distance":0},{"id":3,"distance":4},{"id":5,"distance":7}], "total_distance": 7.0},  "Ts":240,"Tp":43,  "energy":180, "processors":4,  "eficency_score":0.80,"speedup_score":6.6,  "consumption_score":190},
    {"instance_nodes": "5",  "minimal_distance": 7.0,  "secuence": {"sequence": [{"id":1,"distance":0},{"id":3,"distance":4},{"id":5,"distance":7}], "total_distance": 7.0},  "Ts":240,"Tp":43,  "energy":180, "processors":8,  "eficency_score":0.80,"speedup_score":6.6,  "consumption_score":190},
    {"instance_nodes": "11", "minimal_distance": 27.0, "secuence": {"sequence": [{"id":1,"distance":0},{"id":2,"distance":5},{"id":3,"distance":8},{"id":11,"distance":14}],"total_distance":27.0},"Ts":820,"Tp":84,  "energy":520, "processors":16, "eficency_score":0.61,"speedup_score":9.8,  "consumption_score":520},
    {"instance_nodes": "12", "minimal_distance": 18.0, "secuence": {"sequence": [{"id":1,"distance":0},{"id":2,"distance":4},{"id":3,"distance":10},{"id":12,"distance":18}],"total_distance":18.0},"Ts":1100,"Tp":121,"energy":700, "processors":16, "eficency_score":0.57,"speedup_score":9.1,  "consumption_score":700},
    {"instance_nodes": "15", "minimal_distance": 22.0, "secuence": {"sequence": [{"id":1,"distance":0},{"id":2,"distance":5},{"id":4,"distance":12},{"id":15,"distance":22}],"total_distance":22.0},"Ts":2400,"Tp":148,"energy":1500,"processors":32, "eficency_score":0.50,"speedup_score":16.2, "consumption_score":1500},
    {"instance_nodes": "17", "minimal_distance": 28.0, "secuence": {"sequence": [{"id":1,"distance":0},{"id":3,"distance":4},{"id":7,"distance":12},{"id":17,"distance":28}],"total_distance":28.0},"Ts":4200,"Tp":228,"energy":2580,"processors":32, "eficency_score":0.57,"speedup_score":18.4, "consumption_score":2580},
]

# ── Session state ───────────────────────────────────────────────
if "results" not in st.session_state:
    st.session_state.results = MOCK_RESULTS
if "api_status" not in st.session_state:
    st.session_state.api_status = "demo"  # "demo" | "live" | "error"




# ════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="font-family:'Syne',sans-serif; font-size:28px; font-weight:800; color:#1D9E75; letter-spacing:-0.02em; line-height:1; padding-bottom:4px;">HPC</div>
    <div style="font-size:9px; letter-spacing:0.22em; color:#4a4a46; padding-bottom:20px; border-bottom:1px solid rgba(255,255,255,0.06);">GRAPH ANALYZER</div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # API connection
    st.markdown('<div class="section-header">Fuente de datos</div>', unsafe_allow_html=True)
    api_url = st.text_input(
        "URL del endpoint",
        value="http://localhost:8080/api/results",
        placeholder="http://host:port/api/results",
        label_visibility="visible",
    )

    col_btn, col_status = st.columns([2, 1])
    with col_btn:
        if st.button("↻  Actualizar", width="stretch"):
            ok, msg = fetch_from_api(api_url)
            if ok:
                st.success(msg)
            else:
                st.error(msg)
    with col_status:
        st.markdown(f"<div style='padding-top:8px; font-size:11px; color:#8b8a82;'>{status_badge()}</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Node filter
    results = get_results()
    all_nodes = sorted(set(r["instance_nodes"] for r in results))
    st.markdown('<div class="section-header">Filtros</div>', unsafe_allow_html=True)
    selected_nodes = st.multiselect(
        "Tamaños de grafo",
        options=all_nodes,
        default=all_nodes,
        format_func=lambda x: f"{x} nodos",
    )

    # Processor filter
    all_procs = sorted(set(r["processors"] for r in results))
    selected_procs = st.multiselect(
        "Procesadores",
        options=all_procs,
        default=all_procs,
        format_func=lambda x: f"{x}p",
    )

    st.markdown("---")
    st.markdown(f"""
    <div style='font-size:10px; color:#4a4a46; line-height:1.8;'>
    Registros totales: <span style='color:#8b8a82'>{len(results)}</span><br>
    Instancias únicas: <span style='color:#8b8a82'>{len(all_nodes)}</span><br>
    </div>
    """, unsafe_allow_html=True)

# ── Apply filters ───────────────────────────────────────────────
filtered = [
    r for r in get_results()
    if r["instance_nodes"] in (selected_nodes or all_nodes)
    and r["processors"] in (selected_procs or all_procs)
]

# ════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ════════════════════════════════════════════════════════════════
st.markdown("""
<div style='font-family:"Syne",sans-serif; font-size:22px; font-weight:800; color:#e8e6df; letter-spacing:-0.01em; padding-bottom:4px;'>
  TSP Analyzer
</div>
<div style='font-size:11px; color:#4a4a46; letter-spacing:0.1em; padding-bottom:20px; border-bottom:1px solid rgba(255,255,255,0.06); margin-bottom:20px;'>
  TSP PROBLEM — DASHBOARD DE RESULTADOS
</div>
""", unsafe_allow_html=True)

if not filtered:
    st.warning("No hay resultados con los filtros seleccionados.")
    st.stop()

# ── KPI strip: aggregate across filtered results ────────────────
#best_speedup  = max(filtered, key=lambda r: r["speedup_score"])
#best_eff      = max(filtered, key=lambda r: r["eficency_score"])
#min_time      = min(filtered, key=lambda r: r["Tp"])
#min_energy    = min(filtered, key=lambda r: r["energy"])
#min_dist      = min(filtered, key=lambda r: r["minimal_distance"])

#kpi_cols = st.columns(5)
#with kpi_cols[0]:
#    st.metric("Dist. mínima",   f"{min_dist['minimal_distance']:.0f}",
#              delta=f"{min_dist['instance_nodes']} nodos")
#with kpi_cols[1]:
#    st.metric("Mejor speedup",  f"{best_speedup['speedup_score']:.2f}×",
#              delta=f"{best_speedup['processors']}p · {best_speedup['instance_nodes']}n")
#with kpi_cols[2]:
#    st.metric("Mejor eficiencia", f"{best_eff['eficency_score']*100:.0f}%",
#              delta=f"{best_eff['processors']}p · {best_eff['instance_nodes']}n")
#with kpi_cols[3]:
#    st.metric("Menor tiempo Tₚ", f"{min_time['Tp']:.0f} ms",
#              delta=f"T₁={min_time['Ts']:.0f}ms · {min_time['processors']}p")
#with kpi_cols[4]:
#    st.metric("Menor energía",   f"{min_energy['energy']:.0f} J",
#              delta=f"{min_energy['instance_nodes']} nodos · {min_energy['processors']}p")
#
#st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# ── TABS ────────────────────────────────────────────────────────
tab_size, tab_summary = st.tabs([
    "◈  Instancia",
    "◫  Escalabilidad",
    #"☰  Tabla de datos",
])

# ══════════════════════════════════════
# TAB 1 — Instancia individual
# ══════════════════════════════════════
with tab_size:
    node_options = sorted(set(r["instance_nodes"] for r in filtered))
    col_sel1, col_sel2 = st.columns([1, 3])
    with col_sel1:
        selected_instance = st.selectbox("Instancia", node_options, format_func=lambda x: f"{x} nodos")

    # Get all records for selected instance (different processor counts)
    instance_results = sorted(
        [r for r in filtered if r["instance_nodes"] == selected_instance],
        key=lambda x: x["processors"]
    )
    proc_options = [r["processors"] for r in instance_results]
    with col_sel2:
        selected_proc = st.selectbox(
            "Procesadores",
            proc_options,
            format_func=lambda x: f"{x} procesadores",
            index=len(proc_options) - 1 if proc_options else 0,
        )

    result = next((r for r in instance_results if r["processors"] == selected_proc), instance_results[-1] if instance_results else None)
    if not result:
        st.warning("No hay datos para esta selección.")
        st.stop()

    st.markdown("---")

    # ── Row: KPIs for this instance ────────────────────────────
    r_cols = st.columns(4)
    with r_cols[0]:
        st.metric("Speedup S(p)",   f"{result['speedup_score']:.2f}×",
                  delta=f"T₁/Tₚ = {result['Ts']:.0f}/{result['Tp']:.0f}")
    with r_cols[1]:
        st.metric("Eficiencia E",   f"{result['eficency_score']*100:.1f}%",
                  delta=f"E = S/{result['processors']}")
    with r_cols[2]:
        st.metric("Tiempo Tₚ",      f"{result['Tp']:.1f} ms",
                  delta=f"T₁ = {result['Ts']:.1f} ms")
    with r_cols[3]:
        st.metric("Energía",        f"{result['energy']:.1f} kW",
                  delta=f"score: {result['consumption_score']:.1f}")

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ── Row: path + multi-processor chart ──────────────────────
    col_path, col_speedup , col_eficiency= st.columns([1, 1, 1])

    with col_path:
        st.markdown('<div class="section-header">Camino mínimo encontrado</div>', unsafe_allow_html=True)
        seq = result["secuence"]["sequence"]
        total_d = result["secuence"]["total_distance"]

        # Path graph visualization
        st.plotly_chart(build_graph_figure(seq), width="stretch", config={"displayModeBar": False})

        # Path badges
        badge_html = ""
        for i, node in enumerate(seq):
            badge_html += f'<span class="node-badge">#{node["id"]}<br><small style="color:#0F6E56">{node["distance"]:.1f}</small></span>'
            if i < len(seq) - 1:
                badge_html += '<span class="node-arrow">→</span>'
        st.markdown(
            f'<div style="padding:10px 0; line-height:2.4;">{badge_html}</div>'
            f'<div style="font-size:11px; color:#4a4a46; padding-top:6px;">Distancia total: <span style="color:#1D9E75">{total_d}</span></div>',
            unsafe_allow_html=True,
        )

    with col_speedup:
        #st.markdown('<div class="section-header">Métricas por procesadores — esta instancia</div>', unsafe_allow_html=True)
        #multi_fig = build_metrics_over_processors_chart(result)

        st.markdown('<div class="section-header">Speedup vs procesadores — todos los tamaños</div>', unsafe_allow_html=True)
        st.plotly_chart(build_speedup_chart(filtered),width="stretch", config={"displayModeBar": False})
        #if multi_fig:
        #    st.plotly_chart(multi_fig, width="stretch", config={"displayModeBar": False})
        #else:
        #    st.info("Solo hay un registro para esta instancia. Carga más datos de la API con distintos conteos de procesadores.")
    with col_eficiency:
        st.markdown('<div class="section-header">Eficiencia máxima por tamaño</div>', unsafe_allow_html=True)
        st.plotly_chart(build_efficiency_chart_by_proccesor(filtered), width="stretch", config={"displayModeBar": False})
# ══════════════════════════════════════
# TAB 2 — Escalabilidad comparativa
# ══════════════════════════════════════
with tab_summary:


    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    col_s1, col_s2 = st.columns(2)

    with col_s1:
        pass

    with col_s2:
        st.markdown('<div class="section-header">Tiempo serial vs paralelo</div>', unsafe_allow_html=True)
        st.plotly_chart(build_time_compare_chart(filtered), width="stretch", config={"displayModeBar": False})

    col_s3, col_s4 = st.columns(2)
    with col_s3:
        st.markdown('<div class="section-header">Consumo energético (max procesadores)</div>', unsafe_allow_html=True)
        st.plotly_chart(build_energy_chart(filtered), width="stretch", config={"displayModeBar": False})

    with col_s4:
        st.markdown('<div class="section-header">Distancia mínima por instancia</div>', unsafe_allow_html=True)
        st.plotly_chart(build_distance_chart(filtered), width="stretch", config={"displayModeBar": False})
