import requests
import streamlit as st
# ── API fetch ───────────────────────────────────────────────────
def fetch_from_api(url: str) -> tuple[bool, str]:
    try:
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        # Accept both a list of results or a dict with a "results" key
        if isinstance(data, dict):
            if "results" in data:
                data = data["results"]
            else:
                data = [data] # Envolvemos el objeto único en una lista
        if not isinstance(data, list) or len(data) == 0:
            return False, "La API devolvió datos vacíos o con formato incorrecto."
        st.session_state.results = data
        st.session_state.api_status = "live"
        return True, f"✓ {len(data)} resultado(s) cargados."
    except requests.exceptions.ConnectionError:
        st.session_state.api_status = "error"
        return False, "No se pudo conectar al servidor."
    except requests.exceptions.Timeout:
        st.session_state.api_status = "error"
        return False, "Tiempo de espera agotado (8s)."
    except Exception as e:
        st.session_state.api_status = "error"
        return False, f"Error: {str(e)}"