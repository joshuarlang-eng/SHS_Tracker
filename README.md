# Sardis High School Swim & Dive — State Qualifying Times Tracker

Automated swim performance tracking and AHSAA State Qualifying Times (SQT) differential analyzer for the **Sardis High School Swim Team**.

---

## 🦁 Features

1. **State Qualifiers Board:** Instantly highlights locked-in AHSAA State Championship qualifiers, margins under the cut, and qualifying meets.
2. **SQT Bubble Watch & Differentials:** Real-time delta tracker (`Time - Cut` in seconds and percentage) with proximity tags (*Within 1.0s*, *Within 2.0s*, *Within 5%*, *In The Hunt*).
3. **Swimmer Hub & Proximity Analyzer:** Swimmer profile page sorting every event by proximity to achieving an AHSAA State Qualifying cut, plus relay splits and meet progressions.
4. **Event Depth Charts:** Season rankings by event with cuts benchmarks.
5. **Relay Tracker:** Relay squad performance tracking across all contested relays.
6. **Automated Meet Results Ingestion:** Parses Hy-Tek `.cl2` and `.zip` meet result files directly from the web interface.

---

## 🎨 Branding & Identity

- **School:** Sardis High School (SHS)
- **Mascot:** Lions
- **Primary Color:** Sardis Crimson (`#8B0526`)
- **Secondary / Accent:** Crisp White (`#FFFFFF`) and Athletic Slate (`#9CA3AF`)
- **Emblem:** Sardis Lions "S" Logo (`static/Logo.png`)

---

## 🚀 Quick Start (Local Development)

### 1. Requirements
- Python 3.10+ (or Python 3.12)
- Virtual environment

```bash
cd /home/jrl/Projects/sardis_swim_tracker
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Launch the Application
```bash
streamlit run app.py --server.port=8501
```

Access the app in your browser at `http://localhost:8501`.

---

## 🐳 Docker Deployment

The application includes a production-ready `Dockerfile` and `docker-compose.yml` bound to host port **8503** (to run cleanly alongside Boaz on 8502).

```bash
# Build and run container in detached mode
docker compose up -d --build

# View logs
docker compose logs -f

# Stop container
docker compose down
```

Access the app across your local network or Tailscale at:
`http://<MINI-PC-IP>:8503`

---

## 📊 Database & Data Pipeline

- SQLite database located at `data/sardis_swim.db`.
- Meet files stored in `times/`.
- Diffable CSV exports stored in `data/` (`Swimmers.csv`, `Meets.csv`, `Swim_times.csv`, `Relays.csv`, `Sqt_standards.csv`).
