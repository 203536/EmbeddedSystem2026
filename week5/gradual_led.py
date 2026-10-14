from gpiozero import PWMLED
from time import sleep

led = PWMLED(17)
try:
    for value in [0.0, 0.25, 0.5, 0.75, 1.0]:
        led.value = value
        print(f"duty={value:.2f}")
        sleep(2)

    led.pulse(fade_in_time=1, fade_out_time=1)
    sleep(6)
finally:
    led.close()