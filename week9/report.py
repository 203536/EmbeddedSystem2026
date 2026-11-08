# 10주차 미션 C: 하루 통계 HTML 리포트 + CSV 내보내기 + 행 수 비교
# 실행: python report.py                 (오늘)
#       python report.py 2026-07-25      (날짜 지정)
# 결과: reports/report_날짜.html, reports/export_날짜.csv
import csv
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from storage import KST, open_db

day = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else datetime.now(KST).date()   # 한국 시간 기준 오늘
start_ts = f"{day}T00:00:00+09:00"
end_ts = f"{day + timedelta(days=1)}T00:00:00+09:00"

conn = open_db()
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
rows = conn.execute("""
SELECT timestamp, temperature, humidity
FROM readings
WHERE status = 'OK' AND timestamp >= ? AND timestamp < ?
ORDER BY timestamp ASC
""", (start_ts, end_ts)).fetchall()
conn.close()


def fmt(value):
    return "-" if value is None else f"{value:.1f}"   # 데이터 0건이면 None


html = f"""<!doctype html>
<html lang="ko"><meta charset="utf-8">
<title>{day} 환경 리포트</title>
<h1>{day} 환경 리포트</h1>
<ul>
 <li>평균 온도: {fmt(avg_t)} °C</li>
 <li>최저 / 최고: {fmt(min_t)} / {fmt(max_t)} °C</li>
 <li>평균 습도: {fmt(avg_h)} %</li>
 <li>정상 {count}건 · 오류 {errors}건</li>
</ul>
<table border="1" cellpadding="4">
 <tr><th>시각</th><th>온도(°C)</th><th>습도(%)</th></tr>
 {"".join(f"<tr><td>{ts}</td><td>{t}</td><td>{h}</td></tr>" for ts, t, h in rows)}
</table>
</html>"""

out_dir = Path("reports")
out_dir.mkdir(exist_ok=True)
report_path = out_dir / f"report_{day}.html"
report_path.write_text(html, encoding="utf-8")

export_path = out_dir / f"export_{day}.csv"
with export_path.open("w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["timestamp", "temperature", "humidity"])
    writer.writerows(rows)

print("리포트:", report_path.resolve())
print("내보내기:", export_path.resolve())
check = "일치" if len(rows) == count else "불일치!"
print(f"[교차 검증] 리포트 정상 {count}건 · 내보낸 CSV {len(rows)}행 → {check}")
