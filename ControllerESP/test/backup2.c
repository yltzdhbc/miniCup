#include <Arduino.h>
#include <WiFiUdp.h>
#include <ESP8266WiFi.h>
#include "drv8833.hpp"

bool heartbeat_check(unsigned long time_since_last_msg);
int handleUDPServer();
void setup_wifi();

// const int POWER_PIN = 5; //用于拉低充电模块，防止充电模块断电
// const int USER_BTN_PIN = 15;
// const int USER_LED_PIN = 16;
// const int APWM1_PIN = 2;
// const int APWM2_PIN = 4;
// const int BPWM1_PIN = 12;
// const int BPWM2_PIN = 13;

const int POWER_PIN = 14;
const int USER_BTN_PIN = 15;
const int USER_LED_PIN = 16;
const int MODULE_LED_PIN = 2;
const int APWM1_PIN = 4;
const int APWM2_PIN = 5;
const int BPWM1_PIN = 12;
const int BPWM2_PIN = 13;

// 电机初始化
DRV8833_DRIVER lMotor(APWM1_PIN, APWM2_PIN);
DRV8833_DRIVER rMotor(BPWM1_PIN, BPWM2_PIN);

// UDP服务器
WiFiUDP UDPServer;

// Wifi参数设置
const char *ssid = "00ummm00";
const char *password = "bageling";
int robotID = 3;
// #define robotID 3


IPAddress staticIP(192, 168, 0, 130+robotID ); // 固定IP
IPAddress gateway(192, 168, 0, 1);
IPAddress subnet(255, 255, 255, 0);
IPAddress dns(8, 8, 8, 8);
// 设备名称及UDP端口
// const char *deviceName = "bot2";
unsigned int UDPPort = 2801;

String udp_data = " ";
const int packetSize = 15;
byte packetBuffer[packetSize];
unsigned long time_since_last_msg;
int split_msg[4];
int rightspeed = 0;
int leftspeed = 0;

uint32_t time_last = 0;
uint32_t time_now = 0;
uint32_t time_led = 0;

void setup()
{
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
}

// void led_blinker()
// {
//   static int global_led_cnt = 0;
// }

int global_led_state = 0;
int blinker_cnt = 0;

void loop()
{
  // 每过10s拉低充电模块，防止电被关
  time_now = millis();
  if (time_now - time_last > 5000)
  {
    time_last = millis();
    digitalWrite(POWER_PIN, LOW);
    delay(50);
    digitalWrite(POWER_PIN, HIGH);
  }

  if (global_led_state == 0)
  {
    // LED闪烁提示现在的状态
    if (time_now - time_led > 100)
    {
      time_led = millis();

      if (digitalRead(USER_LED_PIN) == LOW)
      {
        digitalWrite(USER_LED_PIN, HIGH);
      }
      else
      {
        digitalWrite(USER_LED_PIN, LOW);
      }
      if (digitalRead(MODULE_LED_PIN) == LOW)
      {
        digitalWrite(MODULE_LED_PIN, HIGH);
      }
      else
      {
        digitalWrite(MODULE_LED_PIN, LOW);
      }

      blinker_cnt++;
      if (blinker_cnt >= robotID*2)
      {
        blinker_cnt = 0;
        global_led_state = 1;
      }
    }
  }
  else
  {
    if (time_now - time_led > 2000)
    {
      time_led = millis();
      global_led_state = 0;
      digitalWrite(USER_LED_PIN, HIGH);
      digitalWrite(MODULE_LED_PIN, HIGH);
    }
  }

  // // LED闪烁提示现在的状态
  // if (time_now - time_led > 1000)
  // {
  //   time_led = millis();
  //   if (digitalRead(USER_LED_PIN) == LOW)
  //   {
  //     digitalWrite(USER_LED_PIN, HIGH);
  //   }
  //   else
  //   {
  //     digitalWrite(USER_LED_PIN, LOW);
  //   }
  //   if (digitalRead(MODULE_LED_PIN) == LOW)
  //   {
  //     digitalWrite(MODULE_LED_PIN, HIGH);
  //   }
  //   else
  //   {
  //     digitalWrite(MODULE_LED_PIN, LOW);
  //   }
  // }

  // 按键检测，检测按键的逻辑
  if (digitalRead(USER_BTN_PIN) == LOW)
  {
    Serial.println("USER_BTN_PIN ");
  }

  // 接收UDP数据，进行数据交互
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
  }

  // 心跳检测，
  if (!heartbeat_check(time_since_last_msg))
  {
    leftspeed = 0;
    rightspeed = 0;
  }

  // 更新速度
  lMotor.setSpeed(leftspeed);
  rMotor.setSpeed(rightspeed);
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
  delay(10);

  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  // WiFi.hostname(deviceName);
  WiFi.config(staticIP, subnet, gateway, dns);
  WiFi.begin(ssid, password);

  WiFi.mode(WIFI_STA);

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
    wifi_error_cnt++;
    if (wifi_error_cnt >= 10)
    {
      break;
    }
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}
