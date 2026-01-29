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
    
    # 1. GEOCODING LOOP
    coords = []
    valid_addresses = []
    
    # Create a progress bar for the batch
    progress_text = "📍 Geocoding addresses..."
    my_bar = st.progress(0, text=progress_text)
    
    for i, addr in enumerate(addresses):
        try:
            # Rate limiting: 40 req/min = ~1.5 sec pause per request to be safe
            time.sleep(1.2) 
            res = client.pelias_search(text=addr, size=1)
            
            if res['features']:
                coords.append(res['features'][0]['geometry']['coordinates'])
                valid_addresses.append(addr)
            else:
                st.toast(f"⚠️ Skipped: Could not find '{addr}'", icon="❌")
                
        except Exception as e:
            st.error(f"API Error on '{addr}': {e}")
            return None, None, None, None
        
        # Update progress
        percent_complete = int(((i + 1) / len(addresses)) * 100)
        my_bar.progress(percent_complete, text=f"📍 Geocoding {i+1}/{len(addresses)}: {addr[:30]}...")
    
    my_bar.empty() # Clear bar when done

    if len(coords) < 2:
        st.error("Need at least 2 valid addresses to optimize.")
        return None, None, None, None

    # --- NEW: CALCULATE ORIGINAL (BAD) ROUTE METRICS ---
    # We ask for directions strictly in the order the user pasted them to compare later
    original_summary = {}
    try:
        # Round-trip logic for original: Add start point to end if not already there
        original_coords = coords.copy()
        original_coords.append(coords[0]) 
        
        orig_res = client.directions(
            coordinates=original_coords,
            profile='driving-car',
            format='json' # We only need the numbers here, not the full map geometry
        )
        original_summary = orig_res['routes'][0]['summary']
    except Exception as e:
        print(f"Could not calc original route: {e}")

    # 2. OPTIMIZATION (VROOM Engine)
    with st.spinner(f"🔄 Optimizing sequence for {len(coords)} stops..."):
        # Vehicle starts and ends at the first address (Depot)
        vehicle = optimization.Vehicle(
            id=0, 
            profile='driving-car', 
            start=coords[0], 
            end=coords[0]
        )
        # Jobs are the remaining addresses
        jobs = [optimization.Job(id=i, location=loc) for i, loc in enumerate(coords[1:])]
        
        try:
            opt_res = client.optimization(jobs=jobs, vehicles=[vehicle])
            steps = opt_res['routes'][0]['steps']
            
            # Reconstruct ordered lists
            ordered_coords = [coords[0]] # Start
            stop_order_display = []
            
            for step in steps:
                if step['type'] == 'job':
                    # Job ID maps to index in coords list (+1 because 0 is depot)
                    idx = step['id'] + 1
                    ordered_coords.append(coords[idx])
                    stop_order_display.append(valid_addresses[idx])
            
            ordered_coords.append(coords[0]) # Return to Start
            
        except Exception as e:
            st.error(f"Optimization failed: {e}")
            return None, None, None, None

    # 3. DIRECTIONS (Exact Geometry for Optimized Path)
    with st.spinner("📏 Drawing final route path..."):
        try:
            route_res = client.directions(
                coordinates=ordered_coords,
                profile='driving-car',
                format='geojson'
            )
            # Return original_summary as the 4th value
            return route_res, stop_order_display, ordered_coords, original_summary 
        except Exception as e:
            st.error(f"Directions failed: {e}")
            return None, None, None, None

# --- RUN BUTTON ---
if st.button("🚀 Optimize Route", type="primary"):
    if not api_key:
        st.error("⚠️ Please enter your API Key in the sidebar.")
    else:
        # Split by newlines so user can paste from Excel
        addr_list = [line.strip() for line in raw_input.split('\n') if line.strip()]
        
        if len(addr_list) > 25:
            st.warning(f"⚠️ You entered {len(addr_list)} locations. The Free Tier limit is usually 50, but we cap at 25 for stability.")
        
        # UPDATED: Catching the 4th return value (orig_stats)
        geojson_data, stop_order, ordered_coords, orig_stats = get_optimized_route(api_key, addr_list)
        
        if geojson_data:
            # Save to Session State so map persists after interaction
            st.session_state['results'] = {
                'geojson': geojson_data,
                'stops': stop_order,
                'coords': ordered_coords,
                'start_addr': addr_list[0],
                'orig_stats': orig_stats
            }

