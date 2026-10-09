"""
Sardis High School Swim Team — Database & Analytics Module
Handles SQLite schema, AHSAA State Qualifying Times (SQT) standards,
CL2 results parser, and query interfaces for the Streamlit dashboard.
"""

import os
import glob
import re
import zipfile
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
TIMES_DIR = os.path.join(BASE_DIR, "times")
STATIC_DIR = os.path.join(BASE_DIR, "static")
DB_PATH = os.path.join(DATA_DIR, "sardis_swim.db")

# 2026 AHSAA State Meet Qualifying Times (SCY)
# Extracted from official 2026 State Meet Qualifying Times standard chart
DEFAULT_SQT_STANDARDS = [
    # Boys Events
    {"season": "2026", "gender": "M", "event": "200 Medley Relay", "cut": "2:06.09", "is_relay": 1, "order": 1},
    {"season": "2026", "gender": "M", "event": "200 Free",         "cut": "2:10.89", "is_relay": 0, "order": 2},
    {"season": "2026", "gender": "M", "event": "200 IM",           "cut": "2:25.79", "is_relay": 0, "order": 3},
    {"season": "2026", "gender": "M", "event": "50 Free",           "cut": "24.69",   "is_relay": 0, "order": 4},
    {"season": "2026", "gender": "M", "event": "1M Diving",        "cut": "200.00",  "is_relay": 0, "order": 5},
    {"season": "2026", "gender": "M", "event": "100 Fly",          "cut": "1:05.19", "is_relay": 0, "order": 6},
    {"season": "2026", "gender": "M", "event": "100 Free",         "cut": "56.29",   "is_relay": 0, "order": 7},
    {"season": "2026", "gender": "M", "event": "500 Free",         "cut": "5:53.69", "is_relay": 0, "order": 8},
    {"season": "2026", "gender": "M", "event": "200 Free Relay",   "cut": "1:50.49", "is_relay": 1, "order": 9},
    {"season": "2026", "gender": "M", "event": "100 Back",         "cut": "1:06.19", "is_relay": 0, "order": 10},
    {"season": "2026", "gender": "M", "event": "100 Breast",       "cut": "1:14.79", "is_relay": 0, "order": 11},
    {"season": "2026", "gender": "M", "event": "400 Free Relay",   "cut": "4:15.99", "is_relay": 1, "order": 12},

    # Girls Events
    {"season": "2026", "gender": "F", "event": "200 Medley Relay", "cut": "2:13.00", "is_relay": 1, "order": 1},
    {"season": "2026", "gender": "F", "event": "200 Free",         "cut": "2:15.09", "is_relay": 0, "order": 2},
    {"season": "2026", "gender": "F", "event": "200 IM",           "cut": "2:35.09", "is_relay": 0, "order": 3},
    {"season": "2026", "gender": "F", "event": "50 Free",           "cut": "27.39",   "is_relay": 0, "order": 4},
    {"season": "2026", "gender": "F", "event": "1M Diving",        "cut": "200.00",  "is_relay": 0, "order": 5},
    {"season": "2026", "gender": "F", "event": "100 Fly",          "cut": "1:12.09", "is_relay": 0, "order": 6},
    {"season": "2026", "gender": "F", "event": "100 Free",         "cut": "1:00.89", "is_relay": 0, "order": 7},
    {"season": "2026", "gender": "F", "event": "500 Free",         "cut": "6:03.79", "is_relay": 0, "order": 8},
    {"season": "2026", "gender": "F", "event": "200 Free Relay",   "cut": "1:59.09", "is_relay": 1, "order": 9},
    {"season": "2026", "gender": "F", "event": "100 Back",         "cut": "1:09.39", "is_relay": 0, "order": 10},
    {"season": "2026", "gender": "F", "event": "100 Breast",       "cut": "1:18.19", "is_relay": 0, "order": 11},
    {"season": "2026", "gender": "F", "event": "400 Free Relay",   "cut": "4:33.19", "is_relay": 1, "order": 12},
]

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
    "400 Free Relay": 12
}

CL2_STROKE_MAP = {
    1: "Free",
    2: "Back",
    3: "Breast",
    4: "Fly",
    5: "IM",
    6: "Free Relay",
    7: "Medley Relay"
}


# ==============================================================================
# Helper Utilities
# ==============================================================================

