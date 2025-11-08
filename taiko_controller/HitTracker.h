#ifndef HITTRACKER_H
#define HITTRACKER_H

#include <Arduino.h>

class HitTracker {
private:
  static const long ACTIVE_TIME = 50000; // 50000us = 5ms
  
  int counters[4] = {0, 0, 0, 0};
  long activeTimeRemaining = 0;
  
public:
  HitTracker() {}
  
  void track(int v0, int v1, int v2, int v3) {
    counters[0] = max(counters[0], v0);
    counters[1] = max(counters[1], v1);
    counters[2] = max(counters[2], v2);
    counters[3] = max(counters[3], v3);
    
    if (activeTimeRemaining == 0) {
      activeTimeRemaining = ACTIVE_TIME;
    }
  }
  
  void update(long deltaTime) {
    activeTimeRemaining = max(0L, activeTimeRemaining - deltaTime);
  }
  
  bool isActive() const {
    return activeTimeRemaining > 0;
  }
  
  bool isDone() const {
    return !isActive();
  }
  
  uint8_t getMaxIndex() const {
    uint8_t maxIdx = 0;
    int maxVal = counters[0];
    
    for (uint8_t i = 1; i < 4; i++) {
      if (counters[i] > maxVal) {
        maxVal = counters[i];
        maxIdx = i;
      }
    }
    
    return maxIdx;
  }
  
  int getMaxValue() const {
    int maxVal = counters[0];
    for (uint8_t i = 1; i < 4; i++) {
      if (counters[i] > maxVal) {
        maxVal = counters[i];
      }
    }
    return maxVal;
  }
  
  void reset() {
    counters[0] = 0;
    counters[1] = 0;
    counters[2] = 0;
    counters[3] = 0;
    activeTimeRemaining = 0;
  }
};

#endif
