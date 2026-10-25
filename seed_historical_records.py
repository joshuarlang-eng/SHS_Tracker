#!/usr/bin/env python3
"""
Seed historical school records from Commit Swimming into Sardis Swim database.
"""

import sqlite3
import uuid
from datetime import datetime
import db

HISTORICAL_INDIV_RECORDS = [
    # Women
    {"gender": "F", "event_name": "50 Free", "swimmer": "Aubrey Lang", "time_str": "31.01", "time_sec": 31.01, "date": "2023-10-20", "meet": "2023 Season Meet (10/20)"},
    {"gender": "F", "event_name": "100 Free", "swimmer": "Aubrey Lang", "time_str": "1:07.97", "time_sec": 67.97, "date": "2023-10-12", "meet": "2023 Season Meet (10/12)"},
    {"gender": "F", "event_name": "200 Free", "swimmer": "Aubrey Lang", "time_str": "2:29.52", "time_sec": 149.52, "date": "2023-10-20", "meet": "2023 Season Meet (10/20)"},
    {"gender": "F", "event_name": "500 Free", "swimmer": "Aubrey Lang", "time_str": "6:26.95", "time_sec": 386.95, "date": "2024-10-19", "meet": "2024 Season Meet (10/19)"},
    {"gender": "F", "event_name": "50 Back", "swimmer": "Cora Lang", "time_str": "34.27", "time_sec": 34.27, "date": "2025-09-11", "meet": "2025 Season Meet (09/11)"},
    {"gender": "F", "event_name": "100 Back", "swimmer": "Aubrey Lang", "time_str": "1:08.94", "time_sec": 68.94, "date": "2024-11-14", "meet": "2024 Season Meet (11/14)"},
    {"gender": "F", "event_name": "50 Breast", "swimmer": "Aubrey Lang", "time_str": "41.44", "time_sec": 41.44, "date": "2025-09-11", "meet": "2025 Season Meet (09/11)"},
    {"gender": "F", "event_name": "100 Breast", "swimmer": "Aubrey Lang", "time_str": "1:28.65", "time_sec": 88.65, "date": "2023-11-07", "meet": "2023 Season Meet (11/07)"},
    {"gender": "F", "event_name": "50 Fly", "swimmer": "Aubrey Lang", "time_str": "31.31", "time_sec": 31.31, "date": "2023-09-04", "meet": "2023 Season Meet (09/04)"},
    {"gender": "F", "event_name": "100 Fly", "swimmer": "Aubrey Lang", "time_str": "1:07.69", "time_sec": 67.69, "date": "2025-11-10", "meet": "2025 Season Meet (11/10)"},
    {"gender": "F", "event_name": "200 IM", "swimmer": "Aubrey Lang", "time_str": "2:29.92", "time_sec": 149.92, "date": "2024-11-14", "meet": "2024 Season Meet (11/14)"},

    # Men
    {"gender": "M", "event_name": "50 Free", "swimmer": "Caleb Battles", "time_str": "24.98", "time_sec": 24.98, "date": "2024-11-12", "meet": "2024 Season Meet (11/12)"},
    {"gender": "M", "event_name": "100 Free", "swimmer": "Caleb Battles", "time_str": "54.19", "time_sec": 54.19, "date": "2025-10-30", "meet": "2025 Season Meet (10/30)"},
    {"gender": "M", "event_name": "200 Free", "swimmer": "Caleb Battles", "time_str": "2:04.05", "time_sec": 124.05, "date": "2025-11-10", "meet": "2025 Season Meet (11/10)"},
    {"gender": "M", "event_name": "50 Back", "swimmer": "Caleb Battles", "time_str": "37.28", "time_sec": 37.28, "date": "2023-09-04", "meet": "2023 Season Meet (09/04)"},
    {"gender": "M", "event_name": "100 Back", "swimmer": "Caleb Battles", "time_str": "1:01.79", "time_sec": 61.79, "date": "2025-11-10", "meet": "2025 Season Meet (11/10)"},
    {"gender": "M", "event_name": "100 Breast", "swimmer": "Rowan Spears", "time_str": "1:16.72", "time_sec": 76.72, "date": "2025-09-11", "meet": "2025 Season Meet (09/11)"},
    {"gender": "M", "event_name": "100 Fly", "swimmer": "Caleb Battles", "time_str": "1:01.57", "time_sec": 61.57, "date": "2025-09-30", "meet": "2025 Season Meet (09/30)"},
    {"gender": "M", "event_name": "200 IM", "swimmer": "Caleb Battles", "time_str": "2:30.37", "time_sec": 150.37, "date": "2025-09-11", "meet": "2025 Season Meet (09/11)"},
]

