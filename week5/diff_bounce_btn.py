_from gpiozero import Button, LED
from signal import pause

button = Button(17, bounce_time=None)   # 두 번째 실험은 0.1로 변경
led = LED(18)
count = 0

def on_press():
    global count
    count += 1
    led.on()
    print(f"count={count}")

button.when_pressed = on_press
button.when_released = led.off

try:
    pause()
finally:
    led.off(); button.close(); led.close()