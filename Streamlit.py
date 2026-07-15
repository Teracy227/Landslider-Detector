import streamlit as st
import paho.mqtt.client as mqtt
import time

# --- KONFIGURASI MQTT ---
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
TOPIC_MPU = "elins/landslide/rafigila123"  # Topik ESP32 Pertama (Tilt, Acc, Soil)
TOPIC_SUHU = "elins/landslide/suhu"        # Topik ESP32 Kedua (Greenhouse / DHT)

# Konfigurasi Halaman Streamlit
st.set_page_config(page_title="Landslide & Temp Monitor", page_icon="⛰️", layout="wide")
st.title("⛰️ Land Moisture, Aspect & Temperature Overseer (LMAO - PLS)")

# --- SETUP MQTT & THREAD BACKGROUND ---
@st.cache_resource
def init_mqtt():
    # Dictionary utama untuk menampung seluruh data dari kedua ESP32
    data = {
        "pitch": 0.0, "roll": 0.0, "yaw": 0.0,
        "accX": 0.0, "accY": 0.0, "accZ": 0.0,
        "soil": 0.0,
        "suhu": 0.0, "suhuBlynk": 0.0
    }

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("✅ Berhasil terhubung ke Broker MQTT!")
            # Langsung berlangganan (subscribe) ke dua topik sekaligus
            client.subscribe([(TOPIC_MPU, 0), (TOPIC_SUHU, 0)])
            print(f"📡 Mendengarkan topik:\n   1. {TOPIC_MPU}\n   2. {TOPIC_SUHU}")
        else:
            print(f"❌ Gagal terhubung, kode error: {rc}")

    def on_message(client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8")
            vals = payload.split(",")
            
            # 1. Parsing data dari ESP32 Pertama (7 Data MPU & Soil)
            if msg.topic == TOPIC_MPU and len(vals) >= 7:
                data["pitch"] = float(vals[0])
                data["roll"] = float(vals[1])
                data["yaw"] = float(vals[2])
                data["accX"] = float(vals[3])
                data["accY"] = float(vals[4])
                data["accZ"] = float(vals[5])
                data["soil"] = float(vals[6])
                print(f"[MPU] Data diperbarui: Pitch={data['pitch']}, Soil={data['soil']}%")
            
            # 2. Parsing data dari ESP32 Kedua (2 Data Suhu Greenhouse)
            elif msg.topic == TOPIC_SUHU and len(vals) >= 2:
                data["suhu"] = float(vals[0])
                data["suhuBlynk"] = float(vals[1])
                print(f"[SUHU] Data diperbarui: Suhu={data['suhu']}C, Blynk={data['suhuBlynk']}C")
                
        except Exception as e:
            print(f"⚠️ Error parsing data dari topik {msg.topic}: {e}")

    # Inisialisasi Klien MQTT (Mendukung Paho MQTT v2.0+)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    
    # Menjalankan loop jaringan MQTT di background secara otomatis
    client.loop_start() 
    return data

# Ambil referensi data sensor yang berjalan secara live di background
sensor_data = init_mqtt()

# --- LIVE UI RENDERING LOOP ---
placeholder = st.empty()

while True:
    with placeholder.container():
        
        # 1. LOGIKA SISTEM PERINGATAN DINI (EARLY WARNING SYSTEM)
        is_critical = (sensor_data["soil"] > 80 and (abs(sensor_data["pitch"]) > 5 or abs(sensor_data["roll"]) > 5)) or \
                      (abs(sensor_data["pitch"]) > 15 or abs(sensor_data["roll"]) > 15)

        if is_critical:
            st.error("⚠️ CRITICAL ALERT: EVACUATE AREA! High Landslide Risk Detected.", icon="🚨")
        else:
            st.success("✅ Ground is stable. Monitoring active.", icon="📡")

        st.markdown("---")

        # 2. DATA HUD (Dibuat menjadi 4 kolom untuk menampung suhu)
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.subheader("📐 Ground Tilt")
            st.metric("Pitch", f"{sensor_data['pitch']:.2f}°")
            st.metric("Roll", f"{sensor_data['roll']:.2f}°")
            st.metric("Yaw", f"{sensor_data['yaw']:.2f}°")

        with col2:
            st.subheader("💥 Impact Forces")
            st.metric("Acc X", f"{int(sensor_data['accX'])}")
            st.metric("Acc Y", f"{int(sensor_data['accY'])}")
            st.metric("Acc Z", f"{int(sensor_data['accZ'])}")

        with col3:
            st.subheader("💧 Soil Saturation")
            st.metric("Moisture", f"{int(sensor_data['soil'])}%")
            # Progress bar Streamlit membutuhkan nilai float strictly di antara 0.0 dan 1.0
            soil_normalized = min(max(sensor_data["soil"] / 100.0, 0.0), 1.0)
            st.progress(soil_normalized)

        with col4:
            st.subheader("🌡️ Temperature")
            st.metric("Suhu DHT (Asli)", f"{sensor_data['suhu']:.2f} °C")
            st.metric("Suhu Blynk (Kalibrasi)", f"{sensor_data['suhuBlynk']:.2f} °C")
            
    # Jeda 100ms agar CPU tidak bekerja terlalu berat saat melakukan render ulang
    time.sleep(0.1)