HISTORICAL_RELAYS = [
    # Women
    {
        "gender": "F", "event_name": "200 Medley Relay", "time_str": "2:20.98", "time_sec": 140.98,
        "date": "2024-10-10", "meet": "2024 Season Meet (10/10)",
        "swimmers": ["A. Stewart", "Cora Lang", "Aubrey Lang", "Brooklynn Pfeiffer"]
    },
    {
        "gender": "F", "event_name": "200 Free Relay", "time_str": "2:09.66", "time_sec": 129.66,
        "date": "2023-11-07", "meet": "2023 Season Meet (11/07)",
        "swimmers": ["A. Stewart", "E. Cardona", "S. Spears", "Aubrey Lang"]
    },
    {
        "gender": "F", "event_name": "400 Free Relay", "time_str": "4:54.41", "time_sec": 294.41,
        "date": "2025-11-12", "meet": "2025 Season Meet (11/12)",
        "swimmers": ["A. Stewart", "Brooklynn Pfeiffer", "Cora Lang", "Aubrey Lang"]
    },
    # Men
    {
        "gender": "M", "event_name": "200 Medley Relay", "time_str": "2:09.01", "time_sec": 129.01,
        "date": "2025-10-14", "meet": "2025 Season Meet (10/14)",
        "swimmers": ["Joseph Ford", "Rowan Spears", "Caleb Battles", "B. Bleem"]
    },
    {
        "gender": "M", "event_name": "200 Free Relay", "time_str": "1:56.35", "time_sec": 116.35,
        "date": "2025-10-14", "meet": "2025 Season Meet (10/14)",
        "swimmers": ["Rowan Spears", "B. Bleem", "Joseph Ford", "Caleb Battles"]
    },
]

def get_or_create_swimmer(cur, name, gender):
    cur.execute("SELECT id FROM swimmers WHERE full_name = ?;", (name,))
    row = cur.fetchone()
    if row:
        return row[0]
    
    parts = name.split()
    first = parts[0] if parts else ""
    last = parts[-1] if len(parts) > 1 else ""
    sw_id = str(uuid.uuid4())
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        INSERT INTO swimmers (id, first_name, last_name, full_name, gender, grade, status, created_at)
        VALUES (?, ?, ?, ?, ?, '', 'Active', ?);
    """, (sw_id, first, last, name, gender, now))
    return sw_id

def get_or_create_meet(cur, meet_name, meet_date):
    cur.execute("SELECT id FROM meets WHERE meet_name = ?;", (meet_name,))
    row = cur.fetchone()
    if row:
        return row[0]
    
    m_id = str(uuid.uuid4())
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        INSERT INTO meets (id, meet_name, meet_date, location, created_at)
        VALUES (?, ?, ?, 'Sardis, AL', ?);
    """, (m_id, meet_name, meet_date, now))
    return m_id

def seed_records(db_path=db.DB_PATH):
    print(f"[*] Seeding historical records into {db_path}...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Seed Individual Records
    for rec in HISTORICAL_INDIV_RECORDS:
        sw_id = get_or_create_swimmer(cur, rec["swimmer"], rec["gender"])
        m_id = get_or_create_meet(cur, rec["meet"], rec["date"])

        # Check if already exists
        cur.execute("""
            SELECT id FROM swim_times 
            WHERE swimmer_id = ? AND event_name = ? AND time_seconds = ? AND meet_id = ?;
        """, (sw_id, rec["event_name"], rec["time_sec"], m_id))
        if not cur.fetchone():
            time_id = str(uuid.uuid4())
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute("""
                INSERT INTO swim_times (id, swimmer_id, meet_id, event_name, gender, time_seconds, time_display, course, round, is_dq, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'Y', 'F', 0, ?);
            """, (time_id, sw_id, m_id, rec["event_name"], rec["gender"], rec["time_sec"], rec["time_str"], now))
            print(f"  + Added indiv: {rec['gender']} {rec['event_name']} - {rec['time_str']} ({rec['swimmer']})")

    # Seed Relay Records
    for r in HISTORICAL_RELAYS:
        m_id = get_or_create_meet(cur, r["meet"], r["date"])
        sw_ids = [get_or_create_swimmer(cur, name, r["gender"]) for name in r["swimmers"]]
        while len(sw_ids) < 4:
            sw_ids.append(None)

        cur.execute("""
            SELECT id FROM relays
            WHERE event_name = ? AND gender = ? AND time_seconds = ? AND meet_id = ?;
        """, (r["event_name"], r["gender"], r["time_sec"], m_id))
        if not cur.fetchone():
            relay_id = str(uuid.uuid4())
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute("""
                INSERT INTO relays (id, meet_id, event_name, gender, team_letter, time_seconds, time_display, swimmer1_id, swimmer2_id, swimmer3_id, swimmer4_id, created_at)
                VALUES (?, ?, ?, ?, 'A', ?, ?, ?, ?, ?, ?, ?);
            """, (relay_id, m_id, r["event_name"], r["gender"], r["time_sec"], r["time_str"], sw_ids[0], sw_ids[1], sw_ids[2], sw_ids[3], now))
            print(f"  + Added relay: {r['gender']} {r['event_name']} - {r['time_str']} ({', '.join(r['swimmers'])})")

    conn.commit()
    conn.close()
    print("[✓] Finished seeding historical records.")

if __name__ == "__main__":
    seed_records()
    db.export_data_to_csv()
    import export_records
    export_records.export_records_json()
