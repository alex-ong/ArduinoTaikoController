#include "LED.h"
#include "AnalogReadNow.h"
#include "FastADC.h"
#include <Keyboard.h>
#define FASTADC
#define DEBUG_STATE

const int min_threshold = 20;
const long cd_length = 50000;
const float k_threshold = 3.0;
const float k_decay = 0.9;

const int pin[4] = {A2, A0, A1, A3};
const int key[4] = {'d', 'f', 'j', 'k'};

const float sens[4] = {1.0, 1.4, 1.0, 1.1};

float threshold = 0;
int rawValues[4] = {0, 0, 0, 0};
float sensorValues[4] = {0, 0, 0, 0};
long cooldowns[4] = {0, 0, 0, 0};
bool keyIsDown[4] = {false, false, false, false};

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


void press(uint8_t index)
{
  if (keyIsDown[index]) 
  {
    return;
  }
  Keyboard.press(key[index]);
  
  UpdateLEDColor(index, true);
  keyIsDown[index] = true;
}

void release(uint8_t index)
{
  if (!keyIsDown[index]) 
  {
    return;
  }

  Keyboard.release(key[index]);
  UpdateLEDColor(index, false);
  keyIsDown[index] = false;
}

void release_on_cooldown(time_t deltaTime)
{
  for (int i = 0; i != 4; ++i) {
    if (cooldowns[i] > 0) {
      cooldowns[i] -= deltaTime;
      if (cooldowns[i] <= 0) {
        cooldowns[i] = 0;
        release(i);
      }
    }
  }
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
    Serial.print(sensorValues[i], 4);
    if (i < 3) Serial.print(", ");
  }
  Serial.print(" | KEYS: ");
  for (int i = 0; i < 4; i++) {
    Serial.print(keyIsDown[i] ? "1" : "0");
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
  SetupLEDs();
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  Keyboard.begin();

  timeAtStartOfRefresh = micros();
  Serial.begin(115200);
}

/// This is a magic function called in a loop by arduino framework.
void loop() {
  time_t currentTime = micros();
  deltaTime = currentTime - timeAtStartOfRefresh;
  timeAtStartOfRefresh = currentTime;
  
  SamplePiezos(); 
  threshold *= k_decay;

  release_on_cooldown(deltaTime);
  
  // todo: use "inline" function and pointers
  int maxSensorIndex = 0;
  float maxSensorValue = 0;
  
  for (int i = 0; i < 4; ++i) {
    if (sensorValues[i] > maxSensorValue && sensorValues[i] > threshold) {
      maxSensorValue = sensorValues[i];
      maxSensorIndex = i;
    }
  }

  if (maxSensorValue > threshold && maxSensorValue > min_threshold) {
    if (cooldowns[maxSensorIndex] == 0) {
        press(maxSensorIndex);
    }
    // todo: non-global cooldown
    for (int i = 0; i < 4; ++i) cooldowns[i] = cd_length;
    threshold = max(threshold, maxSensorValue * k_threshold);
  }

  SendDebugState();
  SendLEDs();
  long delayBeforeNextRefresh = 300 - (micros() - timeAtStartOfRefresh);
  if(delayBeforeNextRefresh > 3) delayMicroseconds(delayBeforeNextRefresh);
}