def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Returns a SQLite connection with foreign keys activated."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def parse_time_str(time_str: Optional[str]) -> Optional[float]:
    """Converts a swim time string (e.g. '1:02.17', '24.69', '5:48.71Y') to float seconds."""
    if not time_str:
        return None
    raw = str(time_str).strip().upper()
    if any(dq in raw for dq in ("DQ", "NS", "SCR", "DFS", "DNF")):
        return None
    # Strip letters like 'Y', 'L', 'S', etc.
    cleaned = "".join(c for c in raw if c.isdigit() or c in ":.")
    if not cleaned:
        return None
    try:
        if ":" in cleaned:
            parts = cleaned.split(":")
            if len(parts) == 2:
                return float(parts[0]) * 60.0 + float(parts[1])
            elif len(parts) == 3:
                return float(parts[0]) * 3600.0 + float(parts[1]) * 60.0 + float(parts[2])
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def format_seconds(seconds: Optional[float]) -> str:
    """Formats float seconds into standard swim display format (e.g. '1:02.17' or '24.69')."""
    if seconds is None or pd.isna(seconds) or seconds <= 0:
        return "—"
    minutes = int(seconds // 60)
    rem_sec = seconds - (minutes * 60)
    if minutes > 0:
        return f"{minutes}:{rem_sec:05.2f}"
    else:
        return f"{rem_sec:.2f}"


def calculate_differential(time_sec: Optional[float], cut_sec: Optional[float]) -> Tuple[Optional[float], Optional[float], str]:
    """
    Computes time delta (time - cut) and percentage off cut.
    Returns: (diff_sec, diff_pct, status_label)
    """
    if time_sec is None or cut_sec is None or cut_sec <= 0:
        return None, None, "No Time"
    
    diff_sec = time_sec - cut_sec
    diff_pct = (diff_sec / cut_sec) * 100.0

    if diff_sec <= 0:
        status = "QUALIFIED"
    elif diff_sec <= 1.0:
        status = "WITHIN 1s"
    elif diff_sec <= 2.0:
        status = "WITHIN 2s"
    elif diff_pct <= 5.0:
        status = "WITHIN 5%"
    elif diff_pct <= 10.0:
        status = "WITHIN 10%"
    else:
        status = "HUNTING"

    return round(diff_sec, 2), round(diff_pct, 2), status


# ==============================================================================
# Database Initialization & Seeding
# ==============================================================================

def init_db(db_path: str = DB_PATH) -> None:
    """Initializes SQLite schema and loads default SQT cut standards."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    # Swimmers table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS swimmers (
        id TEXT PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        full_name TEXT NOT NULL,
        gender TEXT NOT NULL CHECK(gender IN ('M', 'F')),
        grade TEXT,
        status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Inactive')),
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # SQT Standards table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sqt_standards (
        id TEXT PRIMARY KEY,
        season TEXT NOT NULL,
        gender TEXT NOT NULL CHECK(gender IN ('M', 'F')),
        event_name TEXT NOT NULL,
        is_relay INTEGER DEFAULT 0,
        cut_seconds REAL NOT NULL,
        cut_display TEXT NOT NULL,
        sort_order INTEGER DEFAULT 0,
        UNIQUE(season, gender, event_name)
    );
    """)

    # Meets table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS meets (
        id TEXT PRIMARY KEY,
        meet_name TEXT UNIQUE NOT NULL,
        meet_date TEXT,
        location TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Individual swim times
    cur.execute("""
    CREATE TABLE IF NOT EXISTS swim_times (
        id TEXT PRIMARY KEY,
        swimmer_id TEXT NOT NULL REFERENCES swimmers(id) ON DELETE CASCADE,
        meet_id TEXT NOT NULL REFERENCES meets(id) ON DELETE CASCADE,
        event_name TEXT NOT NULL,
        gender TEXT NOT NULL,
        time_seconds REAL NOT NULL,
        time_display TEXT NOT NULL,
        course TEXT DEFAULT 'SCY',
        round TEXT DEFAULT 'F',
        is_dq INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(swimmer_id, meet_id, event_name, round)
    );
    """)

    # Relay entries
    cur.execute("""
    CREATE TABLE IF NOT EXISTS relays (
        id TEXT PRIMARY KEY,
        meet_id TEXT NOT NULL REFERENCES meets(id) ON DELETE CASCADE,
        event_name TEXT NOT NULL,
        gender TEXT NOT NULL,
        team_letter TEXT DEFAULT 'A',
        time_seconds REAL NOT NULL,
        time_display TEXT NOT NULL,
        swimmer1_id TEXT REFERENCES swimmers(id),
        swimmer2_id TEXT REFERENCES swimmers(id),
        swimmer3_id TEXT REFERENCES swimmers(id),
        swimmer4_id TEXT REFERENCES swimmers(id),
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(meet_id, event_name, gender, team_letter)
    );
    """)

    conn.commit()

    # Seed SQT standards if empty
    cur.execute("SELECT COUNT(*) FROM sqt_standards;")
    if cur.fetchone()[0] == 0:
        for std in DEFAULT_SQT_STANDARDS:
            sec = parse_time_str(std["cut"])
            cur.execute("""
            INSERT OR IGNORE INTO sqt_standards
            (id, season, gender, event_name, is_relay, cut_seconds, cut_display, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                str(uuid.uuid4()),
                std["season"],
                std["gender"],
                std["event"],
                std["is_relay"],
                sec,
                std["cut"],
                std["order"]
            ))
        conn.commit()

    conn.close()


# ==============================================================================
# CL2 / Meet Results Parser
# ==============================================================================

def parse_cl2_content(lines: List[str], team_code: str = "SHS") -> Dict[str, Any]:
    """
    Parses Hy-Tek CL2 records for a given team code (specifically Sardis High School).
    Extracts meet information, individual swimmer swims, and relays with team legs.
    """
    meet_name = "High School Swim Meet"
    meet_date = None

    for line in lines:
        if line.startswith("B1"):
            raw_m_name = line[11:41].strip()
            if raw_m_name:
                meet_name = raw_m_name
            d_raw = line[121:129].strip() if len(line) >= 129 else ""
            if len(d_raw) == 8 and d_raw.isdigit():
                meet_date = f"{d_raw[4:8]}-{d_raw[0:2]}-{d_raw[2:4]}"
            else:
                m = re.search(r'(0[1-9]|1[0-2])([0-2][0-9]|3[01])(19|20)\d{2}', line)
                if m:
                    v = m.group(0)
                    meet_date = f"{v[4:8]}-{v[0:2]}-{v[2:4]}"
            break

    in_shs = False
    swimmers_dict = {}  # full_name -> dict(first, last, gender, grade)
    indiv_swims = []
    relays = []
    current_relay = None

    for line in lines:
        if line.startswith("C1"):
            # Match Sardis High School while avoiding Scottsboro (SHS!) or city of Boaz in address
            c1_header = line[:60].upper()
            in_shs = "SARDIS" in c1_header
            current_relay = None

        elif in_shs and (line.startswith("C1") or line.startswith("Z0")):
            in_shs = False
            current_relay = None

        elif in_shs:
            if line.startswith("D0"):
                current_relay = None
                raw_name = line[11:39].strip()
                if not raw_name:
                    continue

                if ", " in raw_name:
                    p = raw_name.split(", ", 1)
                    full_name = f"{p[1].strip()} {p[0].strip()}"
                    first_name = p[1].strip()
                    last_name = p[0].strip()
                else:
                    full_name = raw_name
                    p = raw_name.split(" ", 1)
                    first_name = p[0].strip()
                    last_name = p[1].strip() if len(p) > 1 else ""

                grade = line[6:10].strip()
                gender = line[65].strip().upper()
                if gender not in ("M", "F") and len(line) > 66:
                    gender = line[66].strip().upper()
                if gender not in ("M", "F"):
                    gender = "M"

                swimmers_dict[full_name] = {
                    "first_name": first_name,
                    "last_name": last_name,
                    "full_name": full_name,
                    "gender": gender,
                    "grade": grade
                }

                dist_raw = line[67:71].strip()
                st_code_raw = line[71:72].strip()
                if not dist_raw.isdigit() or not st_code_raw.isdigit():
                    continue

                dist = int(dist_raw)
                stroke_num = int(st_code_raw)
                stroke_name = CL2_STROKE_MAP.get(stroke_num, "Unknown")
                event_name = f"{dist} {stroke_name}"

                f_time_str = line[115:124].strip()
                p_time_str = line[97:106].strip()

                is_dq = 1 if ("DQ" in f_time_str or "DQ" in p_time_str) else 0

                sec = parse_time_str(f_time_str) or parse_time_str(p_time_str)
                disp = f_time_str if f_time_str and not is_dq else p_time_str
                disp_clean = "".join(c for c in (f_time_str or p_time_str) if c.isdigit() or c in ":.")

                if sec is not None:
                    indiv_swims.append({
                        "swimmer_name": full_name,
                        "gender": gender,
                        "event_name": event_name,
                        "time_seconds": sec,
                        "time_display": format_seconds(sec) if not disp_clean else disp_clean,
                        "is_dq": is_dq,
                        "round": "F" if f_time_str else "P"
                    })

            elif line.startswith("E0"):
                # Relay record
                r_gender = line[20].strip().upper()
                if r_gender not in ("M", "F"):
                    r_gender = "M"
                team_letter = line[11].strip().upper() or "A"
                dist_str = line[22:25].strip()
                st_str = line[25].strip()
                if dist_str.isdigit() and st_str.isdigit():
                    dist = int(dist_str)
                    st_num = int(st_str)
                    st_name = CL2_STROKE_MAP.get(st_num, "Relay")
                    event_name = f"{dist} {st_name}"

                    f_time = line[68:81].strip()
                    p_time = line[45:55].strip()
                    sec = parse_time_str(f_time) or parse_time_str(p_time)
                    disp = f_time or p_time

                    if sec is not None:
                        current_relay = {
                            "event_name": event_name,
                            "gender": r_gender,
                            "team_letter": team_letter,
                            "time_seconds": sec,
                            "time_display": format_seconds(sec),
                            "swimmers": []
                        }
                        relays.append(current_relay)
                    else:
                        current_relay = None

            elif line.startswith("F0") and current_relay is not None:
                # Relay leg swimmer: In Hy-Tek CL2, columns 22:50 contain "Last, First M"
                leg_name_raw = line[22:50].strip()
                if ", " in leg_name_raw:
                    p = leg_name_raw.split(", ", 1)
                    sw_name = f"{p[1].strip()} {p[0].strip()}"
                else:
                    sw_name = leg_name_raw
                if sw_name and len(current_relay["swimmers"]) < 4:
                    current_relay["swimmers"].append(sw_name)
                    # Register swimmer if not already registered
                    if sw_name not in swimmers_dict:
                        leg_gender = line[64].strip().upper() if len(line) > 64 else current_relay["gender"]
                        swimmers_dict[sw_name] = {
                            "first_name": p[1].strip() if ", " in leg_name_raw else sw_name,
                            "last_name": p[0].strip() if ", " in leg_name_raw else "",
                            "full_name": sw_name,
                            "gender": leg_gender if leg_gender in ("M", "F") else current_relay["gender"],
                            "grade": line[6:10].strip()
                        }

    return {
        "meet_name": meet_name,
        "meet_date": meet_date,
        "swimmers": swimmers_dict,
        "indiv_swims": indiv_swims,
        "relays": relays
    }


def import_cl2_file(file_path: str, db_path: str = DB_PATH) -> Dict[str, Any]:
    """Imports a single .cl2 file into the database."""
    init_db(db_path)
    with open(file_path, "r", encoding="latin-1", errors="ignore") as f:
        lines = f.readlines()

    data = parse_cl2_content(lines)
    conn = get_connection(db_path)
    cur = conn.cursor()

    # 1. Upsert Meet
    meet_id = str(uuid.uuid4())
    cur.execute("""
    INSERT INTO meets (id, meet_name, meet_date)
    VALUES (?, ?, ?)
    ON CONFLICT(meet_name) DO UPDATE SET
        meet_date = excluded.meet_date;
    """, (meet_id, data["meet_name"], data["meet_date"]))

    cur.execute("SELECT id FROM meets WHERE meet_name = ?;", (data["meet_name"],))
    actual_meet_id = cur.fetchone()[0]

    # 2. Upsert Swimmers
    swimmer_id_map = {}
    for name, s_info in data["swimmers"].items():
        cur.execute("SELECT id, grade FROM swimmers WHERE full_name = ?;", (name,))
        row = cur.fetchone()
        if row:
            s_id = row[0]
            if s_info["grade"] and not row[1]:
                cur.execute("UPDATE swimmers SET grade = ? WHERE id = ?;", (s_info["grade"], s_id))
        else:
            s_id = str(uuid.uuid4())
            cur.execute("""
            INSERT INTO swimmers (id, first_name, last_name, full_name, gender, grade, status)
            VALUES (?, ?, ?, ?, ?, ?, 'Active');
            """, (s_id, s_info["first_name"], s_info["last_name"], name, s_info["gender"], s_info["grade"]))
        swimmer_id_map[name] = s_id

    # 3. Upsert Individual Swims
    swims_imported = 0
    for swim in data["indiv_swims"]:
        s_id = swimmer_id_map.get(swim["swimmer_name"])
        if not s_id:
            continue
        swim_id = str(uuid.uuid4())
        cur.execute("""
        INSERT INTO swim_times
        (id, swimmer_id, meet_id, event_name, gender, time_seconds, time_display, round, is_dq)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(swimmer_id, meet_id, event_name, round) DO UPDATE SET
            time_seconds = excluded.time_seconds,
            time_display = excluded.time_display,
            is_dq = excluded.is_dq;
        """, (
            swim_id,
            s_id,
            actual_meet_id,
            swim["event_name"],
            swim["gender"],
            swim["time_seconds"],
            swim["time_display"],
            swim["round"],
            swim["is_dq"]
        ))
        swims_imported += 1

    # 4. Upsert Relays
    relays_imported = 0
    for rel in data["relays"]:
        rel_id = str(uuid.uuid4())
        leg_ids = [swimmer_id_map.get(s_name) for s_name in rel["swimmers"]]
        while len(leg_ids) < 4:
            leg_ids.append(None)

        cur.execute("""
        INSERT INTO relays
        (id, meet_id, event_name, gender, team_letter, time_seconds, time_display,
         swimmer1_id, swimmer2_id, swimmer3_id, swimmer4_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(meet_id, event_name, gender, team_letter) DO UPDATE SET
            time_seconds = excluded.time_seconds,
            time_display = excluded.time_display,
            swimmer1_id = excluded.swimmer1_id,
            swimmer2_id = excluded.swimmer2_id,
            swimmer3_id = excluded.swimmer3_id,
            swimmer4_id = excluded.swimmer4_id;
        """, (
            rel_id,
            actual_meet_id,
            rel["event_name"],
            rel["gender"],
            rel["team_letter"],
            rel["time_seconds"],
            rel["time_display"],
            leg_ids[0], leg_ids[1], leg_ids[2], leg_ids[3]
        ))
        relays_imported += 1

    conn.commit()
    conn.close()

    return {
        "meet_name": data["meet_name"],
        "meet_date": data["meet_date"],
        "swimmers_count": len(swimmer_id_map),
        "swims_imported": swims_imported,
        "relays_imported": relays_imported
    }


def import_all_meets_in_times(times_dir: str = TIMES_DIR, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """
    Unzips any zip files in times_dir, locates all .cl2 files, and imports them.
    """
    init_db(db_path)
    if not os.path.exists(times_dir):
        return []

    # Unpack any .zip archives if not already unpacked
    for zf_path in glob.glob(os.path.join(times_dir, "*.zip")):
        try:
            with zipfile.ZipFile(zf_path, 'r') as zip_ref:
                zip_ref.extractall(times_dir)
        except Exception:
            pass

    cl2_files = sorted(glob.glob(os.path.join(times_dir, "*.cl2")))
    results = []
    for f in cl2_files:
        res = import_cl2_file(f, db_path=db_path)
        results.append(res)
    return results


# ==============================================================================
# Query Interfaces & Analytics
# ==============================================================================

def get_sqt_standards_df(gender: Optional[str] = None, db_path: str = DB_PATH) -> pd.DataFrame:
    """Returns official SQT standards sorted in championship order."""
    init_db(db_path)
    conn = get_connection(db_path)
    query = "SELECT gender, event_name, is_relay, cut_seconds, cut_display, sort_order FROM sqt_standards"
    params = []
    if gender in ("M", "F"):
        query += " WHERE gender = ?"
        params.append(gender)
    query += " ORDER BY gender, sort_order ASC;"
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df


def get_roster_df(db_path: str = DB_PATH) -> pd.DataFrame:
    """Returns team roster with grades and active status."""
    init_db(db_path)
    conn = get_connection(db_path)
    df = pd.read_sql("""
    SELECT id, first_name, last_name, full_name, gender, grade, status, created_at
    FROM swimmers
    ORDER BY gender, last_name, first_name;
    """, conn)
    conn.close()
    return df


def get_season_bests_df(db_path: str = DB_PATH) -> pd.DataFrame:
    """
    Computes season best time for every swimmer across all events,
    joined with the official SQT cut, delta seconds, percentage off, and qualification status.
    """
    init_db(db_path)
    conn = get_connection(db_path)
    query = """
    WITH Bests AS (
        SELECT 
            st.swimmer_id,
            st.event_name,
            MIN(st.time_seconds) as best_seconds
        FROM swim_times st
        WHERE st.is_dq = 0
        GROUP BY st.swimmer_id, st.event_name
    )
    SELECT 
        s.id as swimmer_id,
        s.full_name as swimmer_name,
        s.gender,
        s.grade,
        b.event_name,
        b.best_seconds,
        m.meet_name as best_meet,
        m.meet_date as best_date,
        sqt.cut_seconds,
        sqt.cut_display,
        sqt.sort_order
    FROM Bests b
    JOIN swimmers s ON b.swimmer_id = s.id
    LEFT JOIN swim_times st ON st.swimmer_id = b.swimmer_id 
                           AND st.event_name = b.event_name 
                           AND st.time_seconds = b.best_seconds
                           AND st.is_dq = 0
    LEFT JOIN meets m ON st.meet_id = m.id
    LEFT JOIN sqt_standards sqt ON sqt.event_name = b.event_name 
                                AND sqt.gender = s.gender
                                AND sqt.is_relay = 0
    GROUP BY b.swimmer_id, b.event_name
    ORDER BY s.gender, s.full_name, sqt.sort_order;
    """
    df = pd.read_sql(query, conn)
    conn.close()

    if df.empty:
        return df

    # Calculate differentials
    df["best_display"] = df["best_seconds"].apply(format_seconds)
    df["diff_sec"] = df["best_seconds"] - df["cut_seconds"]
    df["diff_pct"] = (df["diff_sec"] / df["cut_seconds"]) * 100.0

    def get_status(row):
        if pd.isna(row["cut_seconds"]):
            return "No Standard"
        d = row["diff_sec"]
        pct = row["diff_pct"]
        if d <= 0:
            return "QUALIFIED"
        elif d <= 1.0:
            return "WITHIN 1s"
        elif d <= 2.0:
            return "WITHIN 2s"
        elif pct <= 5.0:
            return "WITHIN 5%"
        elif pct <= 10.0:
            return "WITHIN 10%"
        else:
            return "HUNTING"

    df["status"] = df.apply(get_status, axis=1)
    df["is_qualified"] = df["diff_sec"] <= 0
    return df


def get_relay_bests_df(db_path: str = DB_PATH) -> pd.DataFrame:
    """
    Computes best relay times per event and gender, joined with SQT standard and cuts.
    """
    init_db(db_path)
    conn = get_connection(db_path)
    query = """
    WITH BestRelays AS (
        SELECT 
            r.event_name,
            r.gender,
            MIN(r.time_seconds) as best_seconds
        FROM relays r
        GROUP BY r.event_name, r.gender
    )
    SELECT 
        br.event_name,
        br.gender,
        br.best_seconds,
        r.team_letter,
        m.meet_name as best_meet,
        m.meet_date as best_date,
        s1.full_name as leg1,
        s2.full_name as leg2,
        s3.full_name as leg3,
        s4.full_name as leg4,
        sqt.cut_seconds,
        sqt.cut_display,
        sqt.sort_order
    FROM BestRelays br
    JOIN relays r ON r.event_name = br.event_name 
                 AND r.gender = br.gender 
                 AND r.time_seconds = br.best_seconds
    LEFT JOIN meets m ON r.meet_id = m.id
    LEFT JOIN swimmers s1 ON r.swimmer1_id = s1.id
    LEFT JOIN swimmers s2 ON r.swimmer2_id = s2.id
    LEFT JOIN swimmers s3 ON r.swimmer3_id = s3.id
    LEFT JOIN swimmers s4 ON r.swimmer4_id = s4.id
    LEFT JOIN sqt_standards sqt ON sqt.event_name = br.event_name 
                                AND sqt.gender = br.gender 
                                AND sqt.is_relay = 1
    GROUP BY br.event_name, br.gender
    ORDER BY br.gender, sqt.sort_order;
    """
    df = pd.read_sql(query, conn)
    conn.close()

    if df.empty:
        return df

    df["best_display"] = df["best_seconds"].apply(format_seconds)
    df["diff_sec"] = df["best_seconds"] - df["cut_seconds"]
    df["diff_pct"] = (df["diff_sec"] / df["cut_seconds"]) * 100.0
    df["is_qualified"] = df["diff_sec"] <= 0
    df["status"] = df["diff_sec"].apply(lambda d: "QUALIFIED" if d <= 0 else (f"+{d:.2f}s" if pd.notna(d) else "No Standard"))
    return df


def get_swimmer_progression_df(swimmer_id: str, db_path: str = DB_PATH) -> pd.DataFrame:
    """
    Returns full timeline of all swims for a given swimmer across meets,
    useful for Altair line charts.
    """
    init_db(db_path)
    conn = get_connection(db_path)
    df = pd.read_sql("""
    SELECT 
        st.id,
        st.event_name,
        st.time_seconds,
        st.time_display,
        st.round,
        st.is_dq,
        m.meet_name,
        m.meet_date,
        sqt.cut_seconds,
        sqt.cut_display
    FROM swim_times st
    JOIN meets m ON st.meet_id = m.id
    JOIN swimmers s ON st.swimmer_id = s.id
    LEFT JOIN sqt_standards sqt ON sqt.event_name = st.event_name 
                                AND sqt.gender = s.gender 
                                AND sqt.is_relay = 0
    WHERE st.swimmer_id = ?
    ORDER BY m.meet_date ASC, st.event_name;
    """, conn, params=(swimmer_id,))
    conn.close()
    return df


def get_swimmer_events_proximity_df(swimmer_id: str, sort_by: str = "closest_hunt", db_path: str = DB_PATH) -> pd.DataFrame:
    """
    Returns all contested individual events for a swimmer, joined with SQT cuts and deltas,
    sorted by proximity to the AHSAA state qualifying standard.
    
    Supported sort_by options:
    - 'closest_hunt': Unqualified hunts closest to cut first, followed by qualified cuts
    - 'closest_hunt_sec': Unqualified hunts closest to cut in seconds first, followed by qualified cuts
    - 'qualified_first': Qualified cuts first, followed by closest hunt
    - 'diff_sec': Ascending by time delta in seconds (most under cut to most over)
    - 'diff_pct': Ascending by percentage delta (% under to % over)
    - 'event_order': Championship standard event order
    """
    init_db(db_path)
    conn = get_connection(db_path)
    query = """
    WITH Bests AS (
        SELECT 
            st.swimmer_id,
            st.event_name,
            MIN(st.time_seconds) as best_seconds,
            COUNT(st.id) as swims_count
        FROM swim_times st
        WHERE st.swimmer_id = ? AND st.is_dq = 0
        GROUP BY st.swimmer_id, st.event_name
    )
    SELECT 
        b.event_name,
        b.best_seconds,
        b.swims_count,
        m.meet_name as best_meet,
        m.meet_date as best_date,
        sqt.cut_seconds,
        sqt.cut_display,
        sqt.sort_order
    FROM Bests b
    JOIN swimmers s ON b.swimmer_id = s.id
    LEFT JOIN swim_times st ON st.swimmer_id = b.swimmer_id 
                           AND st.event_name = b.event_name 
                           AND st.time_seconds = b.best_seconds
                           AND st.is_dq = 0
    LEFT JOIN meets m ON st.meet_id = m.id
    LEFT JOIN sqt_standards sqt ON sqt.event_name = b.event_name 
                                AND sqt.gender = s.gender 
                                AND sqt.is_relay = 0
    GROUP BY b.event_name;
    """
    df = pd.read_sql(query, conn, params=(swimmer_id,))
    conn.close()

    if df.empty:
        return pd.DataFrame(columns=[
            "event_name", "best_seconds", "best_display", "cut_seconds", "cut_display",
            "diff_sec", "diff_pct", "is_qualified", "status", "best_meet", "best_date",
            "sort_order", "swims_count"
        ])

    df["best_display"] = df["best_seconds"].apply(format_seconds)
    df["diff_sec"] = df["best_seconds"] - df["cut_seconds"]
    df["diff_pct"] = (df["diff_sec"] / df["cut_seconds"]) * 100.0
    df["is_qualified"] = df["diff_sec"] <= 0

    def get_status(row):
        if pd.isna(row["cut_seconds"]):
            return "No Standard"
        d = row["diff_sec"]
        pct = row["diff_pct"]
        if d <= 0:
            return "QUALIFIED"
        elif d <= 1.0:
            return "WITHIN 1s"
        elif d <= 2.0:
            return "WITHIN 2s"
        elif pct <= 5.0:
            return "WITHIN 5%"
        elif pct <= 10.0:
            return "WITHIN 10%"
        else:
            return "HUNTING"

    df["status"] = df.apply(get_status, axis=1)

    if sort_by == "closest_hunt":
        df = df.sort_values(by=["is_qualified", "diff_pct"], ascending=[True, True])
    elif sort_by == "closest_hunt_sec":
        df = df.sort_values(by=["is_qualified", "diff_sec"], ascending=[True, True])
    elif sort_by == "qualified_first":
        df = df.sort_values(by=["is_qualified", "diff_pct"], ascending=[False, True])
    elif sort_by == "diff_sec":
        df = df.sort_values(by=["diff_sec"], ascending=[True])
    elif sort_by == "diff_pct":
        df = df.sort_values(by=["diff_pct"], ascending=[True])
    elif sort_by == "event_order":
        df = df.sort_values(by=["sort_order"], ascending=[True])
    else:
        df = df.sort_values(by=["is_qualified", "diff_pct"], ascending=[True, True])

    return df.reset_index(drop=True)


def get_swimmer_uncontested_events_df(swimmer_id: str, db_path: str = DB_PATH) -> pd.DataFrame:
    """
    Returns individual championship events that this swimmer has NOT contested yet this season,
    including the target SQT cut time.
    """
    init_db(db_path)
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT gender FROM swimmers WHERE id = ?;", (swimmer_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return pd.DataFrame()
    gender = row[0]

    query = """
    SELECT 
        sqt.event_name,
        sqt.cut_seconds,
        sqt.cut_display,
        sqt.sort_order
    FROM sqt_standards sqt
    WHERE sqt.gender = ? 
      AND sqt.is_relay = 0
      AND sqt.event_name NOT IN (
          SELECT DISTINCT st.event_name 
          FROM swim_times st 
          WHERE st.swimmer_id = ? AND st.is_dq = 0
      )
    ORDER BY sqt.sort_order;
    """
    df = pd.read_sql(query, conn, params=(gender, swimmer_id))
    conn.close()
    return df


def get_swimmer_relays_df(swimmer_id: str, db_path: str = DB_PATH) -> pd.DataFrame:
    """
    Returns all relays where the swimmer competed as a leg, including position and teammates.
    """
    init_db(db_path)
    conn = get_connection(db_path)
    query = """
    SELECT 
        r.id as relay_id,
        r.event_name,
        r.gender,
        r.team_letter,
        r.time_seconds,
        r.time_display,
        m.meet_name,
        m.meet_date,
        sqt.cut_seconds,
        sqt.cut_display,
        sqt.sort_order,
        s1.full_name as leg1,
        s2.full_name as leg2,
        s3.full_name as leg3,
        s4.full_name as leg4,
        r.swimmer1_id,
        r.swimmer2_id,
        r.swimmer3_id,
        r.swimmer4_id
    FROM relays r
    JOIN meets m ON r.meet_id = m.id
    LEFT JOIN sqt_standards sqt ON sqt.event_name = r.event_name AND sqt.gender = r.gender AND sqt.is_relay = 1
    LEFT JOIN swimmers s1 ON r.swimmer1_id = s1.id
    LEFT JOIN swimmers s2 ON r.swimmer2_id = s2.id
    LEFT JOIN swimmers s3 ON r.swimmer3_id = s3.id
    LEFT JOIN swimmers s4 ON r.swimmer4_id = s4.id
    WHERE r.swimmer1_id = ? OR r.swimmer2_id = ? OR r.swimmer3_id = ? OR r.swimmer4_id = ?
    ORDER BY m.meet_date DESC, sqt.sort_order;
    """
    df = pd.read_sql(query, conn, params=(swimmer_id, swimmer_id, swimmer_id, swimmer_id))
    conn.close()

    if df.empty:
        return df

    df["diff_sec"] = df["time_seconds"] - df["cut_seconds"]
    df["diff_pct"] = (df["diff_sec"] / df["cut_seconds"]) * 100.0
    df["is_qualified"] = df["diff_sec"] <= 0
    df["status"] = df["diff_sec"].apply(lambda d: "QUALIFIED" if d <= 0 else (f"+{d:.2f}s" if pd.notna(d) else "No Standard"))

    def get_leg_desc(row):
        ev = row["event_name"]
        is_medley = "Medley" in ev
        if row["swimmer1_id"] == swimmer_id:
            return "Leg 1 (Backstroke)" if is_medley else "Leg 1 (Lead-off)"
        elif row["swimmer2_id"] == swimmer_id:
            return "Leg 2 (Breaststroke)" if is_medley else "Leg 2"
        elif row["swimmer3_id"] == swimmer_id:
            return "Leg 3 (Butterfly)" if is_medley else "Leg 3"
        elif row["swimmer4_id"] == swimmer_id:
            return "Leg 4 (Freestyle)" if is_medley else "Leg 4 (Anchor)"
        return "Alternate"

    df["leg_position"] = df.apply(get_leg_desc, axis=1)
    return df


def get_swimmer_stats(swimmer_id: str, db_path: str = DB_PATH) -> Dict[str, Any]:
    """
    Returns comprehensive summary metrics for an individual swimmer.
    """
    init_db(db_path)
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id, first_name, last_name, full_name, gender, grade, status FROM swimmers WHERE id = ?;", (swimmer_id,))
    sw_row = cur.fetchone()
    if not sw_row:
        conn.close()
        return {}

    events_df = get_swimmer_events_proximity_df(swimmer_id, sort_by="closest_hunt", db_path=db_path)
    relays_df = get_swimmer_relays_df(swimmer_id, db_path=db_path)

    total_events = len(events_df)
    cuts_locked = len(events_df[events_df["is_qualified"]]) if not events_df.empty else 0
    hunts_df = events_df[~events_df["is_qualified"]] if not events_df.empty else pd.DataFrame()

    closest_cut_event = None
    if not hunts_df.empty:
        top_hunt = hunts_df.iloc[0]
        closest_cut_event = {
            "event": top_hunt["event_name"],
            "best_display": top_hunt["best_display"],
            "cut_display": top_hunt["cut_display"],
            "diff_sec": top_hunt["diff_sec"],
            "diff_pct": top_hunt["diff_pct"],
            "status": top_hunt["status"]
        }

    cur.execute("""
        SELECT COUNT(DISTINCT meet_id), COUNT(id) 
        FROM swim_times 
        WHERE swimmer_id = ? AND is_dq = 0;
    """, (swimmer_id,))
    meet_cnt, swim_cnt = cur.fetchone()
    conn.close()

    relay_cuts = len(relays_df[relays_df["is_qualified"]]) if not relays_df.empty else 0

    return {
        "id": sw_row[0],
        "first_name": sw_row[1],
        "last_name": sw_row[2],
        "full_name": sw_row[3],
        "gender": sw_row[4],
        "grade": sw_row[5] or "N/A",
        "status": sw_row[6],
        "total_events": total_events,
        "cuts_locked": cuts_locked,
        "closest_cut": closest_cut_event,
        "meets_attended": meet_cnt,
        "swims_logged": swim_cnt,
        "relays_count": len(relays_df),
        "relay_cuts": relay_cuts
    }


def get_state_qualifiers_summary(db_path: str = DB_PATH) -> Dict[str, Any]:
    """
    Returns high-level state qualifier roster & statistics.
    """
    bests_df = get_season_bests_df(db_path=db_path)
    relays_df = get_relay_bests_df(db_path=db_path)

    if bests_df.empty:
        return {
            "individual_qualifiers": [],
            "individual_cuts_count": 0,
            "relay_cuts_count": 0,
            "total_cuts": 0,
            "qualified_swimmers_count": 0,
            "relays_qualified": []
        }

    qual_indiv = bests_df[bests_df["is_qualified"]].copy()
    qual_relays = relays_df[relays_df["is_qualified"]].copy() if not relays_df.empty else pd.DataFrame()

    # Group qualified events per swimmer
    swimmer_groups = {}
    for _, row in qual_indiv.iterrows():
        name = row["swimmer_name"]
        if name not in swimmer_groups:
            swimmer_groups[name] = {
                "name": name,
                "gender": row["gender"],
                "grade": row["grade"],
                "cuts": []
            }
        swimmer_groups[name]["cuts"].append({
            "event": row["event_name"],
            "best_display": row["best_display"],
            "cut_display": row["cut_display"],
            "margin_sec": abs(row["diff_sec"]),
            "meet": row["best_meet"]
        })

    return {
        "individual_qualifiers": list(swimmer_groups.values()),
        "individual_cuts_count": len(qual_indiv),
        "relay_cuts_count": len(qual_relays),
        "total_cuts": len(qual_indiv) + len(qual_relays),
        "qualified_swimmers_count": len(swimmer_groups),
        "relays_qualified": qual_relays.to_dict("records") if not qual_relays.empty else []
    }


def get_all_meets_df(db_path: str = DB_PATH) -> pd.DataFrame:
    """Returns list of recorded meets with swim counts."""
    init_db(db_path)
    conn = get_connection(db_path)
    df = pd.read_sql("""
    SELECT 
        m.id,
        m.meet_name,
        m.meet_date,
        COUNT(DISTINCT st.id) as individual_swims,
        COUNT(DISTINCT r.id) as relay_swims
    FROM meets m
    LEFT JOIN swim_times st ON st.meet_id = m.id
    LEFT JOIN relays r ON r.meet_id = m.id
    GROUP BY m.id
    ORDER BY m.meet_date DESC;
    """, conn)
    conn.close()
    return df


def export_data_to_csv(data_dir: str = DATA_DIR, db_path: str = DB_PATH) -> None:
    """Exports SQLite tables to CSV for diffable version control and backup."""
    init_db(db_path)
    os.makedirs(data_dir, exist_ok=True)
    conn = get_connection(db_path)

    tables = ["swimmers", "sqt_standards", "meets", "swim_times", "relays"]
    for tbl in tables:
        try:
            df = pd.read_sql(f"SELECT * FROM {tbl};", conn)
            df.to_csv(os.path.join(data_dir, f"{tbl.capitalize()}.csv"), index=False)
        except Exception:
            pass
    conn.close()

