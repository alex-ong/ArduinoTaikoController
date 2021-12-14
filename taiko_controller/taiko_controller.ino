#include "LED.h"
#include "AnalogReadNow.h"
#include "FastADC.h"
#define FASTADC
//#define DEBUG_OUTPUT
//#define DEBUG_OUTPUT_LIVE
//#define DEBUG_TIME
#define DEBUG_DATA

#define ENABLE_KEYBOARD
//#define ENABLE_NS_JOYSTICK

//#define HAS_BUTTONS

#ifdef ENABLE_KEYBOARD
#include <Keyboard.h>
#endif

#ifdef ENABLE_NS_JOYSTICK
#include "Joystick.h"
const int led_pin[4] = {8, 9, 10, 11};
const int sensor_button[4] = {SWITCH_BTN_ZL, SWITCH_BTN_LCLICK, SWITCH_BTN_RCLICK, SWITCH_BTN_ZR};
#endif


const int min_threshold = 20;
const long cd_length = 50000;
const float k_threshold = 3.0;
const float k_decay = 0.9;

const int pin[4] = {A2, A0, A1, A3};
const int key[4] = {'d', 'f', 'j', 'k'};

const float sens[4] = {1.0, 1.4, 1.0, 1.1};

float threshold = 0;
int raw[4] = {0, 0, 0, 0};
float level[4] = {0, 0, 0, 0};
long cd[4] = {0, 0, 0, 0};
bool down[4] = {false, false, false, false};
#ifdef ENABLE_NS_JOYSTICK
uint8_t down_count[4] = {0, 0, 0, 0};
#endif

typedef unsigned long time_t;
time_t t0 = 0;
time_t dt = 0;

void sample() {
  int prev[4] = {raw[0], raw[1], raw[2], raw[3]};
  raw[0] = analogRead(pin[0]);
  raw[1] = analogRead(pin[1]);
  raw[2] = analogRead(pin[2]);
  raw[3] = analogRead(pin[3]);
  for (int i=0; i<4; ++i)
    level[i] = abs(raw[i] - prev[i]) * sens[i];
}


void setup() {
  SetFastADC();
  SetupLEDs();
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
#ifdef ENABLE_NS_JOYSTICK
  for (int i = 0; i < 8; ++i) pinMode(i, INPUT_PULLUP);
  for (int i = 0; i < 4; ++i) {  digitalWrite(led_pin[i], HIGH); pinMode(led_pin[i], OUTPUT); }
#endif
#ifdef ENABLE_KEYBOARD
  Keyboard.begin();
#endif
  t0 = micros();
  Serial.begin(115200);
}



void press(uint8_t index)
{
#ifdef DEBUG_DATA
  Serial.print(level[0], 1);
  Serial.print("\t");
  Serial.print(level[1], 1);
  Serial.print("\t");
  Serial.print(level[2], 1);
  Serial.print("\t");
  Serial.print(level[3], 1);
  Serial.print("\n");
#endif

#ifdef ENABLE_KEYBOARD    
  Keyboard.press(key[index]);
#endif
  down[index] = true;
  UpdateLEDColor(index, true);
#ifdef ENABLE_NS_JOYSTICK
  if (down_count[index] <= 2) down_count[index] += 2;
#endif
  
}

void release(uint8_t index)
{
  if (down[index]) {
#ifdef ENABLE_KEYBOARD
    Keyboard.release(key[index]);
    UpdateLEDColor(index, false);

#endif
  }
  down[index] = false; 
}

void release_on_cd()
{
  //release on cooldown
  for (int i = 0; i != 4; ++i) {
    if (cd[i] > 0) {
      cd[i] -= dt;
      if (cd[i] <= 0) {
        cd[i] = 0;
        if (down[i]) {
          release(i);
        }
      }
    }
  }
}

void debug_all()
{
  #ifdef DEBUG_OUTPUT
  static bool printing = false;
#ifdef DEBUG_OUTPUT_LIVE
  if (true)
#else
  if (printing || (/*down[0] &&*/ threshold > min_threshold))
#endif
  {
    printing = true;
    Serial.print(level[0], 1);
    Serial.print("\t");
    Serial.print(level[1], 1);
    Serial.print("\t");
    Serial.print(level[2], 1);
    Serial.print("\t");
    Serial.print(level[3], 1);
    Serial.print("\t| ");
    Serial.print(cd[0] == 0 ? "  " : down[0] ? "# " : "* ");
    Serial.print(cd[1] == 0 ? "  " : down[1] ? "# " : "* ");
    Serial.print(cd[2] == 0 ? "  " : down[2] ? "# " : "* ");
    Serial.print(cd[3] == 0 ? "  " : down[3] ? "# " : "* ");
    Serial.print("|\t");
    Serial.print(threshold, 1);
    Serial.println();
    if(threshold <= 5){
      Serial.println();
      printing = false;
    }
  } 
#endif

}

void loop() {
  //loop_test2(); return;
  
  time_t t1 = micros();
  dt = t1 - t0;
  t0 = t1;
  
  sample(); 
  threshold *= k_decay;

  release_on_cd();
  
  int i_max = 0;
  int level_max = 0;
  
  for (int i = 0; i < 4; ++i) {
    if (level[i] > level_max && level[i] > threshold) {
      level_max = level[i];
      i_max = i;
    }
  }

  if (level_max > threshold && level_max > min_threshold) {
    if (cd[i_max] == 0) {
      if (!down[i_max]) {
        press(i_max);        
      }
    }
    for (int i = 0; i < 4; ++i) cd[i] = cd_length;
    threshold = max(threshold, level_max * k_threshold);
  }


  
  debug_all();
  SendLEDs();
  long ddt = 300 - (micros() - t0);
  if(ddt > 3) delayMicroseconds(ddt);
  
}
