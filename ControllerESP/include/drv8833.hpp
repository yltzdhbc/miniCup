#include "Arduino.h"

class DRV8833_DRIVER
{
private:
  int PWM1_PIN;
  int PWM2_PIN;

public:
  DRV8833_DRIVER(int PIN1, int PIN2)
  {
    pinMode(PIN1, OUTPUT);
    pinMode(PIN2, OUTPUT);
    PWM1_PIN = PIN1;
    PWM2_PIN = PIN2;
  }

  // pwm: -127--+127
  void setSpeed(int pwm)
  {
    if (pwm >= 0)
    {
      analogWrite(PWM1_PIN, 127 - abs(pwm));
      analogWrite(PWM2_PIN, 127 + abs(pwm));
    }
    else if (pwm < 0)
    {
      analogWrite(PWM1_PIN, 127 + abs(pwm));
      analogWrite(PWM2_PIN, 127 - abs(pwm));
    }
  }
};