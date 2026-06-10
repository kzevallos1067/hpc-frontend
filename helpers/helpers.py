import streamlit as st

import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
import math
import json
from typing import Optional
import pandas as pd


# ── Plotly dark template ────────────────────────────────────────
DARK_LAYOUT = dict(
    paper_bgcolor="#111318",
    plot_bgcolor="#0b0c0e",
    font=dict(family="JetBrains Mono", color="#8b8a82", size=11),
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.05)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.05)"),
    margin=dict(l=50, r=20, t=36, b=40),
)
ACCENT_COLORS = ["#1D9E75", "#378ADD", "#EF9F27", "#D4537E", "#7F77DD"]


# ── Helpers ─────────────────────────────────────────────────────
def get_results() -> list[dict]:
    return st.session_state.results

def status_badge() -> str:
    s = st.session_state.api_status
    if s == "live":  return "🟢 EN VIVO"
    if s == "error": return "🔴 ERROR"
    return "🟡 DEMO"

def fmt_float(v, decimals=2) -> str:
    try:
        return f"{float(v):.{decimals}f}"
    except Exception:
        return str(v)

def build_graph_figure(sequence: list[dict]) -> go.Figure:
    """Build a Plotly figure showing the path as a linear chain graph."""
    n = len(sequence)
    if n == 0:
        return go.Figure()

    # Arrange nodes in a horizontal chain with slight vertical jitter
    angles = [math.pi * i / max(n - 1, 1) for i in range(n)]
    xs = [math.cos(a) * 4 for a in angles]
    ys = [math.sin(a) * 1.5 for a in angles]

    # Edges
    edge_x, edge_y = [], []
    for i in range(n - 1):
        edge_x += [xs[i], xs[i+1], None]
        edge_y += [ys[i], ys[i+1], None]

    node_ids   = [str(node["id"]) for node in sequence]
    node_dists = [node["distance"] for node in sequence]
    hover_text = [f"Nodo {node['id']}<br>Dist acumulada: {node['distance']}" for node in sequence]

    fig = go.Figure()

    # Draw edges
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        mode="lines",
        line=dict(color="#1D9E75", width=2.5),
        hoverinfo="none",
        showlegend=False,
    ))

    # Draw nodes
    fig.add_trace(go.Scatter(
        x=xs, y=ys,
        mode="markers+text",
        marker=dict(
            size=36,
            color=node_dists,
            colorscale=[[0, "#0F6E56"], [1, "#1D9E75"]],
            line=dict(color="#1D9E75", width=2),
            showscale=True,
            colorbar=dict(
                title=dict(
                    text="dist.", 
                    font=dict(family="JetBrains Mono", size=10, color="#8b8a82")
                ), 
                thickness=10, 
                len=0.6,
                tickfont=dict(family="JetBrains Mono", size=10, color="#8b8a82")
            ),
        ),
        text=node_ids,
        textfont=dict(family="JetBrains Mono", size=12, color="#e8e6df"),
        textposition="middle center",
        hovertext=hover_text,
        hoverinfo="text",
        showlegend=False,
    ))

    fig.update_layout(
        DARK_LAYOUT,
        height=220,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(l=10, r=60, t=10, b=10),
    )
    return fig

