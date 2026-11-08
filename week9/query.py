# 10주차 미션 B: 최신값 · 오늘 기간 조회 · 평균/최소/최대/개수
# 실행: python query.py                  (오늘)
#       python query.py 2026-07-25       (날짜 지정)
import sys
from datetime import date, datetime, timedelta

from storage import KST, open_db

day = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else datetime.now(KST).date()   # 한국 시간 기준 오늘
start_ts = f"{day}T00:00:00+09:00"                      # 시작 포함
end_ts = f"{day + timedelta(days=1)}T00:00:00+09:00"    # 끝 미포함  → [start, end)

conn = open_db()

# 1) 최신 1건 (ERROR일 수도 있음)
latest = conn.execute("""
SELECT timestamp, temperature, humidity, status
FROM readings
ORDER BY timestamp DESC
LIMIT 1
""").fetchone()
print("[최신 기록]", latest if latest else "데이터 없음")

# 2) 기간 조회 (정상 값만)
rows = conn.execute("""
SELECT timestamp, temperature, humidity
FROM readings
WHERE status = 'OK' AND timestamp >= ? AND timestamp < ?
ORDER BY timestamp ASC
""", (start_ts, end_ts)).fetchall()
print(f"\n[{day} 정상 기록 {len(rows)}건]")
for ts, t, h in rows:
    print(f"  {ts}  {t:5.1f} ℃  {h:5.1f} %")

# 3) 통계
avg_t, min_t, max_t, avg_h, count = conn.execute("""
SELECT AVG(temperature), MIN(temperature), MAX(temperature),
       AVG(humidity), COUNT(*)
FROM readings
WHERE status = 'OK' AND timestamp >= ? AND timestamp < ?
""", (start_ts, end_ts)).fetchone()
errors = conn.execute("""
SELECT COUNT(*) FROM readings
WHERE status != 'OK' AND timestamp >= ? AND timestamp < ?
""", (start_ts, end_ts)).fetchone()[0]

print(f"\n[{day} 통계]")
if count == 0:
    print("  정상 기록이 없음")                # AVG는 None → 계산하지 않음
else:
    print(f"  평균 온도 {avg_t:.1f} ℃ · 최저 {min_t:.1f} ℃ · 최고 {max_t:.1f} ℃")
    print(f"  평균 습도 {avg_h:.1f} %")
print(f"  정상 {count}건 · 오류 {errors}건")

total = conn.execute("SELECT COUNT(*) FROM readings").fetchone()[0]
print(f"\n[교차 검증] DB 전체 {total}행  ← CSV 데이터 행 수와 같아야 함")
conn.close()
