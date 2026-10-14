from gpiozero import LED
from signal import pause

led = LED(17)
led.blink(
    on_time=0.2,
    off_time=0.8
)

try:
    pause()
finally:
    led.close()