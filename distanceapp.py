import streamlit as st
import openrouteservice
from openrouteservice import optimization
import time
import folium
from streamlit_folium import st_folium

# --- PAGE CONFIG ---
st.set_page_config(page_title="Logistics Optimizer (Max 25)", layout="wide")

st.title("🚛 Multi-Stop Route Optimizer")
st.markdown("""
**Capacity:** Up to 25 stops per route.
**Engine:** VROOM Optimization (powered by Dijkstra/CH routing).
**Goal:** Minimize total fleet driving time.
""")

# --- SIDEBAR CONFIGURATION ---
st.sidebar.header("⚙️ Configuration")
# Password field hides the key for screenshots
api_key = st.sidebar.text_input("OpenRouteService API Key", type="password") 
gas_price = st.sidebar.number_input("Gas Price ($/gal)", value=2.859, step=0.01)
vehicle_mpg = st.sidebar.number_input("Vehicle MPG", value=18.0, step=0.5)

st.sidebar.info("💡 **Tip:** For best results with 10+ stops, ensure addresses include Zip Codes.")

# --- MAIN INPUT ---
st.subheader("📍 Delivery Locations")

# Default Michigan route (6 stops)
default_addresses = (
    "645 W Grand River Ave, East Lansing, MI 48823\n"
    "100 Renaissance Center, Detroit, MI 48243\n"
    "1100 N Main St, Ann Arbor, MI 48104\n"
    "250 Monroe Ave NW, Grand Rapids, MI 49503\n"
    "124 W Allegan St, Lansing, MI 48933\n"
    "300 S Union St, Traverse City, MI 49684"
)

# Using 'One per line' is easier for pasting from Excel than semicolons
raw_input = st.text_area(
    "Enter up to 25 addresses (One per line):", 
    value=default_addresses, 
    height=300,
    help="Paste a list of addresses here. The first address will be the START and END point."
)

# --- LOGIC FUNCTIONS ---
def get_optimized_route(key, addresses):
    client = openrouteservice.Client(key=key)
    
    # 1. GEO