def build_speedup_chart(results: list[dict]) -> go.Figure:
    fig = go.Figure()
    nodes_seen = sorted(set(r["instance_nodes"] for r in results))
    colors = ACCENT_COLORS

    for i, nodes in enumerate(nodes_seen):
        subset = sorted([r for r in results if r["instance_nodes"] == nodes], key=lambda x: x["processors"])
        if not subset:
            continue
        procs   = [r["processors"] for r in subset]
        speedup = [r["speedup_score"] for r in subset]
        fig.add_trace(go.Scatter(
            x=procs, y=speedup,
            mode="lines+markers",
            name=f"{nodes} nodos",
            line=dict(color=colors[i % len(colors)], width=2),
            marker=dict(size=7, color=colors[i % len(colors)]),
        ))

    # Ideal speedup reference
    if results:
        max_proc = max(r["processors"] for r in results)
        fig.add_trace(go.Scatter(
            x=[1, max_proc], y=[1, max_proc],
            mode="lines",
            name="ideal",
            line=dict(color="rgba(255,255,255,0.15)", width=1, dash="dash"),
        ))

    fig.update_layout(
        DARK_LAYOUT,
        xaxis=dict(**DARK_LAYOUT["xaxis"], title="procesadores", type="log"),
        yaxis=dict(**DARK_LAYOUT["yaxis"], title="speedup S(p)"),
        legend=dict(font=dict(family="JetBrains Mono", size=10, color="#8b8a82"), bgcolor="rgba(0,0,0,0)"),
        height=340,
    )
    return fig

def build_efficiency_chart(results: list[dict]) -> go.Figure:
    nodes_seen = sorted(set(r["instance_nodes"] for r in results))
    eff_values = []
    for nodes in nodes_seen:
        subset = [r for r in results if r["instance_nodes"] == nodes]
        if subset:
            best = max(subset, key=lambda x: x["processors"])
            eff_values.append(round(best["eficency_score"] * 100, 1))

    fig = go.Figure(go.Bar(
        x=[f"{n}n" for n in nodes_seen],
        y=eff_values,
        marker=dict(color=ACCENT_COLORS[:len(nodes_seen)], opacity=0.85),
        text=[f"{v}%" for v in eff_values],
        textfont=dict(family="JetBrains Mono", size=11, color="#e8e6df"),
        textposition="outside",
    ))
    fig.update_layout(
        DARK_LAYOUT,
        xaxis=dict(**DARK_LAYOUT["xaxis"], title="tamaño"),
        yaxis=dict(**DARK_LAYOUT["yaxis"], title="eficiencia %", range=[0, 110]),
        height=300,
        showlegend=False,
    )
    return fig

def build_efficiency_chart_by_proccesor(results: list[dict]) -> go.Figure:
    fig = go.Figure()

    # Ordenar por número de procesadores
    subset = sorted(results, key=lambda x: x["processors"])

    if subset:
        procs = [r["processors"] for r in subset]
        eff   = [round(r["eficency_score"] * 100, 1) for r in subset]

        fig.add_trace(go.Scatter(
            x=procs, y=eff,
            mode="lines+markers",
            name=f"{subset[0]['instance_nodes']} nodos",
            line=dict(color=ACCENT_COLORS[0], width=2),
            marker=dict(size=7, color=ACCENT_COLORS[0]),
            text=[f"{v}%" for v in eff],
            textposition="top center",
            textfont=dict(family="JetBrains Mono", size=11, color="#e8e6df"),
        ))

    fig.update_layout(
        DARK_LAYOUT,
        xaxis=dict(**DARK_LAYOUT["xaxis"], title="procesadores"),  # ← sin type="log"
        yaxis=dict(**DARK_LAYOUT["yaxis"], title="eficiencia %", range=[0, 110]),
        legend=dict(font=dict(family="JetBrains Mono", size=10, color="#8b8a82"), bgcolor="rgba(0,0,0,0)"),
        height=340,
    )

    return fig

def build_energy_chart(results: list[dict]) -> go.Figure:
    nodes_seen = sorted(set(r["instance_nodes"] for r in results))
    energies = []
    for nodes in nodes_seen:
        subset = [r for r in results if r["instance_nodes"] == nodes]
        if subset:
            best = max(subset, key=lambda x: x["processors"])
            energies.append(best["energy"])

    fig = go.Figure(go.Scatter(
        x=nodes_seen, y=energies,
        mode="lines+markers",
        line=dict(color="#D4537E", width=2.5),
        marker=dict(size=8, color="#D4537E"),
        fill="tozeroy",
        fillcolor="rgba(212,83,126,0.10)",
    ))
    fig.update_layout(
        DARK_LAYOUT,
        xaxis=dict(**DARK_LAYOUT["xaxis"], title="nodos"),
        yaxis=dict(**DARK_LAYOUT["yaxis"], title="Joules"),
        height=300,
        showlegend=False,
    )
    return fig

