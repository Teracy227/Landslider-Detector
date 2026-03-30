import processing.serial.*;

Serial myPort;
float pitch, roll, yaw;
float rawX, rawY, rawZ;
float soilMoisture = 0; // Variabel baru untuk tanah

void setup() {
  size(1000, 600, P3D); 
  printArray(Serial.list());
  myPort = new Serial(this, Serial.list()[0], 115200);
  myPort.bufferUntil('\n');
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
  text("LANDSLIDE MONITOR", width*0.65, 50);
  
  // TILT DATA
  textSize(18);
  fill(0, 255, 0);
  text("GROUND TILT (Angles)", width*0.65, 110);
  fill(200);
  text("Pitch: " + nf(pitch, 0, 2) + "°", width*0.65, 140);
  text("Roll:  " + nf(roll, 0, 2) + "°", width*0.65, 170);
  
  // IMPACT DATA
  fill(255, 100, 0);
  text("IMPACT FORCES", width*0.65, 230);
  fill(200);
  text("Acc X: " + int(rawX), width*0.65, 260);
  text("Acc Y: " + int(rawY), width*0.65, 290);
  text("Acc Z: " + int(rawZ), width*0.65, 320);

  // SOIL MOISTURE DATA (BARU)
  fill(50, 150, 255); // Warna air
  text("SOIL SATURATION", width*0.65, 380);
  fill(200);
  text("Moisture: " + int(soilMoisture) + "%", width*0.65, 410);
  
  // Gambar Progress Bar untuk kelembaban
  fill(50); // Background bar
  rect(width*0.65, 425, 200, 20);
  fill(50, 150, 255); // Isi bar (biru)
  float barWidth = map(soilMoisture, 0, 100, 0, 200);
  rect(width*0.65, 425, barWidth, 20);
  
  // DANGER ALERT LOGIC (Makin canggih!)
  // Longsor bahaya jika: Tanah sangat basah (>80%) DAN mulai miring sedikit (>5 derajat)
  // ATAU miring drastis (>15 derajat) walaupun kering.
  if ((soilMoisture > 80 && (abs(pitch) > 5 || abs(roll) > 5)) || abs(pitch) > 15 || abs(roll) > 15) {
     fill(255, 0, 0);
     textSize(30);
     text("⚠️ CRITICAL ALERT!", width*0.65, 520);
     text("EVACUATE AREA", width*0.65, 550);
  }
  hint(ENABLE_DEPTH_TEST);
}

void serialEvent(Serial myPort) {
  String inString = myPort.readStringUntil('\n');
  if (inString != null) {
    float[] data = float(split(trim(inString), ','));
    
    // Sekarang kita cek apakah ada 7 data yang masuk
    if (data.length >= 7) {
      if (Float.isNaN(data[0])) return; 
      
      pitch = data[0]; roll = data[1]; yaw = data[2];
      rawX = data[3];  rawY = data[4];  rawZ = data[5];
      soilMoisture = data[6]; // Tangkap data tanah di index ke-6
    }
  }
}
