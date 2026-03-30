import mqtt.*;

MQTTClient client;

float pitch, roll, yaw;
float rawX, rawY, rawZ;
float soilMoisture = 0;

void setup() {
  size(1000, 600, P3D); 
  
  // Connect to the public broker
  client = new MQTTClient(this);
  client.connect("mqtt://broker.hivemq.com", "processing_dashboard_" + int(random(1000)));
  
  // Subscribe to your specific data stream
  // CHANGE THIS TO MATCH YOUR ESP32 TOPIC!
  client.subscribe("elins/landslide/rafigila123"); 
}

void draw() {
  background(20);
  
  // --- 1. THE 3D VISUALIZER (Kiri) ---
  pushMatrix();
    translate(width/3, height/2, 0);
    lights();
    rotateX(radians(-pitch));
    rotateZ(radians(-roll));
    rotateY(radians(yaw));
    fill(100, 200, 100); 
    box(250, 40, 150);
  popMatrix();

  // --- 2. THE DATA HUD (Kanan) ---
  hint(DISABLE_DEPTH_TEST); 
  fill(30);
  rect(width*0.6, 0, width, height); 
  
  textSize(24);
  fill(255);
  text("WIRELESS LANDSLIDE MONITOR", width*0.65, 50);
  
  textSize(18);
  fill(0, 255, 0);
  text("GROUND TILT (Angles)", width*0.65, 110);
  fill(200);
  text("Pitch: " + nf(pitch, 0, 2) + "°", width*0.65, 140);
  text("Roll:  " + nf(roll, 0, 2) + "°", width*0.65, 170);
  
  fill(255, 100, 0);
  text("IMPACT FORCES", width*0.65, 230);
  fill(200);
  text("Acc X: " + int(rawX), width*0.65, 260);
  text("Acc Y: " + int(rawY), width*0.65, 290);
  text("Acc Z: " + int(rawZ), width*0.65, 320);

  fill(50, 150, 255);
  text("SOIL SATURATION", width*0.65, 380);
  fill(200);
  text("Moisture: " + int(soilMoisture) + "%", width*0.65, 410);
  
  fill(50); 
  rect(width*0.65, 425, 200, 20);
  fill(50, 150, 255); 
  float barWidth = map(soilMoisture, 0, 100, 0, 200);
  rect(width*0.65, 425, barWidth, 20);
  
  if ((soilMoisture > 80 && (abs(pitch) > 5 || abs(roll) > 5)) || abs(pitch) > 15 || abs(roll) > 15) {
     fill(255, 0, 0);
     textSize(30);
     text("⚠️ CRITICAL ALERT!", width*0.65, 520);
     text("EVACUATE AREA", width*0.65, 550);
  }
  hint(ENABLE_DEPTH_TEST);
}

// This runs automatically every time a message arrives from the internet!
void messageReceived(String topic, byte[] payload) {
  String inString = new String(payload);
  float[] data = float(split(trim(inString), ','));
  
  if (data.length >= 7) {
    if (Float.isNaN(data[0])) return; 
    
    pitch = data[0]; roll = data[1]; yaw = data[2];
    rawX = data[3];  rawY = data[4];  rawZ = data[5];
    soilMoisture = data[6]; 
  }
}
