#include <Wire.h>
#include <MPU6050_light.h>

MPU6050 mpu(Wire);
const int SOIL_PIN = 34; // Pin ADC1 yang aman untuk Wi-Fi nanti

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);
  
  byte status = mpu.begin();
  while(status != 0){ } 
  
  delay(1000);
  mpu.calcOffsets(true,true); 
  
  // Tidak perlu pinMode untuk analogRead di pin 34
}

void loop() {
  mpu.update();

  // 1. Baca data kelembaban tanah
  int soilRaw = analogRead(SOIL_PIN);
  
  // 2. Ubah nilai mentah ke persentase (0% - 100%)
  // Sesuaikan angka 4095 (kering) dan 1000 (basah) ini dengan sensor aslimu nanti!
  int soilPercent = map(soilRaw, 4095, 1000, 0, 100);
  soilPercent = constrain(soilPercent, 0, 100); // Kunci angkanya biar gak minus atau lebih dari 100

  // 3. Kirim semua data: AngleX, AngleY, AngleZ, AccX, AccY, AccZ, SoilMoisture
  Serial.print(mpu.getAngleX());       Serial.print(",");
  Serial.print(mpu.getAngleY());       Serial.print(",");
  Serial.print(mpu.getAngleZ());       Serial.print(",");
  Serial.print(mpu.getAccX() * 16384); Serial.print(","); 
  Serial.print(mpu.getAccY() * 16384); Serial.print(",");
  Serial.print(mpu.getAccZ() * 16384); Serial.print(",");
  Serial.println(soilPercent); // Tambahan data ke-7 di ujung string
  
  delay(20); 
}