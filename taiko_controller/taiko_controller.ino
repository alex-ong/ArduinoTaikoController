#include "AnalogReadNow.h"
#include "FastADC.h"
#include "LEDKeyboard.h"
#include "HitTracker.h"
#include <Keyboard.h>
#define FASTADC
#define DEBUG_STATE

const float min_threshold = 20;
const long cd_length = 80000;
const float k_threshold = 3.0;
const float k_decay = 0.95;

const int pin[4] = {A2, A0, A1, A3};
const int key[4] = {'d', 'f', 'j', 'k'};

const float sens[4] = {1.0, 1.0, 0.4, 1.0};

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
  for (int i = 0; i < 4; i++) {
    int prev = rawValues[i];
    rawValues[i] = analogRead(pin[i]);
    sensorValues[i] = abs(rawValues[i] - prev) * sens[i];
  }
}

// returns cooldown
inline long update_cooldown(time_t deltaTime)
{
  // Typecast deltaTime to long to avoid unsigned-long and long subtraction issue
  cooldown = max(0L, cooldown - (long)deltaTime);
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
     endloop();
     return;
  }

  if (hitTracker.isActive())
  {
    hitTracker.track(sensorValues[0], sensorValues[1], sensorValues[2],sensorValues[3]);
    hitTracker.update((long)deltaTime);
    if (hitTracker.isDone())
    {
      uint8_t maxIdx = hitTracker.getMaxIndex();
      ledKeyboard.press(maxIdx);
      cooldown = cd_length;  // Start cooldown after pressing
      hitTracker.reset();
    } else {
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
  
  endloop();
}

