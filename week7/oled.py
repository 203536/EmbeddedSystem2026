# 6주차 통합 실습: DHT22 온·습도 측정 → 검증 → SSD1306 OLED 표시 → CSV 기록
# 실행: source .venv/bin/activate 후  python sensor_oled.py   (종료: Ctrl+C)
import csv
import time
from datetime import datetime

import board
import busio
import adafruit_dht
import adafruit_ssd1306

# ---------------- 설정 ----------------
OLED_ADDR = 0x3C          # i2cdetect -y 1 에서 확인한 주소로 바꾸기
INTERVAL = 2.0            # DHT22 최소 측정 간격 2초
TEMP_RANGE = (-40, 80)    # DHT22 데이터시트 측정 범위(℃)
HUM_RANGE = (0, 100)      # 상대습도 범위(%RH)
MAX_DT = 2.0              # 2초 사이 허용 온도 변화(℃)
MAX_DH = 5.0              # 2초 사이 허용 습도 변화(%RH)
JUMP_ACCEPT = 3           # 급변이 3회 연속이면 실제 변화로 인정
WARN_T, WARN_H = 30, 70   # 미션 C 경고 기준
TEST_INJECT = 0           # 0=끔, 5=5회마다 150℃ 가짜 값 주입(비정상 경로 시험용)

# ---------------- 초기화 ----------------
sensor = adafruit_dht.DHT22(board.D17, use_pulseio=False)   # DATA = GPIO17(물리 핀 11)
i2c = busio.I2C(board.SCL, board.SDA)                       # SCL 핀 5, SDA 핀 3
display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=OLED_ADDR)

state = {"prev": None, "jumps": 0}   # 마지막 정상값, 연속 급변 횟수
count = {"OK": 0, "WARN": 0, "FAIL": 0, "BAD": 0}


def judge(t, h):
    """받은 숫자가 믿을 만한지 판정. (결과, 이유) 반환"""
    if t is None or h is None:
        return "BAD", "No value"
    if not (TEMP_RANGE[0] <= t <= TEMP_RANGE[1] and HUM_RANGE[0] <= h <= HUM_RANGE[1]):
        return "BAD", "Out of range"
    prev = state["prev"]
    if prev and (abs(t - prev[0]) > MAX_DT or abs(h - prev[1]) > MAX_DH):
        state["jumps"] += 1
        if state["jumps"] < JUMP_ACCEPT:
            return "BAD", "Sudden jump"
        # 3회 연속 급변이면 순간 오류가 아니라 실제 환경 변화로 보고 받아들임
    state["prev"] = (t, h)
    state["jumps"] = 0
    if t >= WARN_T or h >= WARN_H:
        return "WARN", "Too hot/humid"
    return "OK", ""


def show(lines):
    display.fill(0)                          # 이전 화면 지우기(잔상 방지)
    for i, line in enumerate(lines):
        display.text(line[:21], 0, i * 13, 1)  # 한 줄 최대 21자, 13px 간격
    display.show()


def counts_line():
    ok = count["OK"] + count["WARN"]
    return f"OK{ok} F{count['FAIL']} B{count['BAD']}"


log = open("log.csv", "a", newline="")
writer = csv.writer(log)
n = 0

try:
    show(["Embedded System", "DHT22 + OLED", "Starting..."])
    while True:
        n += 1
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            t = sensor.temperature
            h = sensor.humidity
            if TEST_INJECT and n % TEST_INJECT == 0:
                t = 150.0                     # 일부러 넣은 비정상 값
            result, reason = judge(t, h)
        except RuntimeError as error:          # 통신 실패·시간 초과
            t = h = None
            result, reason = "FAIL", str(error)

        count[result] += 1

        if result in ("OK", "WARN"):
            show([
                f"T: {t:.1f} C",
                f"H: {h:.1f} %RH",
                "!! WARNING !!" if result == "WARN" else "Status: OK",
                counts_line(),
            ])
        elif result == "FAIL":
            show(["Sensor Error", reason, "Retry in 2s", counts_line()])
        else:  # BAD
            raw = f"T{t} H{h}" if t is not None else "raw: None"
            show(["Bad value-excluded", reason, raw, counts_line()])

        print(f"{n:03d} {now} | {result:4} | T={t} H={h} | {reason}")
        writer.writerow([now, result, t, h, reason])
        log.flush()
        time.sleep(INTERVAL)
except KeyboardInterrupt:
    print("\n종료 요약:", count)
finally:
    display.fill(0)
    display.show()
    sensor.exit()
    log.close()