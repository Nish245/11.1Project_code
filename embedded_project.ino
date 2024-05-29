#include <SPI.h>
#include <WiFiNINA.h>
#include <PubSubClient.h>

// Network credentials
const char* ssid = "Optus_B8E72A";
const char* password = "corns39526ys";

// MQTT Broker details
const char* mqtt_server = "mqtt-dashboard.com";
const int mqtt_port = 1883; // Standard MQTT port for non-secure connections

WiFiClient wifiClient;
PubSubClient client(wifiClient);

const int ecgPin = A0; // ECG sensor connected to A0
const int heartRatePin = A2; // Heart rate sensor connected to A2

unsigned long previousMillis = 0;  // Stores last update time for heart rate calculation
unsigned long lastECGSendTime = 0; // Stores last time ECG data was sent
unsigned long lastBPMCalculationTime = 0; // Stores last time BPM was calculated and sent
const long interval = 15000;  // Interval to measure heart rate (15 seconds)
const long ecgSendInterval = 1000; // Interval to send ECG data (1 second)
int beatCounter = 0;  // Number of beats detected

void setup() {
  Serial.begin(9600);
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);

  pinMode(ecgPin, INPUT);
  pinMode(heartRatePin, INPUT);
}

void setup_wifi() {
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  unsigned long currentMillis = millis();

  // Read and publish ECG data every 1 second
  if (currentMillis - lastECGSendTime >= ecgSendInterval) {
    int ecgValue = analogRead(ecgPin);
    float ecgVoltage = ecgValue * (3.3 / 1023.0);
    String ecgPayload = "ECG Voltage: " + String(ecgVoltage) + " V";
    client.publish("ecg/data", ecgPayload.c_str());
    Serial.println("Sent to MQTT - ECG: " + ecgPayload);
    lastECGSendTime = currentMillis;
  }

  // Read and process heart rate data
  int heartRateValue = analogRead(heartRatePin);
  if (heartRateValue > 512) {  // Threshold value for detecting a beat
    if (currentMillis - previousMillis >= 300) {  // Debounce the signal
      beatCounter++;
      previousMillis = currentMillis;
    }
  }

  // Calculate and publish heart rate every 15 seconds
  if (currentMillis - lastBPMCalculationTime >= interval) {
    double bpm = (beatCounter / (interval / 1000.0)) * 60.0;  // Calculate BPM
    String bpmStatus = (bpm > 100) ? "High" : "Normal";  // Determine heart rate status

    // Filter out unreasonable BPM values
    if (bpm > 200) {
      bpm = 0;  // Set to 0 or another indicative value
      bpmStatus = "Invalid";  // Mark as invalid reading
    }

    String bpmPayload = "Heart Rate: " + String(bpm) + " BPM (" + bpmStatus + ")";
    client.publish("heartRate/bpm", bpmPayload.c_str());
    Serial.println("Sent to MQTT - BPM: " + bpmPayload);
    beatCounter = 0;  // Reset beat counter
    lastBPMCalculationTime = currentMillis;
  }

  delay(10); // Short delay to prevent spamming readings
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("ArduinoClient")) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}
