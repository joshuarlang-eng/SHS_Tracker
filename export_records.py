#!/usr/bin/env python3
"""
Sardis High School Swim & Dive — Team Records Exporter & GitHub Pages Pipeline
==============================================================================
Exports all-time Short Course Yards (SCY) team records from the local SQLite database
(data/sardis_swim.db) to records.json and syncs the embedded JSON in index.html.
Can also commit and push directly to GitHub (origin main) for automated GitHub Pages deploy.
"""

import os
import sys
import json
import re
import sqlite3
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "data", "sardis_swim.db")
OUTPUT_JSON = os.path.join(SCRIPT_DIR, "records.json")
INDEX_HTML = os.path.join(SCRIPT_DIR, "index.html")

EVENT_ORDER_MAP = {
    "200 Medley Relay": 1,
    "200 Free": 2,
    "200 IM": 3,
    "50 Free": 4,
    "1M Diving": 5,
    "100 Fly": 6,
    "100 Free": 7,
    "500 Free": 8,
    "200 Free Relay": 9,
    "100 Back": 10,
    "100 Breast": 11,
    "400 Free Relay": 12,
    "100 IM": 13,
    "50 Fly": 14,
    "50 Back": 15,
    "50 Breast": 16,
}

def format_seconds(seconds: Optional[float]) -> str:
    """Format float seconds to swim notation (e.g., 24.13 or 1:05.56 or 5:43.67)."""
    if seconds is None:
        return "--"
    if seconds >= 60.0:
        minutes = int(seconds // 60)
        rem = seconds % 60.0
        return f"{minutes}:{rem:05.2f}"
    return f"{seconds:.2f}"

def get_stroke(event_name: str) -> str:
    """Classifies stroke category for event."""
    ev = event_name.lower()
    if "relay" in ev:
        return "Relay"
    if "free" in ev:
        return "Free"
    if "back" in ev:
        return "Back"
    if "breast" in ev:
        return "Breast"
    if "fly" in ev:
        return "Fly"
    if "im" in ev or "medley" in ev:
        return "IM"
    if "div" in ev:
        return "Diving"
    return "Other"

def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    return sqlite3.connect(db_path)

def build_team_records_data(db_path: str = DB_PATH) -> Dict[str, Any]:
    """
    Queries the database and compiles all-time team records for Girls and Boys,
    identifying new records broken in the most recent meet.
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}")

    conn = get_connection(db_path)
    cur = conn.cursor()

    # 1. Identify latest meet
    cur.execute("""
        SELECT id, meet_name, meet_date 
        FROM meets 
        ORDER BY meet_date DESC, created_at DESC 
        LIMIT 1;
    """)
    latest_meet_row = cur.fetchone()
    latest_meet_id = latest_meet_row[0] if latest_meet_row else None
    latest_meet_name = latest_meet_row[1] if latest_meet_row else "Initial"
    latest_meet_date = latest_meet_row[2] if latest_meet_row else datetime.now().strftime("%Y-%m-%d")

    # 2. Individual Records
    indiv_query = """
    WITH RankedSwims AS (
        SELECT 
            st.event_name,
            s.gender,
            st.time_seconds,
            st.time_display,
            s.full_name as swimmer_name,
            m.id as meet_id,
            m.meet_name,
            m.meet_date,
            ROW_NUMBER() OVER (
                PARTITION BY st.event_name, s.gender 
                ORDER BY st.time_seconds ASC, m.meet_date ASC
            ) as rn
        FROM swim_times st
        JOIN swimmers s ON st.swimmer_id = s.id
        JOIN meets m ON st.meet_id = m.id
        WHERE st.is_dq = 0
    )
    SELECT event_name, gender, time_seconds, time_display, swimmer_name, meet_id, meet_name, meet_date
    FROM RankedSwims
    WHERE rn = 1
    ORDER BY gender, event_name;
    """
    cur.execute(indiv_query)
    indiv_rows = cur.fetchall()

    records_list = []

    for row in indiv_rows:
        ev_name, gender, sec, disp, sw_name, m_id, m_name, m_date = row
        is_new = (m_id == latest_meet_id)

        # Check for previous record if broken at latest meet
        prev_record_text = None
        if is_new:
            cur.execute("""
                SELECT st.time_seconds, st.time_display, s.full_name, m.meet_date
                FROM swim_times st
                JOIN swimmers s ON st.swimmer_id = s.id
                JOIN meets m ON st.meet_id = m.id
                WHERE st.is_dq = 0 
                  AND st.event_name = ? 
                  AND s.gender = ? 
                  AND m.id != ?
                ORDER BY st.time_seconds ASC
                LIMIT 1;
            """, (ev_name, gender, latest_meet_id))
            prev_row = cur.fetchone()
            if prev_row:
                prev_sec, prev_disp, prev_holder, prev_date = prev_row
                drop = prev_sec - sec
                drop_str = f"-{drop:.2f}s" if drop > 0 else f"+{abs(drop):.2f}s"
                prev_record_text = f"Prev: {prev_disp} ({prev_holder}) [{drop_str}]"

        records_list.append({
            "id": f"{gender}_{re.sub(r'[^a-zA-Z0-9]', '_', ev_name).lower()}",
            "gender": gender,
            "gender_name": "Girls" if gender == "F" else "Boys",
            "event_name": ev_name,
            "stroke": get_stroke(ev_name),
            "is_relay": False,
            "time_seconds": round(sec, 2),
            "time_formatted": format_seconds(sec) if not disp else disp,
            "swimmer_name": sw_name,
            "swimmers": [sw_name],
            "relay_legs": None,
            "meet_name": m_name,
            "meet_date": m_date,
            "is_new": is_new,
            "prev_record": prev_record_text,
            "sort_order": EVENT_ORDER_MAP.get(ev_name, 99)
        })

    # 3. Relay Records
    relay_query = """
    WITH RankedRelays AS (
        SELECT 
            r.event_name,
            r.gender,
            r.time_seconds,
            r.time_display,
            r.team_letter,
            m.id as meet_id,
            m.meet_name,
            m.meet_date,
            s1.full_name as leg1,
            s2.full_name as leg2,
            s3.full_name as leg3,
            s4.full_name as leg4,
            ROW_NUMBER() OVER (
                PARTITION BY r.event_name, r.gender 
                ORDER BY r.time_seconds ASC, m.meet_date ASC
            ) as rn
        FROM relays r
        JOIN meets m ON r.meet_id = m.id
        LEFT JOIN swimmers s1 ON r.swimmer1_id = s1.id
        LEFT JOIN swimmers s2 ON r.swimmer2_id = s2.id
        LEFT JOIN swimmers s3 ON r.swimmer3_id = s3.id
        LEFT JOIN swimmers s4 ON r.swimmer4_id = s4.id
        WHERE r.time_seconds IS NOT NULL
    )
    SELECT event_name, gender, time_seconds, time_display, team_letter, meet_id, meet_name, meet_date, leg1, leg2, leg3, leg4
    FROM RankedRelays
    WHERE rn = 1
    ORDER BY gender, event_name;
    """
    cur.execute(relay_query)
    relay_rows = cur.fetchall()

    for row in relay_rows:
        ev_name, gender, sec, disp, t_letter, m_id, m_name, m_date, l1, l2, l3, l4 = row
        is_new = (m_id == latest_meet_id)

        legs = [l for l in [l1, l2, l3, l4] if l]
        is_medley = "medley" in ev_name.lower()
        leg_roles = ["Back", "Breast", "Fly", "Free"] if is_medley else ["Leg 1", "Leg 2", "Leg 3", "Leg 4"]

        relay_legs = []
        for i, swimmer in enumerate(legs):
            role = leg_roles[i] if i < len(leg_roles) else f"Leg {i+1}"
            relay_legs.append({"leg": i + 1, "role": role, "swimmer": swimmer})

        swimmer_str = ", ".join(legs)

        prev_record_text = None
        if is_new:
            cur.execute("""
                SELECT r.time_seconds, r.time_display, m.meet_date
                FROM relays r
                JOIN meets m ON r.meet_id = m.id
                WHERE r.event_name = ? 
                  AND r.gender = ? 
                  AND m.id != ?
                ORDER BY r.time_seconds ASC
                LIMIT 1;
            """, (ev_name, gender, latest_meet_id))
            prev_row = cur.fetchone()
            if prev_row:
                prev_sec, prev_disp, prev_date = prev_row
                drop = prev_sec - sec
                drop_str = f"-{drop:.2f}s" if drop > 0 else f"+{abs(drop):.2f}s"
                prev_record_text = f"Prev: {prev_disp} [{drop_str}]"

        records_list.append({
            "id": f"{gender}_{re.sub(r'[^a-zA-Z0-9]', '_', ev_name).lower()}",
            "gender": gender,
            "gender_name": "Girls" if gender == "F" else "Boys",
            "event_name": ev_name,
            "stroke": "Relay",
            "is_relay": True,
            "team_letter": t_letter,
            "time_seconds": round(sec, 2),
            "time_formatted": format_seconds(sec) if not disp else disp,
            "swimmer_name": swimmer_str,
            "swimmers": legs,
            "relay_legs": relay_legs,
            "meet_name": m_name,
            "meet_date": m_date,
            "is_new": is_new,
            "prev_record": prev_record_text,
            "sort_order": EVENT_ORDER_MAP.get(ev_name, 99)
        })

    conn.close()

    # Sort all records by Gender (Girls first, then Boys) and standard event order
    records_list.sort(key=lambda r: (0 if r["gender"] == "F" else 1, r["sort_order"], r["event_name"]))

    new_count = sum(1 for r in records_list if r["is_new"])

    return {
        "team": "SHS",
        "team_name": "Sardis High School",
        "mascot": "Lions",
        "last_updated": datetime.now().isoformat(),
        "latest_meet": {
            "name": latest_meet_name,
            "date": latest_meet_date
        },
        "total_records": len(records_list),
        "new_records_count": new_count,
        "records": records_list
    }

def sync_embedded_records_in_html(json_data: Dict[str, Any], html_path: str = INDEX_HTML) -> bool:
    """
    Updates the embedded fallback JSON script inside index.html so the page
    can be viewed locally without CORS restrictions or external web servers.
    """
    if not os.path.exists(html_path):
        return False

    try:
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()

        compact_json = json.dumps(json_data, separators=(',', ':'))
        pattern = r'(<script\s+id="embeddedRecords"\s+type="application/json">)(.*?)(</script>)'
        replacement = r'\g<1>' + compact_json + r'\g<3>'

        if re.search(pattern, content, flags=re.DOTALL):
            new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return True
    except Exception as e:
        print(f"[!] Warning syncing embedded records into {html_path}: {e}")
        return False
    return False

def export_records_json(output_path: str = OUTPUT_JSON, db_path: str = DB_PATH) -> Dict[str, Any]:
    """
    Builds and writes records.json, and syncs index.html fallback.
    """
    data = build_team_records_data(db_path=db_path)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"[✓] Successfully wrote {data['total_records']} records to {output_path}")

    if os.path.exists(INDEX_HTML):
        if sync_embedded_records_in_html(data, INDEX_HTML):
            print(f"[✓] Synced embedded records inside {INDEX_HTML}")

    return data

def push_to_github(meet_name: Optional[str] = None) -> Tuple[bool, str]:
    """
    Stages records, web files, and data diffs, commits, and pushes to origin main.
    Returns (success, message).
    """
    # Verify git work tree
    res = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True, cwd=SCRIPT_DIR)
    if res.returncode != 0:
        return False, "Not inside a git repository."

    files_to_stage = [
        "records.json",
        "index.html",
        "data/Meets.csv",
        "data/Swimmers.csv",
        "data/Swim_times.csv",
        "data/Relays.csv",
        "data/Swim_splits.csv",
        "data/Sqt_standards.csv",
        "times"
    ]

    existing = [f for f in files_to_stage if os.path.exists(os.path.join(SCRIPT_DIR, f))]
    if not existing:
        return False, "No modified files found to stage."

    try:
        # Stage files
        subprocess.run(["git", "add"] + existing, cwd=SCRIPT_DIR, check=True)

        # Check if changes exist
        diff_res = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=SCRIPT_DIR)
        if diff_res.returncode == 0:
            return True, "GitHub Pages is already up to date with latest records."

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        if meet_name:
            commit_msg = f"data: update SHS team records from {meet_name} [{timestamp}]"
        else:
            commit_msg = f"data: update SHS team records [{timestamp}]"

        subprocess.run(["git", "commit", "-m", commit_msg], cwd=SCRIPT_DIR, check=True)
        push_res = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True, cwd=SCRIPT_DIR)
        
        if push_res.returncode != 0:
            err = push_res.stderr.strip() or push_res.stdout.strip()
            return False, f"Git push failed: {err}"

        return True, "Successfully pushed to GitHub! Website will update in ~25 seconds."
    except Exception as e:
        return False, f"Git push exception: {str(e)}"

def export_and_push(meet_name: Optional[str] = None, db_path: str = DB_PATH) -> Tuple[bool, str]:
    """
    Convenience method: exports records and pushes to GitHub.
    """
    try:
        data = export_records_json(db_path=db_path)
        m_name = meet_name or data.get("latest_meet", {}).get("name")
        return push_to_github(meet_name=m_name)
    except Exception as e:
        return False, f"Export & push failed: {str(e)}"

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Export SHS Team Records to JSON & GitHub Pages")
    parser.add_argument("--push", action="store_true", help="Commit and push changes to GitHub origin main")
    parser.add_argument("--meet", help="Optional meet name for commit title")
    parser.add_argument("--db", default=DB_PATH, help="Path to sardis_swim.db")
    parser.add_argument("--json", default=OUTPUT_JSON, help="Path to output records.json")
    args = parser.parse_args()

    data = export_records_json(output_path=args.json, db_path=args.db)
    print(f"[*] Processed {data['total_records']} team records ({data['new_records_count']} new).")

    if args.push:
        success, msg = push_to_github(meet_name=args.meet or data["latest_meet"]["name"])
        print(f"[{'✓' if success else '!'}] {msg}")
        sys.exit(0 if success else 1)
