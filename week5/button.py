from gpiozero import Button, LED
from signal import pause

button = Button(17)
led = LED(18)

button.when_pressed = led.on    # 괄호 없이 함수만 등록!
button.when_released = led.off

pause()