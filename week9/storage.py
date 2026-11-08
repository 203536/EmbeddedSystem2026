# 10주차 공통 모듈: 타임스탬프 · 검증 · CSV 저장 · SQLite 저장
# 다른 파일에서 import 해서 사용 (직접 실행하지 않음)
import csv
import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# ---------------- 설정 ----------------
KST = ZoneInfo("Asia/Seoul")      # 한국 표준시 (+09:00)
DEVICE_ID = "rpi-01"              # 이 장치의 이름
CSV_PATH = Path("environment.csv")
DB_PATH = Path("sensors.db")
TEMP_RANGE = (-40.0, 80.0)        # DHT22 데이터시트 측정 범위(℃)
HUM_RANGE = (0.0, 100.0)          # 상대습도 범위(%)

FIELDS = ["timestamp", "temperature", "humidity",
          "status", "device_id", "error_message"]


# ---------------- 시간 · 검증 ----------------
def now_text():
    """시간대가 포함된 ISO 8601 문자열. 예: 2026-07-25T14:30:00+09:00"""
    return datetime.now(KST).isoformat(timespec="seconds")


def validate(t, h):
    """값이 없거나 범위를 벗어나면 ValueError. 정상이면 소수 첫째 자리로 반올림"""
    if t is None or h is None:
        raise ValueError("missing value")
    if not (TEMP_RANGE[0] <= t <= TEMP_RANGE[1]):
        raise ValueError("temperature range")
    if not (HUM_RANGE[0] <= h <= HUM_RANGE[1]):
        raise ValueError("humidity range")
    return round(t, 1), round(h, 1)


def make_record(t, h, status, error=None):
    """스키마에 맞는 레코드(딕셔너리) 하나 만들기"""
    return {
        "timestamp": now_text(),
        "temperature": t,          # 실패 시 None (0으로 저장하지 않음)
        "humidity": h,
        "status": status,          # OK / ERROR
        "device_id": DEVICE_ID,
        "error_message": error,    # 정상이면 None
    }


def read_record(sensor):
    """센서를 한 번 읽어 검증까지 끝난 레코드를 반환"""
    try:
        t, h = validate(sensor.temperature, sensor.humidity)
        return make_record(t, h, "OK")
    except (RuntimeError, ValueError) as exc:   # 측정 실패 + 비정상 값
        return make_record(None, None, "ERROR", str(exc))


# ---------------- CSV ----------------
def append_csv(record, path=CSV_PATH):
    """CSV 끝에 한 줄 추가. 파일이 처음이면 헤더부터 쓴다"""
    new_file = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if new_file:
            writer.writerow(FIELDS)
        writer.writerow([record[f] for f in FIELDS])
        file.flush()               # Python 버퍼 → OS로 바로 넘김


# ---------------- SQLite ----------------
CREATE_SQL = """
CREATE TABLE IF NOT EXISTS readings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT NOT NULL,         -- ISO 8601 + 타임존
  temperature REAL,                -- 측정 실패 시 NULL
  humidity REAL,                   -- 측정 실패 시 NULL
  status TEXT NOT NULL,            -- OK / ERROR
  device_id TEXT NOT NULL,
  error_message TEXT
)
"""

INSERT_SQL = """
INSERT INTO readings (timestamp, temperature, humidity,
                      status, device_id, error_message)
VALUES (?, ?, ?, ?, ?, ?)
"""


def open_db(path=DB_PATH):
    """DB 연결 + 테이블 준비"""
    conn = sqlite3.connect(path)
    conn.execute(CREATE_SQL)
    conn.commit()
    return conn


def insert_record(conn, record):
    """레코드 1개 저장. 성공하면 commit, 예외면 rollback"""
    try:
        with conn:
            conn.execute(INSERT_SQL, [record[f] for f in FIELDS])
    except sqlite3.Error as exc:
        print("DB 저장 오류:", exc)
        raise
