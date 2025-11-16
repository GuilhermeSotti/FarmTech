#include <WiFi.h>
#include <PubSubClient.h>

const char* ssid = "YOUR_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* mqtt_server = "broker.hivemq.com";

WiFiClient espClient;
PubSubClient client(espClient);

const int SENSOR_PIN = 34;

void setup() {
  Serial.begin(115200);
  pinMode(SENSOR_PIN, INPUT);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
  client.setServer(mqtt_server, 1883);
}

void publish_reading() {
  int raw = analogRead(SENSOR_PIN);
  float humidity = map(raw, 0, 4095, 0, 100);
  char payload[128];
  snprintf(payload, sizeof(payload), "{\"sensor_id\":\"esp32-01\",\"umidade\":%.2f,\"ts\":\"%s\"}", humidity, "2025-11-16T00:00:00");
  client.publish("farmtech/sensors/soil", payload);
  Serial.println(payload);
}

void loop() {
  if (!client.connected()) {
    client.connect("esp32-client");
  }
  client.loop();
  publish_reading();
  delay(60000);
}
