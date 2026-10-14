from gpiozero import Button, LED
from signal import pause

button = Button(17, bounce_time=0.1, hold_time=2.0)
led = LED(18)

def pressed():  led.on();  print("눌림")
def released(): led.off(); print("뗌")
def held():
    print("2초 이상 누름")
    led.blink(on_time=0.1, off_time=0.1, n=3)  # 빠르게 3번 깜빡

button.when_pressed = pressed
button.when_released = released
button.when_held = held

try:
    pause()
finally:
    led.off(); button.close(); led.close()