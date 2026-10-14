from gpiozero import LED
from time import sleep

led = LED(17)

def show_ok():                 # 정상: 느린 점멸, 장시간 확인하기 편한 패턴
    led.blink(1.0, 1.0)

def show_warning():            # 경고: 빠른 점멸, 주의가 필요한 상태
    led.blink(0.2, 0.2)

def show_error():              # 오류: 세 번 점멸 후 긴 휴지
    led.off()
    for _ in range(3):
        led.on();  sleep(0.1)
        led.off(); sleep(0.1)
    sleep(1.5)

try:
    while True:
        print("정상")
        show_ok();      sleep(6)    # 느린 점멸 6초

        print("경고")
        show_warning(); sleep(4)    # 빠른 점멸 4초

        print("오류")
        for _ in range(2):          # 3번 깜빡이고 쉬기를 2번 반복
            show_error()
except KeyboardInterrupt:
    led.off()