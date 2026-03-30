import streamlit as st
import paho.mqtt.client as mqtt
import time

# --- CONFIGURATION ---
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "elins/landslide/monitor123" # <--- MUST MATCH ESP32 EXACTLY

# Set up the page layout
st.set_page_config(page_title="Landslide Monitor", page_icon="⛰️", layout="wide")
st.title("⛰️ Wireless Landslide Early Warning System")

# --- MQTT SETUP & BACKGROUND THREAD ---
# We use @st.cache_resource so Streamlit doesn't disconnect/reconnect every millisecond
@st.cache_resource
def init_mqtt():
    # This dictionary holds the live data. The background thread updates it, 
    # and the Streamlit UI reads from it.
    data = {
        "pitch": 0.0, "roll": 0.0, "yaw": 0.0,
        "accX": 0.0, "accY": 0.0, "accZ": 0.0,
        "soil": 0.0
    }

    def on_connect(client, userdata, flags, rc):
        client.subscribe(MQTT_TOPIC)

    def on_message(client, userdata, msg):
        try:
            # Decode the comma-separated string from the ESP32
            payload = msg.payload.decode("utf-8")
            vals = payload.split(",")
            
            if len(vals) >= 7:
                data["pitch"] = float(vals[0])
                data["roll"] = float(vals[1])
                data["yaw"] = float(vals[2])
                data["accX"] = float(vals[3])
                data["accY"] = float(vals[4])
                data["accZ"] = float(vals[5])
                data["soil"] = float(vals[6])
        except Exception as e:
            pass

    # Initialize the MQTT Client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    
    # loop_start() runs the network code in the background automatically!
    client.loop_start() 
    return data

# Grab the live data dictionary
sensor_data = init_mqtt()

# --- LIVE UI LOOP ---
# Create an empty container that we will overwrite rapidly
placeholder = st.empty()

while True:
    with placeholder.container():
        
        # 1. DANGER ALERT LOGIC
        is_critical = (sensor_data["soil"] > 80 and (abs(sensor_data["pitch"]) > 5 or abs(sensor_data["roll"]) > 5)) or \
                      (abs(sensor_data["pitch"]) > 15 or abs(sensor_data["roll"]) > 15)

        if is_critical:
            st.error("⚠️ CRITICAL ALERT: EVACUATE AREA! High Landslide Risk Detected.", icon="🚨")
        else:
            st.success("✅ Ground is stable. Monitoring active.", icon="📡")

        st.markdown("---")

        # 2. DATA HUD (Split into 3 neat columns)
        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("📐 Ground Tilt")
            st.metric("Pitch", f"{sensor_data['pitch']:.2f}°")
            st.metric("Roll", f"{sensor_data['roll']:.2f}°")

        with col2:
            st.subheader("💥 Impact Forces")
            st.metric("Acc X", f"{int(sensor_data['accX'])}")
            st.metric("Acc Y", f"{int(sensor_data['accY'])}")
            st.metric("Acc Z", f"{int(sensor_data['accZ'])}")

        with col3:
            st.subheader("💧 Soil Saturation")
            st.metric("Moisture", f"{int(sensor_data['soil'])}%")
            
            # Streamlit progress bars require a float strictly between 0.0 and 1.0
            soil_normalized = min(max(sensor_data["soil"] / 100.0, 0.0), 1.0)
            st.progress(soil_normalized)
            
    # Pause for 100ms so we don't melt your laptop's CPU, then loop and redraw!
    time.sleep(0.1)