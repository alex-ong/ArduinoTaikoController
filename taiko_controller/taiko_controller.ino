#include "AnalogReadNow.h"
#include "FastADC.h"
#include "LEDKeyboard.h"
#include "HitTracker.h"
#include <Keyboard.h>
#define FASTADC
#define DEBUG_STATE

const float min_threshold = 20;
const long cd_length = 50000;
const float k_threshold = 3.0;
const float k_decay = 0.9;

const int pin[4] = {A2, A0, A1, A3};
const int key[4] = {'d', 'f', 'j', 'k'};

const float sens[4] = {1.0, 1.4, 1.2, 1.1};

float threshold = 0;
int rawValues[4] = {0, 0, 0, 0};
float sensorValues[4] = {0, 0, 0, 0};
long cooldown = 0;

LEDKeyboard ledKeyboard;
HitTracker hitTracker;

typedef unsigned long time_t;
time_t timeAtStartOfRefresh = 0;
time_t deltaTime = 0;

void SamplePiezos() {
  int prev[4] = {rawValues[0], rawValues[1], rawValues[2], rawValues[3]};
  rawValues[0] = analogRead(pin[0]);
  rawValues[1] = analogRead(pin[1]);
  rawValues[2] = analogRead(pin[2]);
  rawValues[3] = analogRead(pin[3]);
  
  // this bit here is a weird...
  // its a decay thing...
  for (int i=0; i<4; ++i) {
    sensorValues[i] = abs(rawValues[i] - prev[i]) * sens[i];
  }
}

// returns cooldown
inline long update_cooldown(time_t deltaTime)
{
  cooldown = max(0L, cooldown - deltaTime);
  if (cooldown == 0) ledKeyboard.release_all();
  return cooldown;
}

void SendDebugState() {
#ifdef DEBUG_STATE
  Serial.print("★ RAW: ");
  for (int i = 0; i < 4; i++) {
    Serial.print(rawValues[i]);
    if (i < 3) Serial.print(", ");
  }
  Serial.print(" | SENSOR: ");
  for (int i = 0; i < 4; i++) {
    Serial.print(hitTracker.getCounter(i), 4);
    if (i < 3) Serial.print(", ");
  }
  Serial.print(" | KEYS: ");
  for (int i = 0; i < 4; i++) {
    Serial.print(ledKeyboard.isPressed(i) ? "1" : "0");
    if (i < 3) Serial.print(", ");
  }
  Serial.print(" | THRESH: ");
  Serial.print(threshold);
  Serial.println();
#endif
}

// This is a magic function called by Arduino framework once at startup.
// case matters. It MUST be "setup"
void setup() {
  SetFastADC();
  ledKeyboard.setup();
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  timeAtStartOfRefresh = micros();
  Serial.begin(115200);
}

inline void endloop()
{
  SendDebugState();
  SendLEDs();
  long delayBeforeNextRefresh = 300 - (micros() - timeAtStartOfRefresh);
  if(delayBeforeNextRefresh > 3) delayMicroseconds(delayBeforeNextRefresh);
}

/// This is a magic function called in a loop by arduino framework.
void loop() {
  time_t currentTime = micros();
  deltaTime = currentTime - timeAtStartOfRefresh;
  timeAtStartOfRefresh = currentTime;

  threshold = max(min_threshold, threshold * k_decay);
  SamplePiezos();
  
  if (update_cooldown(deltaTime) != 0)
  {
     threshold = 69;
     endloop();
     return;
  }

  if (hitTracker.isActive())
  {
    hitTracker.track(sensorValues[0], sensorValues[1], sensorValues[2],sensorValues[3]);
    hitTracker.update(deltaTime);
    if (hitTracker.isDone())
    {
      uint8_t maxIdx = hitTracker.getMaxIndex();
      ledKeyboard.press(maxIdx);
      cooldown = cd_length;  // Start cooldown after pressing
    } else {
      threshold = 120;
      endloop();
      return;
    }
  }

  float maxSensorValue = getMaxValue(sensorValues, 4);
  if (maxSensorValue > threshold)
  {
    hitTracker.startTracking(sensorValues[0],sensorValues[1],sensorValues[2],sensorValues[3]);
    threshold = maxSensorValue;
  }
  
  threshold = 100;
  endloop();
}

