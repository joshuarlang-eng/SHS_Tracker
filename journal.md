# Sardis High School Swim & Dive — Project Chronicle & System Architecture

> **Purpose:**  
> This journal documents the architecture, database schema, official qualifying standards, branding specifications, and deployment procedures for the **Sardis High School Swim Team State Qualifying Times (SQT) Tracker**.

---

## 1. Project Mission & Overview

The **Sardis High School Swim Tracker** is an automated athletic analytics and database platform designed to track swimmer performances across competitive high school meets, celebrate locked-in **AHSAA State Championship Qualifiers**, and calculate precise **differentials (seconds and percentage off)** for athletes hunting state qualifying cuts.

### Key Capabilities
1. **Automated Meet Ingestion:** Direct parser for Hy-Tek `.cl2` and `.zip` meet results files, automatically resolving Sardis High School swimmers (`SHS` / `Sardis High School`), individual events, and relays.
2. **State Qualifiers Board:** Instant recognition of all athletes and relays that have satisfied the 2026 AHSAA State Meet Qualifying standard (1A–5A), detailing margin beat and qualifying meets.
3. **SQT Bubble Watch & Differentials:** Filterable performance board calculating time deltas (`Time - SQT`) and percentages off with proximity categorizations (`Within 1.0s`, `Within 2.0s`, `Within 5%`, `In The Hunt`).
4. **Swimmer View & Proximity Analyzer:** Dedicated individual swimmer hub with all contested events sorted by proximity to achieving a cut.
5. **Event Depth Charts:** Event-by-event rankings comparing all team athletes directly against the cut mark.
6. **Relay Tracker:** Tracking of 200 Medley, 200 Free, and 400 Free relay teams, leg rosters, and time deltas.
7. **Offline-First & Containerized:** Self-hosted on Docker on the mini-PC, accessible across school/pool devices via Tailscale.

---

## 2. Branding & Visual Design Standards

- **School:** Sardis High School (SHS)
- **Mascot / Program:** Lions Swim & Dive
- **Official Team Colors:** Sardis Crimson & White
  - **Sardis Crimson:** `#8B0526`
  - **Crimson Light / Glow:** `#B20731` / `rgba(139, 5, 38, 0.45)`
  - **Crimson Dark Border:** `#5C0319` / `rgba(139, 5, 38, 0.4)`
  - **Athletic Slate Gray:** `#9CA3AF` / `#E5E7EB`
  - **Dark Aquatic Surface:** `#0B0E14` (Background) / `#141824` (Cards)
- **Official Emblem:** Stylized Sardis Lions "S" with charging Lion profile (`static/Logo.png`)

---

## 3. Official 2026 AHSAA State Qualifying Times (SCY)

AHSAA 1A–5A State Championship Qualifying standards:

| Event | Boys | Girls | Order |
| :--- | :---: | :---: | :---: |
| **200 Medley Relay** | 2:06.09 (126.09s) | 2:13.00 (133.00s) | 1 |
| **200 Freestyle** | 2:10.89 (130.89s) | 2:15.09 (135.09s) | 2 |
| **200 IM** | 2:25.79 (145.79s) | 2:35.09 (155.09s) | 3 |
| **50 Freestyle** | 0:24.69 (24.69s) | 0:27.39 (27.39s) | 4 |
| **1M Diving** | 200.00 pts | 200.00 pts | 5 |
| **100 Butterfly** | 1:05.19 (65.19s) | 1:12.09 (72.09s) | 6 |
| **100 Freestyle** | 0:56.29 (56.29s) | 1:00.89 (60.89s) | 7 |
| **500 Freestyle** | 5:53.69 (353.69s) | 6:03.79 (363.79s) | 8 |
| **200 Freestyle Relay** | 1:50.49 (110.49s) | 1:59.09 (119.09s) | 9 |
| **100 Backstroke** | 1:06.19 (66.19s) | 1:09.39 (69.39s) | 10 |
| **100 Breaststroke** | 1:14.79 (74.79s) | 1:18.19 (78.19s) | 11 |
| **400 Freestyle Relay** | 4:15.99 (255.99s) | 4:33.19 (273.19s) | 12 |

---

## 4. Current Season Snapshot (Meets Contested)

1. **2026 SMPA Aquapalooza** (Sept 12, 2026)
2. **2026 Boaz Invitational** (Sept 15, 2026)
3. **2026 Albertville Invitational** (Sept 28, 2026)

### Locked-In State Qualifiers (4 Total Cuts):
- **Caleb Battles:** 2 Cuts (50 Free: 24.13, 100 Fly: 1:00.85)
- **Jace Duncan:** 1 Cut (100 Fly: 1:04.65)
- **Rowan Spears:** 1 Cut (100 Breast: 1:14.51)

---

## 5. System Architecture & Tech Stack

- **Frontend / UI:** Streamlit with customized Sardis Crimson (`#8B0526`) styling
- **Database:** Local SQLite (`data/sardis_swim.db`)
- **Visuals:** Altair declarative charts
- **Deployment:** Docker & Docker Compose on Port `8503:8501`
- **Public Team Records Site:** Static HTML5 / CSS3 / Vanilla JS on GitHub Pages (`https://joshuarlang-eng.github.io/SHS_Tracker/`)

---

## 6. Public GitHub Pages Records Pipeline (SHS Website Integration)

To provide official Short Course Yards (SCY) team records for the Sardis High School athletics website, a public-facing static records widget was deployed:
1. **`export_records.py`**: Extracts all-time best times per event for Girls and Boys, formats times, tracks broken records, and outputs `records.json` while syncing embedded JSON in `index.html`.
2. **`index.html`**: A mobile-responsive web dashboard with Sardis Crimson (`#8B0526`) palette, instant search, stroke filters, gender pills, dark/light mode toggle, and dynamic `NEW RECORD!` badges.
3. **`.github/workflows/pages.yml`**: GitHub Actions workflow that automatically deploys the static files to GitHub Pages upon push to `main`.
4. **Direct Push from Mini-PC**: Integrated into `app.py` meet ingestion workflow so that whenever a new meet file is uploaded and processed on the mini-PC, team records are automatically compiled and pushed to GitHub.
