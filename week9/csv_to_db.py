# 10주차 미션 A (보조): 1차시에 CSV만 쌓았다면, 같은 레코드를 SQLite로 옮긴다
# 실행: python csv_to_db.py
# 주의: 여러 번 실행하면 같은 기록이 중복 저장됨 → 다시 하려면 sensors.db를 지우고 실행
import csv

from storage import CSV_PATH, FIELDS, insert_record, open_db


def to_float(text):
    return float(text) if text else None    # 빈칸 → None → SQL NULL


conn = open_db()
n = 0
with CSV_PATH.open("r", newline="", encoding="utf-8") as file:
    for row in csv.DictReader(file):
        record = {f: (row[f] or None) for f in FIELDS}
        record["temperature"] = to_float(row["temperature"])
        record["humidity"] = to_float(row["humidity"])
        insert_record(conn, record)
        n += 1

db_count = conn.execute("SELECT COUNT(*) FROM readings").fetchone()[0]
conn.close()
print(f"CSV {n}행 옮김 · DB 전체 {db_count}행")
