#include <Arduino.h>
#include <WiFiUdp.h>
#include <ESP8266WiFi.h>
#include "drv8833.hpp"

bool heartbeat_check(unsigned long time_since_last_msg);
int handleUDPServer();
void setup_wifi();

void led_handler();
void button_handler();
void refresh_power_module();

const int POWER_PIN = 14;
const int USER_BTN_PIN = 15;
const int USER_LED_PIN = 16;
const int MODULE_LED_PIN = 2;
const int APWM1_PIN = 4;
const int APWM2_PIN = 5;
const int BPWM1_PIN = 12;
const int BPWM2_PIN = 13;

DRV8833_DRIVER lMotor(APWM1_PIN, APWM2_PIN);
DRV8833_DRIVER rMotor(BPWM1_PIN, BPWM2_PIN);
WiFiUDP UDPServer;

// Wifi和机器人参数设置
int robotID = 4;
const char *ssid = "00ummm00";
const char *password = "bageling";
unsigned int UDPPort = 2801;
IPAddress staticIP(192, 168, 0, 130 + robotID); // 固定IP
IPAddress gateway(192, 168, 0, 1);
IPAddress subnet(255, 255, 255, 0);
IPAddress dns(8, 8, 8, 8);

String udp_data = " ";
const int packetSize = 15;
byte packetBuffer[packetSize];
unsigned long time_since_last_msg;
int split_msg[4];
int rightspeed = 0;
int leftspeed = 0;

uint32_t time_record[10];
uint32_t time_now = 0;
int wifi_connected = 0;
int blinker_cnt = 0;

enum led_blinker_stage_e
{
  SHOW_ID = 0,
  SHOW_WIFI_DISCONNECT,
  SHOW_BLACK
};
enum led_blinker_stage_e blinker_stage = SHOW_ID;

void setup()
{
  memset(time_record, 0, sizeof(time_record));

  lMotor.setSpeed(0);
  rMotor.setSpeed(0);

  Serial.begin(9600);

  pinMode(USER_LED_PIN, OUTPUT);
  pinMode(MODULE_LED_PIN, OUTPUT);
  pinMode(POWER_PIN, OUTPUT);
  pinMode(USER_BTN_PIN, OUTPUT);

  digitalWrite(USER_LED_PIN, LOW);
  digitalWrite(MODULE_LED_PIN, LOW);
  digitalWrite(POWER_PIN, HIGH);
  digitalWrite(USER_BTN_PIN, HIGH);

  setup_wifi();

  UDPServer.begin(UDPPort);

  digitalWrite(USER_LED_PIN, HIGH);
  digitalWrite(MODULE_LED_PIN, HIGH);

  delay(1000);
}

void loop()
{

  // 每过10s拉低充电模块，防止电被关
  refresh_power_module();

  // 处理led灯的动作
  led_handler();

  // 处理按键
  button_handler();

  // 接收UDP数据并解析
  if (handleUDPServer() != 0)
  {
    char str[udp_data.length()];
    memcpy(&str[0], &udp_data[0], sizeof(str));
    char *token = strtok(str, ",");
    int i = 0;
    while (token != NULL)
    {
      split_msg[i] = atoi(token);
      token = strtok(NULL, ",");
      i++;
    }
    leftspeed = split_msg[0];
    rightspeed = split_msg[1];
    Serial.println("get udp data ! ");
  }

  // 心跳检测，1S没有消息则停止电机
  if (!heartbeat_check(time_since_last_msg))
  {
    leftspeed = 0;
    rightspeed = 0;
  }

  // 更新驱动速度
  lMotor.setSpeed(leftspeed);
  rMotor.setSpeed(rightspeed);
}

void refresh_power_module()
{
  // 每过10s拉低充电模块，防止电被关
  time_now = millis();
  if (time_now - time_record[0] > 5000)
  {
    time_record[0] = millis();
    digitalWrite(POWER_PIN, LOW);
    delay(50);
    digitalWrite(POWER_PIN, HIGH);
  }
}

void button_handler()
{
  time_now = millis();
  // 按键检测，检测按键的逻辑
  if (digitalRead(USER_BTN_PIN) == LOW)
  {
    Serial.println("USER_BTN_PIN ");
  }
}

void led_toggle(int pin)
{
  if (digitalRead(pin) == LOW)
    digitalWrite(pin, HIGH);
  else
    digitalWrite(pin, LOW);
}

void led_handler()
{
  time_now = millis();

  switch (blinker_stage)
  {
  case SHOW_ID:
    if (time_now - time_record[1] > 200)
    {
      time_record[1] = millis();
      led_toggle(USER_LED_PIN);
      led_toggle(MODULE_LED_PIN);
      blinker_cnt++;
      if (blinker_cnt >= robotID * 2)
      {
        blinker_cnt = 0;
        if (wifi_connected == false)
          blinker_stage = SHOW_WIFI_DISCONNECT;
        else
          blinker_stage = SHOW_BLACK;
      }
    }
    break;
  case SHOW_WIFI_DISCONNECT:
    if (time_now - time_record[1] > 50)
    {
      time_record[1] = millis();
      led_toggle(USER_LED_PIN);
      led_toggle(MODULE_LED_PIN);
      blinker_cnt++;
      if (blinker_cnt >= 20)
      {
        blinker_cnt = 0;
        blinker_stage = SHOW_BLACK;
      }
    }
    break;
  case SHOW_BLACK:
    if (time_now - time_record[1] > 2000)
    {
      time_record[1] = millis();
      blinker_stage = SHOW_ID;
      digitalWrite(USER_LED_PIN, HIGH);
      digitalWrite(MODULE_LED_PIN, HIGH);
    }
    break;
  default:
    break;
  }
}

bool heartbeat_check(unsigned long time_since_last_msg)
{
  unsigned long new_msg = millis();
  // 一秒钟没有接收到新的消息则返回 False
  if (new_msg - time_since_last_msg >= 1000)
  {
    return false;
  }
  return true;
}

int handleUDPServer()
{
  int cb = UDPServer.parsePacket();
  if (cb)
  {
    UDPServer.read(packetBuffer, packetSize);
    udp_data = "";
    for (int i = 0; i < packetSize; i++)
    {
      udp_data += (char)packetBuffer[i];
    }
    time_since_last_msg = millis();
  }
  return cb;
}

int wifi_error_cnt = 0;
void setup_wifi()
{
  delay(100);

  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.config(staticIP, subnet, gateway, dns);
  WiFi.begin(ssid, password);

  wifi_connected = true;

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
    wifi_error_cnt++;
    if (wifi_error_cnt >= 40)
    {
      wifi_connected = false;
      break;
    }
  }

  if (wifi_connected == true)
  {
    Serial.println("");
    Serial.println("WiFi connected");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  }
  else
  {
    Serial.println("");
    Serial.println("WiFi connect Failed !!");
    for (int i = 0; i < 50; i++)
    {
      led_toggle(USER_LED_PIN);
      led_toggle(MODULE_LED_PIN);
      delay(50);
    }
    delay(1000);
  }
}
