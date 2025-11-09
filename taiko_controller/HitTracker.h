#ifndef HITTRACKER_H
#define HITTRACKER_H

#include <Arduino.h>

float getMaxValue(float* values, size_t length)
{
  float maxVal = values[0];
  for (size_t i = 1; i < length; ++i) {
    if (values[i] > maxVal) {
      maxVal = values[i];
    }
  }
  return maxVal;
}

class HitTracker {
private:
  static const long ACTIVE_TIME = 15000; // 15000us = 15ms
  
  float counters[4] = {0, 0, 0, 0};
  long activeTimeRemaining = 0;
  
public:
  HitTracker() {}

  void track(float v0, float v1, float v2, float v3) {
    counters[0] = max(counters[0], v0);
    counters[1] = max(counters[1], v1);
    counters[2] = max(counters[2], v2);
    counters[3] = max(counters[3], v3);
  }
  
  void update(long deltaTime) {
    activeTimeRemaining = max(0L, activeTimeRemaining - deltaTime);
  }
  
  bool isActive() const {
    return activeTimeRemaining > 0;
  }
  
  bool isDone() const {
    return activeTimeRemaining == 0;
  }
  
  uint8_t getMaxIndex() const {
    uint8_t maxIdx = 0;
    float maxVal = counters[0];
    
    for (uint8_t i = 1; i < 4; i++) {
      if (counters[i] > maxVal) {
        maxVal = counters[i];
        maxIdx = i;
      }
    }
    
    return maxIdx;
  }

  float getMaxValue() const {
    float maxVal = counters[0];
    for (uint8_t i = 1; i < 4; i++) {
      if (counters[i] > maxVal) {
        maxVal = counters[i];
      }
    }
    return maxVal;
  }
  
  void startTracking(float v0, float v1, float v2, float v3) {
    counters[0] = v0;
    counters[1] = v1;
    counters[2] = v2;
    counters[3] = v3;
    activeTimeRemaining = ACTIVE_TIME;
  }
  void reset() {
    for (uint8_t i = 0; i < 4; i++) {
      counters[i] = 0;
    }
  }

  float getCounter(uint8_t index) const {
    return counters[index];
  }
};

#endif
