#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <MPU6050_light.h>

// --- Wi-Fi & MQTT Settings ---
const char* ssid = "POCO M3";         // <--- CHANGE THIS
const char* password = "pzkmpfwgnviii"; // <--- CHANGE THIS
const char* mqtt_server = "broker.hivemq.com";
const char* mqtt_topic = "elins/landslide/rafigila123"; // <--- Make this unique!

WiFiClient espClient;
PubSubClient client(espClient);

// --- Sensor Settings ---
MPU6050 mpu(Wire);
const int SOIL_PIN = 34;
int valueDry = 2540; // Your custom dry calibration
int valueWet = 910;  // Your custom wet calibration

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
}

void reconnect() {
  // Loop until we're reconnected to the MQTT broker
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Create a random client ID
    String clientId = "ESP32Client-";
    clientId += String(random(0, 10000));
    
    if (client.connect(clientId.c_str())) {
      Serial.println("connected to broker!");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  
  // 1. Setup Sensors
  Wire.begin(21, 22);
  byte status = mpu.begin();
  while(status != 0){ } 
  delay(1000);
  mpu.calcOffsets(true,true); 
  
  // 2. Setup Network
  setup_wifi();
  client.setServer(mqtt_server, 1883);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop(); // Keep MQTT connection alive

  mpu.update();

  // 1. Read and Smooth Soil Data
  long soilSum = 0;
  for (int i = 0; i < 20; i++) {
    soilSum += analogRead(SOIL_PIN);
    delay(2);
  }
  int avgSoilRaw = soilSum / 20;
  int soilPercent = map(avgSoilRaw, valueDry, valueWet, 0, 100);
  soilPercent = constrain(soilPercent, 0, 100);

  // 2. Package all data into one comma-separated String
  String payload = String(mpu.getAngleX()) + "," + 
                   String(mpu.getAngleY()) + "," + 
                   String(mpu.getAngleZ()) + "," + 
                   String(mpu.getAccX() * 16384) + "," + 
                   String(mpu.getAccY() * 16384) + "," + 
                   String(mpu.getAccZ() * 16384) + "," + 
                   String(soilPercent);

  // 3. Publish to the Internet!
  client.publish(mqtt_topic, payload.c_str());
  
  // Print to Serial monitor just so we can watch it work locally
  Serial.println(payload);
  
  delay(50); // Send data roughly 20 times a second
}