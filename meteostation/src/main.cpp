#include <Arduino.h>
#include <Wire.h>
#include <BH1750.h>
#include "SparkFunHTU21D.h"
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

const char* ssid = "KomarNetwork";
const char* password = "";
const char* mqtt_server = "192.168.1.222"; //Raspberry staticka adresa

//Init senzoru
BH1750 lightMeter;
HTU21D htu;

//Wifi + MQTT objekty
WiFiClient espClient;
PubSubClient client(espClient);

//MQTT vars
const int delayTime = 5000;
long lastMsg = 0;

//Deklarace funkcí 
void setup_wifi();
void callback(char*, byte*, unsigned int);
void reconnect();

//Funkce pro připojení k Wifi
void setup_wifi() {
  delay(10);

  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  //Dokud nebylo ESP neni pripojeno cekej
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  randomSeed(micros());

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

//Funkce pro poslech MQTT --> zatim nevyuzita
void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();
}

//Funkce pro připojení k MQTT serveru
void reconnect() {
  //Opakuj dokud se nepripojis
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    //Nahodna generace ID
    String clientId = "ESP8266Client-";
    clientId += String(random(0xffff), HEX);
    //Test spojeni
    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
      //Případný poslech MQTT
      //client.subscribe("TOPIC");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      //Za 5 sekund se zkus pripojit znovu
      delay(5000);
    }
  }
}

void setup(){
  //Init Portů a serialu
  Serial.begin(9600);
  Wire.begin(D1,D2);
  pinMode(BUILTIN_LED, OUTPUT); 

  //Init senzorů
  lightMeter.begin();
  htu.begin();

  //Init wifi a MQTT
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  long now = millis();
  if(now - lastMsg > delayTime) { 
    lastMsg = now;

    //Light
    float lux = lightMeter.readLightLevel();

    //Temp, hum
    float humd = htu.readHumidity();
    float temp = htu.readTemperature();

    Serial.printf("Light: %f lux, ", lux);
    Serial.printf("Temp: %f C, ", temp);
    Serial.printf("Humd: %f pr", humd);
    Serial.println();

    //Posli hodnoty na MQTT Broker na Raspberry
    client.publish("meteo1/temp", String(temp).c_str());
    client.publish("meteo1/humd", String(humd).c_str());
    client.publish("meteo1/light", String(lux).c_str());
  }
}