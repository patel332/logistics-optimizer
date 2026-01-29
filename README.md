# 🚛 Last-Mile Logistics Optimizer (Student Prototype)

A Python-based logistics tool that solves the **Traveling Salesperson Problem (TSP)** for small delivery fleets. Built using **Streamlit**, **OpenRouteService**, and the **VROOM** optimization engine.

## ⚠️ CRITICAL DISCLAIMER
**EDUCATIONAL USE ONLY. DO NOT USE FOR PRACTICAL NAVIGATION.**

This application is a student research prototype. It is **not** designed for real-world commercial logistics or active fleet management.
* **Data Reliability:** The tool relies on open-source data (OpenStreetMap) which may not reflect real-time traffic, road closures, construction, or legal truck restrictions.
* **Liability:** The developer assumes no liability for any incidents, delays, or damages resulting from the use of this software.
* **API Limits:** This tool uses the free tier of OpenRouteService and is subject to rate limiting.

## 🚀 Features
* **TSP Solver:** Optimizes the sequence of up to 20 stops to minimize total drive time.
* **Interactive Map:** Visualizes the route topology using `Folium`.
* **Savings Analysis:** Calculates "Time Saved" by comparing the user's input sequence against the optimized VROOM sequence.
* **Turn-by-Turn Directions:** Generates a detailed navigation manifest.

## 🛠️ Tech Stack
* **Frontend:** Streamlit (Python)
* **Routing Matrix:** OpenRouteService API (Dijkstra / Contraction Hierarchies)
* **Optimization Engine:** VROOM (TSP Heuristics)
* **Visualization:** Folium

## 📊 Benchmarks
Tested against commercial routing standards on 20-stop loops:
* **Variance:** Routes match commercial estimates within **~2%**.
* **Processing Time:** <2 seconds for standard loops.

## ⚙️ How to Run Locally

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up API Key**
    * Get a free API key from [OpenRouteService.org](https://openrouteservice.org/).
    * Paste it into the app sidebar when running.

4.  **Run the App**
    ```bash
    streamlit run distanceapp.py
    ```

## 🤝 Credits
* Routing logic provided by [OpenRouteService](https://openrouteservice.org).
* Map data © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors.
* Optimization logic based on the [VROOM Project](http://vroom-project.org/).
