/*
 * ESP32 MyIoT — Clean architecture with configurable rooms
 * 
 * Device: ESP32 with configurable channels (buttons and LEDs)
 * Each channel can be mapped to any room via CHANNEL_ROOM_INDEX[]
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ===== CONFIGURATION =====
const char* SSID = "Hani";
const char* PASSWORD = "12345678h";
const char* MQTT_SERVER = "172.20.10.4";
const int MQTT_PORT = 1884;
const char* DEVICE_ID = "esp32_multi";

// ===== CONFIGURATION DES CHAMBRES =====
#define MAX_CHANNELS 4  // Nombre maximum de canaux supportés

// Liste des chambres disponibles
const char* ROOM_NAMES[] = {"chambre", "cuisine", "salon"};
const int NUM_ROOMS = 3;

// Configuration des canaux actifs
const int NUM_CHANNELS = 3;  // Nombre de canaux réellement utilisés (3 boutons)

// Mapping canal -> index de chambre dans ROOM_NAMES[]
// Ici : canal0->chambre, canal1->cuisine, canal2->salon
const int CHANNEL_ROOM_INDEX[MAX_CHANNELS] = {0, 1, 2, 0};

// GPIO Pin assignments par canal (ajustez si nécessaire)
// J'utilise GPIO 18 pour le 3ème bouton et GPIO 5 pour la 3ème LED par défaut
const int BUTTON_PINS[MAX_CHANNELS] = {21, 19, 18, 0};
const int LED_PINS[MAX_CHANNELS] = {23, 22, 5, 0};

// LED inversion (set true if LED is active-low)
const bool INVERT_LEDS[MAX_CHANNELS] = {false, false, false, false};

// Timing
const unsigned long DEBOUNCE_MS = 50;
const unsigned long SENSOR_PUBLISH_INTERVAL_MS = 5000;

// ===== GLOBALS =====
WiFiClient wifiClient;
PubSubClient client(wifiClient);

// Button states
bool lastButtonStates[MAX_CHANNELS];
unsigned long lastButtonDebounces[MAX_CHANNELS];
int buttonValues[MAX_CHANNELS];
unsigned long lastSensorPublish = 0;


// ===== HELPERS =====
const char* mqttStateName(int state){
  switch(state){
    case -4: return "TIMEOUT";
    case -3: return "LOST";
    case -2: return "CONNECT_FAILED";
    case -1: return "DISCONNECTED";
    case 0:  return "CONNECTED";
    case 1:  return "BAD_PROTOCOL";
    case 2:  return "BAD_CLIENT_ID";
    case 3:  return "UNAVAILABLE";
    case 4:  return "BAD_CREDENTIALS";
    case 5:  return "UNAUTHORIZED";
    default: return "UNKNOWN";
  }
}

void setLed(int channel, bool on){
  if (channel < 0 || channel >= NUM_CHANNELS) return;
  
  int pin = LED_PINS[channel];
  bool invert = INVERT_LEDS[channel];
  
  bool out = on;
  if (invert) out = !out;
  digitalWrite(pin, out ? HIGH : LOW);
  
  int roomIdx = CHANNEL_ROOM_INDEX[channel];
  Serial.print("LED"); Serial.print(channel); Serial.print(" ("); 
  Serial.print(ROOM_NAMES[roomIdx]); Serial.print("): "); 
  Serial.println(on ? "ON" : "OFF");
}

void publishSensor(const char* room, int value){
  String topic = String("myiot_local/") + room + "/sensor/motion";
  StaticJsonDocument<200> doc;
  doc["value"] = value;
  doc["unit"] = "binary";
  doc["timestamp"] = millis();
  
  String payload;
  serializeJson(doc, payload);
  
  if (client.publish(topic.c_str(), payload.c_str())){
    Serial.print("Published: "); Serial.print(topic); Serial.print(" = "); Serial.println(payload);
  }
}

void onMqttMessage(char* topicC, byte* payload, unsigned int length){
  String topic = String(topicC);
  String pl;
  pl.reserve(length + 1);
  for (unsigned int i = 0; i < length; i++){
    pl += (char)payload[i];
  }
  
  Serial.print("MQTT IN: "); Serial.print(topic); Serial.print(" = "); Serial.println(pl);
  
  // Parse state from JSON
  StaticJsonDocument<200> doc;
  DeserializationError err = deserializeJson(doc, pl);
  String state = "OFF";
  if (!err && doc.containsKey("state")){
    state = String(doc["state"].as<const char*>());
  }
  state.toUpperCase();
  
  // Route to correct LED based on room
  for (int channel = 0; channel < NUM_CHANNELS; channel++){
    int roomIdx = CHANNEL_ROOM_INDEX[channel];
    if (topic.indexOf(ROOM_NAMES[roomIdx]) >= 0){
      if (state == "ON" || state == "1") setLed(channel, true);
      else setLed(channel, false);
      break;
    }
  }
}

void subscribeToActuators(){
  // S'abonner aux topics de toutes les chambres utilisées
  bool subscribed[NUM_ROOMS];
  for (int i = 0; i < NUM_ROOMS; i++) subscribed[i] = false;
  
  for (int channel = 0; channel < NUM_CHANNELS; channel++){
    int roomIdx = CHANNEL_ROOM_INDEX[channel];
    if (!subscribed[roomIdx]){
      String topic = String("myiot_local/") + ROOM_NAMES[roomIdx] + "/actuator/+/cmd";
      client.subscribe(topic.c_str());
      Serial.print("Subscribed: "); Serial.println(topic);
      subscribed[roomIdx] = true;
    }
  }
}

void reconnectMqtt(){
  static unsigned long lastAttempt = 0;
  if (millis() - lastAttempt < 3000) return;
  lastAttempt = millis();
  
  if (client.connected()) return;
  
  Serial.print("Connecting MQTT...");
  if (client.connect(DEVICE_ID)){
    Serial.println(" ✓");
    subscribeToActuators();
  } else {
    int rc = client.state();
    Serial.print(" failed rc="); Serial.print(rc);
    Serial.print(" ("); Serial.print(mqttStateName(rc)); Serial.println(")");
  }
}

void handleButton(int channel){
  if (channel < 0 || channel >= NUM_CHANNELS) return;
  
  bool cur = digitalRead(BUTTON_PINS[channel]);
  if (cur != lastButtonStates[channel]){
    unsigned long now = millis();
    if (now - lastButtonDebounces[channel] > DEBOUNCE_MS){
      lastButtonDebounces[channel] = now;
      lastButtonStates[channel] = cur;
      buttonValues[channel] = (cur == LOW) ? 1 : 0;
      
      int roomIdx = CHANNEL_ROOM_INDEX[channel];
      Serial.print("Button"); Serial.print(channel); Serial.print(" (");
      Serial.print(ROOM_NAMES[roomIdx]); Serial.print("): ");
      Serial.println(buttonValues[channel]);
      
      // Control LED directly when button pressed/released
      setLed(channel, buttonValues[channel] == 1);
      // Publish sensor
      publishSensor(ROOM_NAMES[roomIdx], buttonValues[channel]);
    }
  }
}

void handleSerialCommands(){
  if (Serial.available()){
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    cmd.toLowerCase();
    
    // Commandes LED dynamiques (led0, led1, etc.)
    for (int ch = 0; ch < NUM_CHANNELS; ch++){
      String ledOnCmd = "led" + String(ch) + " on";
      String ledOffCmd = "led" + String(ch) + " off";
      if (cmd == ledOnCmd) { setLed(ch, true); return; }
      if (cmd == ledOffCmd) { setLed(ch, false); return; }
    }
    
    if (cmd == "blink"){
      for (int i = 0; i < 3; i++){
        for (int ch = 0; ch < NUM_CHANNELS; ch++) setLed(ch, true);
        delay(300);
        for (int ch = 0; ch < NUM_CHANNELS; ch++) setLed(ch, false);
        delay(200);
      }
    }
    else if (cmd == "status"){
      Serial.println("=== STATUS ===");
      for (int ch = 0; ch < NUM_CHANNELS; ch++){
        int roomIdx = CHANNEL_ROOM_INDEX[ch];
        Serial.print("Button"); Serial.print(ch); Serial.print(" (");
        Serial.print(ROOM_NAMES[roomIdx]); Serial.print("): ");
        Serial.println(buttonValues[ch]);
      }
      Serial.print("MQTT: "); Serial.println(client.connected() ? "CONNECTED" : "DISCONNECTED");
    }
    else if (cmd == "config"){
      Serial.println("=== CONFIGURATION ===");
      Serial.print("Device ID: "); Serial.println(DEVICE_ID);
      Serial.print("Nombre de chambres: "); Serial.println(NUM_ROOMS);
      Serial.print("Chambres disponibles: ");
      for (int i = 0; i < NUM_ROOMS; i++){
        Serial.print(ROOM_NAMES[i]);
        if (i < NUM_ROOMS - 1) Serial.print(", ");
      }
      Serial.println();
      Serial.print("Nombre de canaux: "); Serial.println(NUM_CHANNELS);
      for (int ch = 0; ch < NUM_CHANNELS; ch++){
        Serial.print("  Canal "); Serial.print(ch); Serial.print(": ");
        Serial.print("Button=GPIO"); Serial.print(BUTTON_PINS[ch]);
        Serial.print(", LED=GPIO"); Serial.print(LED_PINS[ch]);
        Serial.print(" -> "); Serial.println(ROOM_NAMES[CHANNEL_ROOM_INDEX[ch]]);
      }
    }
    else if (cmd.length() > 0) {
      Serial.println("Unknown cmd. Try: led0/led1 on/off, blink, status, config");
    }
  }
}

// ===== SETUP =====
void setup(){
  Serial.begin(115200);
  delay(50);
  
  Serial.println("\n=== ESP32 MyIoT (Clean Architecture) ===");
  Serial.print("Device: "); Serial.println(DEVICE_ID);
  Serial.print("Chambres configurées: ");
  for (int ch = 0; ch < NUM_CHANNELS; ch++){
    Serial.print(ROOM_NAMES[CHANNEL_ROOM_INDEX[ch]]);
    if (ch < NUM_CHANNELS - 1) Serial.print(", ");
  }
  Serial.println();
  
  // GPIO setup dynamique
  for (int ch = 0; ch < NUM_CHANNELS; ch++){
    pinMode(BUTTON_PINS[ch], INPUT_PULLUP);
    pinMode(LED_PINS[ch], OUTPUT);
    setLed(ch, false);
    lastButtonStates[ch] = digitalRead(BUTTON_PINS[ch]);
    lastButtonDebounces[ch] = 0;
    buttonValues[ch] = 0;
  }
  
  // WiFi connection
  Serial.print("Connecting WiFi...");
  WiFi.mode(WIFI_STA);
  WiFi.begin(SSID, PASSWORD);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20){
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED){
    Serial.println("\nWiFi OK");
    Serial.print("IP: "); Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nWiFi FAILED");
  }
  
  // MQTT setup
  client.setServer(MQTT_SERVER, MQTT_PORT);
  client.setCallback(onMqttMessage);
  
  // Startup LED blink test
  Serial.println("=== STARTUP LED TEST ===");
  for (int test = 0; test < 2; test++){
    Serial.print("Blink "); Serial.println(test + 1);
    for (int ch = 0; ch < NUM_CHANNELS; ch++) setLed(ch, true);
    delay(300);
    for (int ch = 0; ch < NUM_CHANNELS; ch++) setLed(ch, false);
    delay(200);
  }
  Serial.println("=== READY ===");
  Serial.println("Serial commands: led0/led1 on/off, blink, status, config");
}

// ===== MAIN LOOP =====
void loop(){
  handleSerialCommands();
  
  if (!client.connected()){
    reconnectMqtt();
  }
  client.loop();
  
  // Check all buttons dynamically
  for (int ch = 0; ch < NUM_CHANNELS; ch++){
    handleButton(ch);
  }
  
  // Periodic sensor publish
  if (millis() - lastSensorPublish >= SENSOR_PUBLISH_INTERVAL_MS){
    for (int ch = 0; ch < NUM_CHANNELS; ch++){
      int roomIdx = CHANNEL_ROOM_INDEX[ch];
      publishSensor(ROOM_NAMES[roomIdx], (digitalRead(BUTTON_PINS[ch]) == LOW) ? 1 : 0);
    }
    lastSensorPublish = millis();
  }
}
