import streamlit as st
import paho.mqtt.client as mqtt
import time

# --- CONFIGURATION ---
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "elins/landslide/rafigila123" # <--- MUST MATCH ESP32 EXACTLY

# Set up the page layout
st.set_page_config(page_title="Landslide & Temp Monitor", page_icon="⛰️", layout="wide")
st.title("⛰️ Land Moisture, Aspect & Temperature Overseer (LMAO - PLS)")

# --- MQTT SETUP & BACKGROUND THREAD ---
@st.cache_resource
def init_mqtt():
    # Ditambahkan "suhu" dan "suhuBlynk" ke dalam dictionary
    data = {
        "pitch": 0.0, "roll": 0.0, "yaw": 0.0,
        "accX": 0.0, "accY": 0.0, "accZ": 0.0,
        "soil": 0.0,
        "suhu": 0.0, "suhuBlynk": 0.0
    }

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("✅ Connected to MQTT Broker successfully!")
            client.subscribe(MQTT_TOPIC)
            print(f"📡 Listening to topic: {MQTT_TOPIC}")
        else:
            print(f"❌ Failed to connect, return code {rc}")

    def on_message(client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8")
            print(f"Data masuk dari ESP32: {payload}")
            vals = payload.split(",")
            
            # Diubah menjadi >= 9 untuk menampung dua nilai suhu baru
            if len(vals) >= 9:
                data["pitch"] = float(vals[0])
                data["roll"] = float(vals[1])
                data["yaw"] = float(vals[2])
                data["accX"] = float(vals[3])
                data["accY"] = float(vals[4])
                data["accZ"] = float(vals[5])
                data["soil"] = float(vals[6])
                data["suhu"] = float(vals[7])       # <--- Nilai Suhu Asli (DHT)
                data["suhuBlynk"] = float(vals[8])  # <--- Nilai Suhu Kalibrasi
        except Exception as e:
            print(f"Error parsing data: {e}")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    
    client.loop_start() 
    return data

sensor_data = init_mqtt()

# --- LIVE UI LOOP ---
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

        # 2. DATA HUD (Diubah menjadi 4 kolom agar suhu memiliki tempat sendiri)
        col1, col2, col3, col4 = st.columns(4)

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
            soil_normalized = min(max(sensor_data["soil"] / 100.0, 0.0), 1.0)
            st.progress(soil_normalized)

        # Kolom Baru Khusus Nilai Suhu & Suhu Blynk
        with col4:
            st.subheader("🌡️ Temperature")
            st.metric("Suhu DHT (Asli)", f"{sensor_data['suhu']:.2f} °C")
            st.metric("Suhu Blynk (Kalibrasi)", f"{sensor_data['suhuBlynk']:.2f} °C")
            
    time.sleep(0.1)
