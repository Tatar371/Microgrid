#include <ArduinoJson.h>

const int voltagePin = A0;
const int illuminancePin = A1;
const int modePin = 2;  // Для определения режима работы

void setup() {
  Serial.begin(9600);
  pinMode(modePin, INPUT_PULLUP); 
}

void loop() {
  int voltageRaw = analogRead(voltagePin);
  int illuminanceRaw = analogRead(illuminancePin);

  String mode = digitalRead(modePin) == HIGH ? "NORMAL" : "ALTERNATE";

  StaticJsonDocument<200> doc;
  doc["voltage_raw"] = voltageRaw;
  doc["illuminance_raw"] = illuminanceRaw;
  doc["mode"] = mode;
  
  String output;
  serializeJson(doc, output);

  Serial.println(output);
  
  delay(1000);
}