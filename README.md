# 📊 Dashboard HPC – Visualización de Resultados

Este proyecto ofrece una interfaz de usuario desarrollada en **Python** utilizando **Streamlit**.  
Funciona como cliente que consume datos del backend y los transforma en **inteligencia visual interactiva**.  
Actualmente, la aplicación funciona con **datos de prueba** (sin conexión a la API).

---

## ⚙️ Instalación

1. Clona este repositorio.  
2. Instala las dependencias listadas en `requirements.txt`:

```bash

py -m venv venv

.\venv\Scripts\activate

pip install -r requirements.txt

```

## 🚀 Ejecución

Para iniciar la aplicación:

```bash
streamlit run main.py

```

## 🧩 Funcionalidades

* **Consumo de API (si el backend no está definido usa datos de prueba):**  
Uso de la librería requests para conectarse al endpoint en Go y extraer datos en formato JSON.

* **Procesamiento y Filtros:** 
Con pandas se manipulan los datos y se implementan filtros que permiten aislar resultados por:

    * Tamaño del grafo (nodos).

* **Visualización (Plotly & Componentes UI):**
Se emplea plotly.graph_objects para generar gráficos interactivos de alto nivel:

    * ⚡ Curvas de escalabilidad (Speedup vs. Procesadores).

    * 📉 Gráficos de degradación de la eficiencia.

    * ⏱️ Comparativas de tiempo de ejecución.


## 📌 Estado Actual

* ✅ Interfaz funcional con datos de prueba.

* 🔄 Conexión a la API en desarrollo.

* 🛠️ Gráficos de tiempo,escalabilidad fuerte.