def build_time_compare_chart(results: list[dict]) -> go.Figure:
    nodes_seen = sorted(set(r["instance_nodes"] for r in results))
    ts_vals, tp_vals = [], []
    for nodes in nodes_seen:
        subset = [r for r in results if r["instance_nodes"] == nodes]
        if subset:
            best = max(subset, key=lambda x: x["processors"])
            ts_vals.append(best["Ts"])
            tp_vals.append(best["Tp"])

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Serial T₁",    x=nodes_seen, y=ts_vals, marker_color="#378ADD", opacity=0.8))
    fig.add_trace(go.Bar(name="Paralelo Tₚ",  x=nodes_seen, y=tp_vals, marker_color="#1D9E75", opacity=0.85))
    fig.update_layout(
        DARK_LAYOUT,
        barmode="group",
        xaxis=dict(**DARK_LAYOUT["xaxis"], title="nodos"),
        yaxis=dict(**DARK_LAYOUT["yaxis"], title="tiempo (ms)"),
        legend=dict(font=dict(family="JetBrains Mono", size=10, color="#8b8a82"), bgcolor="rgba(0,0,0,0)"),
        height=300,
    )
    return fig

def build_distance_chart(results: list[dict]) -> go.Figure:
    nodes_seen = sorted(set(r["instance_nodes"] for r in results))
    dists = []
    for nodes in nodes_seen:
        subset = [r for r in results if r["instance_nodes"] == nodes]
        if subset:
            dists.append(subset[0]["minimal_distance"])

    fig = go.Figure(go.Bar(
        x=nodes_seen, y=dists,
        marker=dict(color=ACCENT_COLORS[:len(nodes_seen)], opacity=0.85),
        text=[str(d) for d in dists],
        textfont=dict(family="JetBrains Mono", size=11, color="#e8e6df"),
        textposition="outside",
    ))
    fig.update_layout(
        DARK_LAYOUT,
        xaxis=dict(**DARK_LAYOUT["xaxis"], title="nodos"),
        yaxis=dict(**DARK_LAYOUT["yaxis"], title="dist. mínima"),
        height=300,
        showlegend=False,
    )
    return fig

def build_metrics_over_processors_chart(result: dict) -> go.Figure:
    """For a single instance, show speedup and efficiency across processors if multiple records exist."""
    results = get_results()
    same = sorted(
        [r for r in results if r["instance_nodes"] == result["instance_nodes"]],
        key=lambda x: x["processors"]
    )
    if len(same) < 2:
        return None

    procs = [r["processors"] for r in same]
    speedups = [r["speedup_score"] for r in same]
    #effs = [r["eficency_score"] * 100 for r in same]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=procs, y=speedups, mode="lines+markers", name="Speedup",
                             line=dict(color="#1D9E75", width=2), marker=dict(size=7)))
    #fig.add_trace(go.Scatter(x=procs, y=effs, mode="lines+markers", name="Eficiencia %",
    #                         line=dict(color="#378ADD", width=2, dash="dot"), marker=dict(size=7),
    #                         yaxis="y2"))
    fig.update_layout(
        DARK_LAYOUT,
        height=260,
        xaxis=dict(**DARK_LAYOUT["xaxis"], title="procesadores"),
        yaxis=dict(**DARK_LAYOUT["yaxis"], title="speedup"),
        #yaxis2=dict(overlaying="y", side="right", title="eficiencia %",
        #            gridcolor="rgba(255,255,255,0.03)", tickfont=dict(color="#8b8a82")),
        legend=dict(font=dict(family="JetBrains Mono", size=10, color="#8b8a82"), bgcolor="rgba(0,0,0,0)"),
    )
    return fig
