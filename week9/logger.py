# 10주차 실습 (미션 1 · 2 · A): DHT22를 5초마다 측정 → 검증 → CSV + SQLite 이중 저장
# 실행: source .venv/bin/activate 후  python logger.py          (기본 30개 기록)
#       python logger.py --count 50 --interval 5               (개수·간격 변경)
#       python logger.py --csv-only                           (1차시: CSV만 저장)
# 종료: Ctrl+C (남은 기록을 DB에 다 쓰고 끝남)
import argparse
import threading
import time
from queue import Queue

import board
import adafruit_dht

from storage import append_csv, insert_record, open_db, read_record

parser = argparse.ArgumentParser()
parser.add_argument("--count", type=int, default=30, help="기록할 개수")
parser.add_argument("--interval", type=float, default=5.0, help="측정 간격(초), 최소 2")
parser.add_argument("--csv-only", action="store_true", help="SQLite 없이 CSV만 저장")
args = parser.parse_args()
interval = max(args.interval, 2.0)          # DHT22 최소 측정 간격 2초

# ---------------- DB 저장 스레드 (9주차 Queue 연결) ----------------
records = Queue(maxsize=200)                # 대기 레코드 최대 200개


def db_writer():
    conn = open_db()                        # 이 스레드 전용 연결
    try:
        while True:
            record = records.get()          # 항목이 올 때까지 대기
            try:
                if record is None:          # 종료 신호
                    break
                insert_record(conn, record)
            finally:
                records.task_done()
    finally:
        conn.close()


writer = None
if not args.csv_only:
    writer = threading.Thread(target=db_writer)
    writer.start()                          # 저장 스레드를 먼저 시작

# ---------------- 측정 루프 ----------------
sensor = adafruit_dht.DHT22(board.D17, use_pulseio=False)   # DATA = GPIO17(물리 핀 11)
count = {"OK": 0, "ERROR": 0}

try:
    for n in range(1, args.count + 1):
        record = read_record(sensor)
        count[record["status"]] += 1

        append_csv(record)                  # CSV는 이 스레드에서 바로
        if writer:
            records.put(record)             # SQLite는 저장 스레드에 맡김

        print(f"{n:03d} {record['timestamp']} | {record['status']:5} | "
              f"T={record['temperature']} H={record['humidity']} | "
              f"{record['error_message'] or ''}")
        if n < args.count:
            time.sleep(interval)
except KeyboardInterrupt:
    print("\n중단됨")
finally:
    if writer:
        records.put(None)                   # 기존 레코드 뒤에 종료 신호
        writer.join()                       # 남은 기록을 다 쓸 때까지 대기
    sensor.exit()
    print("저장 요약:", count)
