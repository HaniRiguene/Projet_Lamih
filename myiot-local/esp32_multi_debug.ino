/*
 * ESP32 MyIoT — Debug build (3 buttons / 3 lamps)
 * Adds verbose logs, MQTT ack, heartbeat and remote force commands.
 */
/*
 * ESP32 MyIoT — 2 boutons / 2 diodes (myiot_local per-room topics)
 * - Publishes: myiot_local/<room>/sensor/button1  and button2
 * - Subscribes: myiot_local/<room>/actuator/lamp1/cmd and lamp2
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ===== CONFIG =====
const char* SSID = "Hani";             // TODO: change
const char* PASSWORD = "12345678h"; // TODO: change

const char* MQTT_SERVER = "172.20.10.4";    // TODO: change to PC IP
const int MQTT_PORT = 1884;

const char* DEVICE_ID = "esp32_salon"; // kept for backward compatibility

// Channels
const int NUM_CHANNELS = 2;
int BUTTON_PINS[NUM_CHANNELS] = {21, 19};
int LED_PINS[NUM_CHANNELS]    = {23, 22};

// Available room names in your home
const int NUM_AVAILABLE_ROOMS = 5;
const char* ROOM_NAMES[NUM_AVAILABLE_ROOMS] = {"chambre", "salle_a_manger", "salon", "bureau", "cuisine"};

// Map each physical channel to an index in ROOM_NAMES.
// Example: CHANNEL_ROOM_INDEX[0] = 0 -> channel0 maps to ROOM_NAMES[0] == "chambre"
int CHANNEL_ROOM_INDEX[NUM_CHANNELS] = {0, 1}; // legacy: not used for new per-channel mapping below

// Per-channel sensor room index and actuator room index (indices into ROOM_NAMES)
// User request: button1 -> sensor room 'salle_a_manger' and subscribe to 'salle_a_manger' lamp1
//               button2 -> sensor room 'cuisine' and subscribe to 'salle_a_manger' lamp2
int SENSOR_ROOM_INDEX[NUM_CHANNELS]   = { 1, 4 }; // 1 == salle_a_manger, 4 == cuisine
int ACTUATOR_ROOM_INDEX[NUM_CHANNELS] = { 1, 1 }; // both actuators listened in salle_a_manger

// If your LEDs are active-low (connected to VCC through resistor), set true per channel
bool INVERT_LED[NUM_CHANNELS] = {false, false};

// Timing
const unsigned long DEBOUNCE_MS = 50;
const unsigned long PUBLISH_INTERVAL_MS = 5000;

// ===== GLOBALS =====
WiFiClient wifiClient;
PubSubClient client(wifiClient);

String ROOM;
bool lastButtonState[NUM_CHANNELS];
unsigned long lastDebounce[NUM_CHANNELS];
unsigned long lastPublish = 0;

// ===== HELPERS =====
void deriveRoomFromDeviceId(){
  ROOM = String(DEVICE_ID);
  if (ROOM.startsWith("esp32_")) ROOM = ROOM.substring(6);
  ROOM.toLowerCase();
}

String sensorTopic(int ch){
  int idx = SENSOR_ROOM_INDEX[ch];
  return String("myiot_local/") + String(ROOM_NAMES[idx]) + "/sensor/button" + String(ch+1);
}

String actuatorWildcardForRoom(const char* room){
  return String("myiot_local/") + String(room) + "/actuator/+/cmd";
}

// extract room from topic 'myiot_local/<room>/actuator/...'
String roomFromTopic(const String &topic){
  int p0 = topic.indexOf('/');
  if (p0 < 0) return String();
  int p1 = topic.indexOf('/', p0+1);
  if (p1 < 0) return String();
  return topic.substring(p0+1, p1);
}

int channelForRoom(const String &room){
  // find room index
  int ridx = -1;
  for (int i=0;i<NUM_AVAILABLE_ROOMS;i++){
    if (room == String(ROOM_NAMES[i])) { ridx = i; break; }
  }
  if (ridx < 0) return -1;
  // find which channel maps to that room index
  for (int ch=0; ch<NUM_CHANNELS; ch++){
    if (CHANNEL_ROOM_INDEX[ch] == ridx) return ch;
  }
  return -1;
}

// parse actuator id (lamp1/lamp2) from topic
String parseActuatorId(const String &topic){
  int p = topic.indexOf("/actuator/");
  if (p<0) return String();
  int start = p + 10;
  int slash = topic.indexOf('/', start);
  if (slash<0) return topic.substring(start);
  return topic.substring(start, slash);
}

// map actuator name like "lamp1" -> channel index
int channelForActuator(const String &act){
  if (act.startsWith("lamp")){
    String num = act.substring(4);
    int n = num.toInt();
    if (n>=1 && n<=NUM_CHANNELS) return n-1;
  }
  return -1;
}

String extractState(const String &payload){
  StaticJsonDocument<200> doc;
  DeserializationError err = deserializeJson(doc, payload);
  if (!err && doc.containsKey("state")){
    String s = String(doc["state"].as<const char*>());
    s.trim(); return s;
  }
  // fallback simple parse
  String s = payload; s.replace('{',' '); s.replace('}',' '); s.trim();
  String su = s; su.toUpperCase();
  int pos = su.indexOf("STATE");
  if (pos>=0){ int colon = su.indexOf(':', pos); if (colon>=0){ String val = s.substring(colon+1); val.trim(); if (val.length()>0 && (val.charAt(0)=='"' || val.charAt(0)=='\'')) val = val.substring(1); if (val.length()>0){ char last = val.charAt(val.length()-1); if (last=='"' || last=='\'') val = val.substring(0,val.length()-1);} val.trim(); return val; } }
  return String();
}

void setLed(int ch, bool on){
  bool out = on;
  if (INVERT_LED[ch]) out = !out;
  digitalWrite(LED_PINS[ch], out ? HIGH : LOW);
  Serial.print("LED"); Serial.print(ch+1); Serial.print("(pin"); Serial.print(LED_PINS[ch]); Serial.print(") "); Serial.println(on?"ON":"OFF");
}

void subscribeAll(){
  // subscribe to actuator wildcards for each unique actuator room
  bool seen[NUM_AVAILABLE_ROOMS]; for (int i=0;i<NUM_AVAILABLE_ROOMS;i++) seen[i]=false;
  for (int ch=0; ch<NUM_CHANNELS; ch++){
    int ridx = ACTUATOR_ROOM_INDEX[ch];
    if (ridx<0 || ridx>=NUM_AVAILABLE_ROOMS) continue;
    if (seen[ridx]) continue;
    seen[ridx]=true;
    String topic = actuatorWildcardForRoom(ROOM_NAMES[ridx]);
    client.subscribe(topic.c_str());
    Serial.print("Subscribed to: "); Serial.println(topic);
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
    subscribeAll();
  } else {
    Serial.print(" failed rc="); Serial.println(client.state());
  }
}

// ===== MQTT CALLBACK =====
void onMqttMessage(char* topicC, byte* payload, unsigned int length){
  String topic = String(topicC);
  String pl; pl.reserve(length+1);
  for (unsigned int i=0;i<length;i++) pl += (char)payload[i];
  Serial.print("MQTT IN: "); Serial.print(topic); Serial.print(" = "); Serial.println(pl);

  // Determine room from topic and attempt to route to correct channel
  String room = roomFromTopic(topic);
  int ridx = -1;
  for (int i=0;i<NUM_AVAILABLE_ROOMS;i++) if (room == String(ROOM_NAMES[i])) { ridx = i; break; }
  if (ridx < 0) { Serial.println("No matching room in ROOM_NAMES"); return; }

  // Prefer mapping by actuator id (lamp1 -> channel 0, lamp2 -> channel1)
  String act = parseActuatorId(topic);
  int chByAct = channelForActuator(act);

  int targetCh = -1;
  if (chByAct >= 0 && ACTUATOR_ROOM_INDEX[chByAct] == ridx) {
    targetCh = chByAct;
  } else {
    // fallback: find a channel that listens to this actuator room
    for (int ch=0; ch<NUM_CHANNELS; ch++){
      if (ACTUATOR_ROOM_INDEX[ch] == ridx) { targetCh = ch; break; }
    }
  }

  if (targetCh < 0) { Serial.println("No channel mapped to this actuator room"); return; }

  String state = extractState(pl);
  if (state.length()==0){ Serial.println("No state parsed"); return; }
  state.toUpperCase();
  if (state=="ON" || state=="1") setLed(targetCh, true);
  else setLed(targetCh, false);
}

// publish sensor for channel
void publishSensor(int ch, int value){
  StaticJsonDocument<200> doc; doc["value"] = value; doc["unit"] = "binary"; doc["msg_id"] = String(millis());
  String payload; serializeJson(doc, payload);
  String topic = sensorTopic(ch);
  if (client.publish(topic.c_str(), payload.c_str())){
    Serial.print("Published: "); Serial.print(topic); Serial.print(" = "); Serial.println(payload);
  }
}

// ===== SETUP =====
void setup(){
  Serial.begin(115200); delay(50);
  Serial.println("\n=== ESP32 MyIoT (2 boutons / 2 diodes) ===");
  deriveRoomFromDeviceId();
  Serial.print("ROOM: "); Serial.println(ROOM);

  for (int i=0;i<NUM_CHANNELS;i++){
    pinMode(BUTTON_PINS[i], INPUT_PULLUP);
    pinMode(LED_PINS[i], OUTPUT);
    setLed(i, false);
    lastButtonState[i] = digitalRead(BUTTON_PINS[i]);
    lastDebounce[i] = 0;
  }

  WiFi.mode(WIFI_STA); WiFi.begin(SSID, PASSWORD);
  Serial.print("Connecting WiFi"); int attempts=0; while (WiFi.status()!=WL_CONNECTED && attempts<20){ delay(500); Serial.print('.'); attempts++; }
  if (WiFi.status()==WL_CONNECTED) { Serial.println("\nWiFi OK"); Serial.print("IP: "); Serial.println(WiFi.localIP()); } else Serial.println("\nWiFi failed");

  client.setServer(MQTT_SERVER, MQTT_PORT);
  client.setCallback(onMqttMessage);

  // Diagnostic output
  Serial.print("LED pins: ");
  for (int i=0;i<NUM_CHANNELS;i++){ Serial.print(LED_PINS[i]); if (i<NUM_CHANNELS-1) Serial.print(","); }
  Serial.println();
  Serial.print("INVERT_LED: ");
  for (int i=0;i<NUM_CHANNELS;i++){ Serial.print(INVERT_LED[i] ? "1":"0"); if (i<NUM_CHANNELS-1) Serial.print(","); }
  Serial.println();

  // Startup blink test
  Serial.println("=== STARTUP LED BLINK TEST ===");
  for (int test=0; test<3; test++){
    Serial.print("Blink "); Serial.println(test+1);
    setLed(0, true); setLed(1, true); delay(300);
    setLed(0, false); setLed(1, false); delay(200);
  }
  Serial.println("=== END BLINK TEST ===");
  Serial.println("Send 'led1 on', 'led1 off', 'led2 on', 'led2 off' via Serial to test LEDs");
}

// Handle Serial commands for LED testing
void handleSerialCommands(){
  if (Serial.available()){
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "led1 on") { setLed(0, true); }
    else if (cmd == "led1 off") { setLed(0, false); }
    else if (cmd == "led2 on") { setLed(1, true); }
    else if (cmd == "led2 off") { setLed(1, false); }
    else if (cmd == "blink") { for(int i=0;i<3;i++){ setLed(0, true); setLed(1, true); delay(300); setLed(0, false); setLed(1, false); delay(200); } }
    else if (cmd.length() > 0) { Serial.println("Unknown cmd. Try: led1 on/off, led2 on/off, blink"); }
  }
}

// ===== MAIN LOOP =====
void loop(){
  handleSerialCommands();
  if (!client.connected()) reconnectMqtt();
  client.loop();

  // debounce check
  for (int i=0;i<NUM_CHANNELS;i++){
    bool cur = digitalRead(BUTTON_PINS[i]);
    if (cur != lastButtonState[i]){
      unsigned long now = millis();
      if (now - lastDebounce[i] > DEBOUNCE_MS){
        lastDebounce[i] = now;
        lastButtonState[i] = cur;
        if (cur == LOW){ // pressed
          Serial.print("Button"); Serial.print(i+1); Serial.println(" PRESSED");
          publishSensor(i, 1);
        } else {
          Serial.print("Button"); Serial.print(i+1); Serial.println(" RELEASED");
          publishSensor(i, 0);
        }
      }
    }
  }

  // periodic publish of current state
  if (millis() - lastPublish >= PUBLISH_INTERVAL_MS){
    for (int i=0;i<NUM_CHANNELS;i++){
      publishSensor(i, (digitalRead(BUTTON_PINS[i])==LOW)?1:0);
    }
    lastPublish = millis();
  }
}
