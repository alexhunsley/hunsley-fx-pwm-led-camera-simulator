## 25 fps base

Assuming we're using shutter angle of 180°:

<div class="spaced-columns-table">
{{< centered-table border="1px" >}}

| LED PWM | Example device/class | Base rate OK? | Ideal crank FPS | Maybe crank FPS |
| ---: | --- | :---: | --- | --- |
| 400 Hz | old WS2812/WS2812B | ❌ | - | - |
| 580 Hz* | APA102 global brightness | ❌ | - | - |
| 1 kHz | some SK6812 variants | ✅ | - | 30 |
| 1.2 kHz | SK6812 | ✅ | 30, 40 | - |
| 2 kHz | WS2813/14, newer WS2812 | ✅ | 40, 50 | 30, 48, 60 |
| 2.5 kHz | WS2801 class | ✅ | 50 | 30, 40, 48, 60, 72 |
| 4.7 kHz | SK9822 | ✅ | 50 | 30, 40, 48, 60, 72, 96, 100, 120, 144 |
| 8 kHz | GS8208 / CS8812 class | ✅ | 40, 50, 100, 200 | 30, 48, 60, 72, 96, 120, 144, 240 |
| 10 kHz | WS2816B class | ✅ | 40, 50, 100, 200 | 30, 48, 60, 72, 96, 120, 144, 240 |
| 19.2 kHz | APA102 RGB PWM | ✅ | 30, 40, 48, 50, 60, 96, 100, 120, 200, 240 | 72, 144 |
| 20 kHz | generic high-frequency PWM | ✅ | 40, 50, 100, 200 | 30, 48, 60, 72, 96, 120, 144, 240 |
| 26 kHz | HD107S class | ✅ | 40, 50, 100, 200 | 30, 48, 60, 72, 96, 120, 144, 240 |
| 27 kHz | HD108 class | ✅ | 30, 50, 60, 100 | 40, 48, 72, 96, 120, 144, 200, 240 |

{{< /centered-table >}}
</div>

**Comments:** At 25 fps there are no good PWM LED options below 1 kHz PWM.

**Ideal crank FPS** *means at least 15 nominal PWM cycles[^1] per exposure[^2] and an integer number of PWM cycles per exposure.*

**Maybe crank FPS** *means at least 15 nominal PWM cycles per exposure, but not an integer number of cycles.*

\* APA102's ~580 Hz figure refers to global-brightness modulation rather than its normal RGB PWM.
