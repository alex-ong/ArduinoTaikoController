#ifndef LEDKEYBOARD_H
#define LEDKEYBOARD_H

#include <Keyboard.h>
#include "LED.h"

class LEDKeyboard {
private:
  bool keyIsDown[4] = {false, false, false, false};
  const int keys[4] = {'d', 'f', 'j', 'k'};

public:
  LEDKeyboard() {}
  
  void setup() {
    Keyboard.begin();
    SetupLEDs();
  }
  
  void press(uint8_t index) {
    if (keyIsDown[index]) return;
    // Keyboard.press(keys[index]);
    UpdateLEDColor(index, true);
    keyIsDown[index] = true;
  }
  
  void release(uint8_t index) {
    if (!keyIsDown[index]) return;
    // Keyboard.release(keys[index]);
    UpdateLEDColor(index, false);
    keyIsDown[index] = false;
  }
  
  void release_all() {
    for (int i = 0; i < 4; ++i) {
      release(i);
    }
  }
  
  bool isPressed(uint8_t index) const {
    return keyIsDown[index];
  }
};
#endif