# --- DISPLAY RESULTS ---
if 'results' in st.session_state:
    data = st.session_state['results']
    geojson_data = data['geojson']
    stop_order = data['stops']
    ordered_coords = data['coords']
    orig_stats = data.get('orig_stats', {})
    
    st.success(f"✅ Route Optimized for {len(stop_order) + 1} Locations!")
    
    # Extract Metrics
    props = geojson_data['features'][0]['properties']
    dist_km = props['summary']['distance'] / 1000
    duration = props['summary']['duration']
    
    fuel_cost = (dist_km * 0.621371 / vehicle_mpg) * gas_price
    
    # --- CALCULATE SAVINGS ---
    saved_time_min = 0
    saved_dist_km = 0
    pct_saved = 0.0
    
    if orig_stats:
        orig_dur = orig_stats.get('duration', 0)
        orig_dist = orig_stats.get('distance', 0) / 1000
        
        saved_time_sec = orig_dur - duration
        saved_time_min = int(saved_time_sec / 60)
        saved_dist_km = orig_dist - dist_km
        
        if orig_dur > 0:
            pct_saved = (saved_time_sec / orig_dur) * 100

    # Render Savings Banner (Like RouteXL)
    if saved_time_min > 5: # Only show if significant savings (> 5 mins)
        st.success(f"📉 **Optimization Success:** You saved **{saved_time_min // 60}h {saved_time_min % 60}m** ({pct_saved:.1f}%) compared to the original order!")
    
    hrs = int(duration // 3600)
    mins = int((duration % 3600) // 60)
    
    # --- METRICS ROW ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Distance", f"{dist_km:.1f} km", delta=f"-{saved_dist_km:.1f} km", delta_color="inverse")
    c2.metric("Driving Time", f"{hrs}h {mins}m", delta=f"-{saved_time_min} min", delta_color="inverse")
    c3.metric("Est. Fuel Cost", f"${fuel_cost:.2f}")
    c4.metric("Stops", len(stop_order))
    
    # --- INTERACTIVE MAP ---
    st.subheader("🗺️ Route Visualization")
    start_coords = geojson_data['features'][0]['geometry']['coordinates'][0]
    
    m = folium.Map(location=[start_coords[1], start_coords[0]], zoom_start=9)
    
    # Route Line
    folium.GeoJson(
        geojson_data,
        name="Optimized Path",
        style_function=lambda x: {'color': '#2A82DA', 'weight': 6, 'opacity': 0.8}
    ).add_to(m)
    
    # Start Marker
    folium.Marker(
        [start_coords[1], start_coords[0]],
        popup=f"START: {data['start_addr']}",
        icon=folium.Icon(color="green", icon="play", prefix="fa")
    ).add_to(m)
    
    # --- Add Markers for Each Stop ---
    for i, stop_name in enumerate(stop_order):
        # ordered_coords[0] is Start, so stop #1 is at index 1
        stop_coord = ordered_coords[i+1]
        
        folium.Marker(
            [stop_coord[1], stop_coord[0]],
            popup=f"STOP {i+1}: {stop_name}",
            icon=folium.Icon(color="blue", icon="box", prefix="fa")
        ).add_to(m)

    # Render Map
    st_folium(m, width=None, height=500)
    
    # --- TEXT INSTRUCTIONS ---
    with st.expander("📋 View Turn-by-Step Sequence", expanded=True):
        st.markdown(f"**1. START:** {data['start_addr']}")
        for i, stop in enumerate(stop_order):
            st.markdown(f"**{i+2}. STOP:** {stop}")
        st.markdown(f"**{len(stop_order)+2}. FINISH:** Return to Start")
