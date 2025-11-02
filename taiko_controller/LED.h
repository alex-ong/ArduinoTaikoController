#include <FastLED.h>
#define USE_WS2812B 1
#define LED_PIN     15
#define NUM_LEDS    9+12+12

CRGB leds[NUM_LEDS];
CRGB RED = CRGB(128,0,0);
CRGB BLUE = CRGB(0,0,128);
CRGB BLACK = CRGB(0,0,0);
CRGB led_colors[] = {BLUE,RED,RED,BLUE};

//LED settings.
uint8_t firstled[4] = {0, 9, 21, NUM_LEDS};  //middle, right, left
bool needLEDUpdate = false;
bool muteLEDs = false;
bool is_led_on[]= {false, false, false, false};

void UpdateLEDColor(uint8_t button_idx, bool pressed)
{
  is_led_on[button_idx] = pressed;
  CRGB color = led_colors[button_idx];
  if (!pressed) color = BLACK;
  // todo: update region rather than all
  for (int i = 0; i < NUM_LEDS; i++)
  {
    leds[i] = color;
  }
  needLEDUpdate = true;
}

void SendLEDs()
{
  if (!needLEDUpdate) 
  {
    return;
  }

  #if USE_WS2812B
    FastLED.show();
  #endif
  needLEDUpdate = false;
}

void SetupLEDs()
{
  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.show();
}
