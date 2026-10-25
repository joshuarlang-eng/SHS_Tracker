"""
Sardis High School Swim Team — State Qualifying Times Tracker
Streamlit Web Application
Colors: Sardis Crimson (#8B0526) and Athletic Gray (#9CA3AF)
"""

import os
import base64
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
import altair as alt
import streamlit as st

import db

# -----------------------------------------------------------------------------
# Configuration & Theming
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Sardis Swim & Dive | State Qualifying Tracker",
    page_icon="Icon.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Colors
MAROON = "#8B0526"       # Sardis Crimson
MAROON_LIGHT = "#B20731"
MAROON_DARK = "#5C0319"
GRAY_LIGHT = "#E5E7EB"
GRAY_MID = "#9CA3AF"     # Athletic Gray
GRAY_DARK = "#374151"
BG_DARK = "#0B0E14"
BG_CARD = "#141824"
BG_CARD_LIGHT = "#1C2234"
GOLD = "#F59E0B"
GREEN = "#10B981"
BLUE = "#3B82F6"

# Ensure database is initialized and data loaded on startup
db.init_db()
db.deduplicate_swimmers()
if not os.path.exists(db.DB_PATH) or os.path.getsize(db.DB_PATH) < 10000:
    db.import_all_meets_in_times()

@st.cache_data
def get_logo_b64() -> str:
    """Loads and caches the base64-encoded logo."""
    logo_path = os.path.join(db.STATIC_DIR, "Logo.png")
    if os.path.exists(logo_path):
        try:
            with open(logo_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            return ""
    return ""

LOGO_B64 = get_logo_b64()

# Custom CSS
st.markdown(f"""
<head>
    <link rel="apple-touch-icon" href="Icon.png">
    <link rel="icon" type="image/png" href="Icon.png">
</head>
<style>
    /* Global Background & Variables */
    :root {{
        --maroon: {MAROON};
        --maroon-glow: rgba(139, 5, 38, 0.45);
        --gray-mid: {GRAY_MID};
        --bg-dark: {BG_DARK};
        --bg-card: {BG_CARD};
    }}

    .stApp {{
        background-color: {BG_DARK};
        background-image: 
            radial-gradient(circle at 10% 15%, rgba(139, 5, 38, 0.18) 0%, transparent 40%),
            radial-gradient(circle at 90% 85%, rgba(156, 163, 175, 0.12) 0%, transparent 45%);
        color: #F3F4F6;
    }}

    /* Header Banner */
    .shs-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: linear-gradient(135deg, rgba(20, 24, 36, 0.98), rgba(11, 14, 20, 0.98));
        border: 2px solid rgba(139, 5, 38, 0.4);
        border-radius: 14px;
        padding: 16px 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6), 0 0 20px rgba(139, 5, 38, 0.2);
    }}
    .shs-header-left {{
        display: flex;
        align-items: center;
        gap: 20px;
    }}
    .shs-header-logo {{
        height: 64px;
        width: auto;
        filter: drop-shadow(0 2px 8px rgba(139, 5, 38, 0.7));
    }}
    .shs-header-title {{
        font-size: 26px;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #FFFFFF;
        margin: 0;
        line-height: 1.2;
    }}
    .shs-header-subtitle {{
        font-size: 14px;
        color: {GRAY_MID};
        margin: 4px 0 0 0;
        font-weight: 500;
    }}

    /* Metric Cards */
    .metric-card {{
        background: {BG_CARD};
        border: 1px solid rgba(139, 5, 38, 0.3);
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }}
    .metric-card:hover {{
        border-color: {MAROON_LIGHT};
        transform: translateY(-2px);
    }}
    .metric-value {{
        font-size: 32px;
        font-weight: 800;
        color: #FFFFFF;
        line-height: 1;
        margin-bottom: 6px;
    }}
    .metric-label {{
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: {GRAY_MID};
        font-weight: 600;
    }}

    /* Badges */
    .badge-qual {{
        background: linear-gradient(135deg, #9D2235, #C4273E);
        color: #FFFFFF;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 12px;
        display: inline-block;
        box-shadow: 0 2px 8px rgba(157, 34, 53, 0.4);
    }}
    .badge-close-1s {{
        background: rgba(16, 185, 129, 0.2);
        color: #10B981;
        border: 1px solid #10B981;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 12px;
    }}
    .badge-close-2s {{
        background: rgba(59, 130, 246, 0.2);
        color: #60A5FA;
        border: 1px solid #3B82F6;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 12px;
    }}
    .badge-hunt {{
        background: rgba(138, 141, 143, 0.15);
        color: #D1D5DB;
        border: 1px solid rgba(138, 141, 143, 0.4);
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 500;
        font-size: 12px;
    }}
    .badge-close-5pct {{
        background: rgba(245, 158, 11, 0.2);
        color: #F59E0B;
        border: 1px solid #F59E0B;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 12px;
    }}
    .proximity-card {{
        background: linear-gradient(135deg, rgba(20, 24, 36, 0.95), rgba(28, 34, 52, 0.95));
        border: 1px solid rgba(138, 141, 143, 0.25);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4);
        transition: transform 0.15s ease, border-color 0.15s ease;
    }}
    .proximity-card:hover {{
        transform: translateY(-2px);
        border-color: rgba(157, 34, 53, 0.6);
    }}

    /* Qualifier Profile Card */
    .qual-card {{
        background: linear-gradient(135deg, rgba(20, 24, 36, 0.95), rgba(28, 34, 52, 0.95));
        border: 1px solid rgba(157, 34, 53, 0.4);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 14px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4);
    }}
    .qual-card-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 10px;
        margin-bottom: 10px;
    }}
    .qual-swimmer-name {{
        font-size: 18px;
        font-weight: 700;
        color: #FFFFFF;
    }}
    .qual-swimmer-meta {{
        font-size: 13px;
        color: {GRAY_MID};
    }}

    /* Streamlit Widget tweaks */
    div[data-testid="stSidebar"] {{
        background-color: #0E121B !important;
        border-right: 1px solid rgba(157, 34, 53, 0.25);
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        border-bottom: 2px solid rgba(157, 34, 53, 0.2);
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent;
        color: {GRAY_MID};
        border-radius: 6px 6px 0 0;
        font-weight: 600;
        padding: 10px 18px;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: rgba(157, 34, 53, 0.25) !important;
        color: #FFFFFF !important;
        border-bottom: 3px solid {MAROON} !important;
    }}
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# App Header & Overview Metrics
# -----------------------------------------------------------------------------
def render_header():
    summary = db.get_state_qualifiers_summary()
    roster_df = db.get_roster_df()
    meets_df = db.get_all_meets_df()

    total_swimmers = len(roster_df)
    qual_swimmers = summary["qualified_swimmers_count"]
    total_cuts = summary["total_cuts"]
    qual_relays = summary["relay_cuts_count"]
    total_meets = len(meets_df)

    img_html = f'<img src="data:image/png;base64,{LOGO_B64}" class="shs-header-logo" alt="SHS Logo">' if LOGO_B64 else ''

    st.markdown(f"""
    <div class="shs-header">
        <div class="shs-header-left">
            {img_html}
            <div>
                <h1 class="shs-header-title">Sardis High School Swim & Dive</h1>
                <p class="shs-header-subtitle">2026 AHSAA State Meet Qualifying Times (SQT) Performance Tracker</p>
            </div>
        </div>
        <div>
            <span class="badge-qual" style="font-size: 14px; padding: 6px 14px;">AHSAA 1A–5A Championship Quest</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4-Column Quick Metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{qual_swimmers} <span style="font-size: 16px; color: {GRAY_MID};">/ {total_swimmers}</span></div>
            <div class="metric-label">Swimmers Qualified</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #F59E0B;">{total_cuts}</div>
            <div class="metric-label">Total SQT Cuts Locked In</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #10B981;">{qual_relays} <span style="font-size: 16px; color: {GRAY_MID};">/ 6</span></div>
            <div class="metric-label">Relays Qualified</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #60A5FA;">{total_meets}</div>
            <div class="metric-label">Meets Contested</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")


# -----------------------------------------------------------------------------
# Tab 1: State Qualifiers Showcase
# -----------------------------------------------------------------------------
def tab_state_qualifiers():
    st.subheader("🏆 AHSAA State Championship Qualifiers")
    st.markdown("Athletes and relay teams that have successfully met or beaten the official AHSAA State Qualifying standard.")

    summary = db.get_state_qualifiers_summary()
    indiv_quals = summary["individual_qualifiers"]
    relay_quals = summary["relays_qualified"]

    if not indiv_quals and not relay_quals:
        st.info("No State Qualifiers logged yet. Import meet files in the Data Manager tab to begin tracking.")
        return

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("#### 🌟 Individual Event Qualifiers")
        for q in indiv_quals:
            cuts_items = []
            for c in q["cuts"]:
                cuts_items.append(
                    f'<div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 10px; background: rgba(0,0,0,0.25); border-radius: 6px; margin-bottom: 6px;">'
                    f'<div>'
                    f'<strong style="color: #FFFFFF;">{c["event"]}</strong>'
                    f'<span style="color: {GRAY_MID}; font-size: 12px; margin-left: 8px;">({c["meet"]})</span>'
                    f'</div>'
                    f'<div>'
                    f'<span style="font-weight: 700; color: #10B981;">{c["best_display"]}</span>'
                    f'<span style="color: {GRAY_MID}; font-size: 12px; margin: 0 4px;">vs SQT</span>'
                    f'<span style="color: {GRAY_LIGHT}; font-weight: 500;">{c["cut_display"]}</span>'
                    f'<span style="color: #F59E0B; font-size: 11px; margin-left: 6px; font-weight: 600;">(-{c["margin_sec"]:.2f}s)</span>'
                    f'</div>'
                    f'</div>'
                )
            cuts_html = "".join(cuts_items)
            grade_disp = f"Grade: {q['grade']}" if q['grade'] else "Sardis High"
            
            card_html = (
                f'<div class="qual-card">'
                f'<div class="qual-card-header">'
                f'<div>'
                f'<div class="qual-swimmer-name">{q["name"]}</div>'
                f'<div class="qual-swimmer-meta">{q["gender"]} • {grade_disp}</div>'
                f'</div>'
                f'<div>'
                f'<span class="badge-qual">{len(q["cuts"])} Event Cut{"s" if len(q["cuts"]) > 1 else ""}</span>'
                f'</div>'
                f'</div>'
                f'{cuts_html}'
                f'</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)

    with col_right:
        st.markdown("#### 🏊‍♂️ Qualified Relays")
        for r in relay_quals:
            legs_str = f"1. {r['leg1']} • 2. {r['leg2']} • 3. {r['leg3']} • 4. {r['leg4']}"
            margin = abs(r['diff_sec'])
            st.markdown(f"""
            <div class="qual-card" style="border-color: rgba(16, 185, 129, 0.4);">
                <div class="qual-card-header">
                    <div>
                        <div class="qual-swimmer-name">{r['gender']} {r['event_name']}</div>
                        <div class="qual-swimmer-meta">{r['best_meet']}</div>
                    </div>
                    <div>
                        <span class="badge-qual" style="background: linear-gradient(135deg, #059669, #10B981);">QUALIFIED</span>
                    </div>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 6px 10px; background: rgba(0,0,0,0.25); border-radius: 6px; margin-bottom: 8px;">
                    <div><strong style="color: #10B981; font-size: 18px;">{r['best_display']}</strong></div>
                    <div style="text-align: right;">
                        <span style="color: {GRAY_MID}; font-size: 12px;">SQT: {r['cut_display']}</span><br>
                        <span style="color: #F59E0B; font-weight: 700; font-size: 12px;">Beats Cut by {margin:.2f}s</span>
                    </div>
                </div>
                <div style="font-size: 12px; color: {GRAY_MID}; line-height: 1.4;">
                    <strong style="color: {GRAY_LIGHT};">Lineup:</strong> {legs_str}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("#### 📋 SQT Standards Overview")
        st_df = db.get_sqt_standards_df()
        st.dataframe(
            st_df[["gender", "event_name", "cut_display"]].rename(
                columns={"gender": "Gender", "event_name": "Event", "cut_display": "SQT Standard"}
            ),
            use_container_width=True,
            hide_index=True
        )


# -----------------------------------------------------------------------------
# Tab 2: SQT Bubble Watch & Differentials
# -----------------------------------------------------------------------------
def tab_bubble_watch():
    st.subheader("🎯 SQT Bubble Watch & Differential Analysis")
    st.markdown("Real-time differential tracking: see exactly how many seconds and percentage points each swimmer is from the AHSAA State Qualifying Time.")

    bests_df = db.get_season_bests_df()
    if bests_df.empty:
        st.info("No swim times found.")
        return

    # Filter Controls
    f1, f2, f3 = st.columns(3)
    with f1:
        gender_filter = st.selectbox("Filter Gender", ["All", "Boys (M)", "Girls (F)"], index=0)
    with f2:
        proximity_filter = st.selectbox(
            "Proximity to SQT",
            ["All Swims", "⭐ Already Qualified", "🟢 Within 1.0s", "🔵 Within 2.0s", "🟡 Within 5%", "⚪ In The Hunt (> 5%)"],
            index=0
        )
    with f3:
        all_events = ["All Events"] + sorted(list(bests_df["event_name"].unique()), key=lambda x: db.EVENT_ORDER_MAP.get(x, 99))
        event_filter = st.selectbox("Filter Event", all_events, index=0)

    filtered_df = bests_df.copy()
    if gender_filter == "Boys (M)":
        filtered_df = filtered_df[filtered_df["gender"] == "M"]
    elif gender_filter == "Girls (F)":
        filtered_df = filtered_df[filtered_df["gender"] == "F"]

    if event_filter != "All Events":
        filtered_df = filtered_df[filtered_df["event_name"] == event_filter]

    if proximity_filter == "⭐ Already Qualified":
        filtered_df = filtered_df[filtered_df["is_qualified"]]
    elif proximity_filter == "🟢 Within 1.0s":
        filtered_df = filtered_df[(filtered_df["diff_sec"] > 0) & (filtered_df["diff_sec"] <= 1.0)]
    elif proximity_filter == "🔵 Within 2.0s":
        filtered_df = filtered_df[(filtered_df["diff_sec"] > 0) & (filtered_df["diff_sec"] <= 2.0)]
    elif proximity_filter == "🟡 Within 5%":
        filtered_df = filtered_df[(filtered_df["diff_sec"] > 0) & (filtered_df["diff_pct"] <= 5.0)]
    elif proximity_filter == "⚪ In The Hunt (> 5%)":
        filtered_df = filtered_df[filtered_df["diff_pct"] > 5.0]

    # Sort so closest to cut comes first
    filtered_df = filtered_df.sort_values(by=["is_qualified", "diff_pct"], ascending=[False, True]).reset_index(drop=True)

    # Display Table with custom status rendering
    st.markdown("#### 📋 Detailed Differential Leaderboard")
    display_df = filtered_df[[
        "swimmer_name", "gender", "grade", "event_name", "best_display", "cut_display",
        "diff_sec", "diff_pct", "status", "best_meet"
    ]].copy()

    display_df["diff_sec"] = display_df["diff_sec"].apply(lambda x: f"{x:+.2f}s" if pd.notna(x) else "—")
    display_df["diff_pct"] = display_df["diff_pct"].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "—")

    display_df = display_df.rename(columns={
        "swimmer_name": "Swimmer",
        "gender": "Gender",
        "grade": "Grade",
        "event_name": "Event",
        "best_display": "Season Best",
        "cut_display": "SQT Cut",
        "diff_sec": "Time Delta",
        "diff_pct": "% Off Cut",
        "status": "Cut Status",
        "best_meet": "Achieved At"
    })

    st.dataframe(display_df, use_container_width=True, hide_index=True)


# -----------------------------------------------------------------------------
# Tab 3: Swimmer View & State Cut Differential Analyzer
# -----------------------------------------------------------------------------
def tab_swimmer_view():
    st.subheader("🏊‍♂️ Swimmer View & State Cut Differential Analyzer")
    st.markdown(
        "Individual athlete performance hub tracking every contested event, "
        "sorted by proximity to the **2026 AHSAA State Qualifying standard**."
    )

    roster_df = db.get_roster_df()
    if roster_df.empty:
        st.info("No swimmers registered. Import meet files in the Data Manager tab to begin.")
        return

    # Swimmer Selector Row
    sel_col1, sel_col2 = st.columns([1, 2])
    with sel_col1:
        gender_filter = st.selectbox(
            "Filter Roster by Gender",
            ["All Swimmers", "Boys (M)", "Girls (F)"],
            key="swimmer_view_gender_filter"
        )

    filtered_roster = roster_df.copy()
    if gender_filter == "Boys (M)":
        filtered_roster = filtered_roster[filtered_roster["gender"] == "M"]
    elif gender_filter == "Girls (F)":
        filtered_roster = filtered_roster[filtered_roster["gender"] == "F"]

    if filtered_roster.empty:
        st.warning("No swimmers found for the selected gender filter.")
        return

    # Build swimmer options with badges
    bests_df = db.get_season_bests_df()
    swimmer_cut_counts = {}
    if not bests_df.empty:
        qual_df = bests_df[bests_df["is_qualified"]]
        for s_id, grp in qual_df.groupby("swimmer_id"):
            swimmer_cut_counts[s_id] = len(grp)

    def format_swimmer_option(s_id):
        matching = filtered_roster[filtered_roster["id"] == s_id]
        if matching.empty:
            return s_id
        row = matching.iloc[0]
        grade_str = f" ({row['grade']})" if row['grade'] else ""
        cuts = swimmer_cut_counts.get(s_id, 0)
        cut_badge = f" — {cuts} Cut{'s' if cuts > 1 else ''} ⭐" if cuts > 0 else ""
        return f"{row['full_name']}{grade_str}{cut_badge}"

    swimmer_ids = list(filtered_roster["id"].unique())

    # Sync with session_state if available
    default_idx = 0
    saved_id = st.session_state.get("selected_swimmer_id")
    if saved_id and saved_id in swimmer_ids:
        default_idx = swimmer_ids.index(saved_id)

    with sel_col2:
        selected_swimmer_id = st.selectbox(
            "Select Swimmer",
            options=swimmer_ids,
            format_func=format_swimmer_option,
            index=default_idx,
            key="swimmer_view_selected_id"
        )

    # Save to session_state
    st.session_state["selected_swimmer_id"] = selected_swimmer_id

    # Fetch stats and info
    stats = db.get_swimmer_stats(selected_swimmer_id)
    if not stats:
        st.warning("Swimmer details not found.")
        return

    swimmer_name = stats["full_name"]
    gender_disp = "Boys (M)" if stats["gender"] == "M" else "Girls (F)"

    # Hero Banner / KPI Cards
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        cuts_str = f"{stats['cuts_locked']} <span style='font-size: 16px; color: {GRAY_MID};'>/ {stats['total_events']} events</span>"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: {'#10B981' if stats['cuts_locked'] > 0 else '#FFFFFF'};">{cuts_str}</div>
            <div class="metric-label">State Cuts Locked In</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi2:
        if stats["closest_cut"]:
            cc = stats["closest_cut"]
            diff_str = f"+{cc['diff_sec']:.2f}s"
            pct_str = f"+{cc['diff_pct']:.1f}%"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="font-size: 20px; color: #F59E0B; margin-top: 4px;">{cc['event']}</div>
                <div class="metric-label">Closest Cut: <span style="color: #FFFFFF; font-weight: 700;">{diff_str}</span> ({pct_str})</div>
            </div>
            """, unsafe_allow_html=True)
        elif stats["total_events"] > 0 and stats["cuts_locked"] == stats["total_events"]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="font-size: 20px; color: #10B981; margin-top: 4px;">All Qualified ⭐</div>
                <div class="metric-label">100% SQT Cut Rate</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="font-size: 20px; color: {GRAY_MID}; margin-top: 4px;">Hunting Cuts</div>
                <div class="metric-label">Building Baseline Times</div>
            </div>
            """, unsafe_allow_html=True)

    with kpi3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #60A5FA;">{stats['total_events']} <span style="font-size: 16px; color: {GRAY_MID};">({stats['swims_logged']} swims)</span></div>
            <div class="metric-label">Individual Events Contested</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi4:
        relay_label = f"{stats['relay_cuts']} Qualified ⭐" if stats['relay_cuts'] > 0 else f"{stats['relays_count']} Relays"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: {'#10B981' if stats['relay_cuts'] > 0 else '#FFFFFF'};">{stats['relays_count']} <span style="font-size: 16px; color: {GRAY_MID};">relays</span></div>
            <div class="metric-label">{relay_label}</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # Proximity Section
    st.markdown("### 🎯 Events Ranked by Proximity to AHSAA State Cut")
    st.markdown(
        "Each event is evaluated against the 2026 AHSAA Qualifying standard. "
        "Sort and filter below to focus on target opportunities or locked-in cuts."
    )

    # Sorting & Filtering Controls
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2, 2, 1])
    with ctrl_col1:
        sort_choice = st.selectbox(
            "Sort Events By",
            [
                "🎯 Closest to Next Cut First (Hunting Cuts First)",
                "⭐ State Cuts Locked In First, then Closest Hunt",
                "⏱️ Smallest Time Delta (+Seconds to Cut)",
                "📊 Smallest % Off Cut (+% to Cut)",
                "📋 Official AHSAA Championship Event Order"
            ],
            index=0,
            key="swimmer_view_sort_choice"
        )
    with ctrl_col2:
        status_filter = st.selectbox(
            "Filter Events",
            [
                "All Contested Events",
                "🎯 Hunting State Cut (Needs Cut)",
                "⭐ State Cuts Locked In"
            ],
            index=0,
            key="swimmer_view_status_filter"
        )
    with ctrl_col3:
        view_toggle = st.radio(
            "Display Style",
            ["Visual Cards", "Table View"],
            index=0,
            horizontal=True,
            key="swimmer_view_style_toggle"
        )

    # Map sort choice to internal db mode
    sort_mode_map = {
        "🎯 Closest to Next Cut First (Hunting Cuts First)": "closest_hunt",
        "⭐ State Cuts Locked In First, then Closest Hunt": "qualified_first",
        "⏱️ Smallest Time Delta (+Seconds to Cut)": "diff_sec",
        "📊 Smallest % Off Cut (+% to Cut)": "diff_pct",
        "📋 Official AHSAA Championship Event Order": "event_order"
    }
    db_sort_mode = sort_mode_map.get(sort_choice, "closest_hunt")

    proximity_df = db.get_swimmer_events_proximity_df(selected_swimmer_id, sort_by=db_sort_mode)

    if proximity_df.empty:
        st.info(f"No recorded individual times for {swimmer_name} yet this season.")
        return

    # Apply status filter
    display_df = proximity_df.copy()
    if status_filter == "🎯 Hunting State Cut (Needs Cut)":
        display_df = display_df[~display_df["is_qualified"]].reset_index(drop=True)
    elif status_filter == "⭐ State Cuts Locked In":
        display_df = display_df[display_df["is_qualified"]].reset_index(drop=True)

    if display_df.empty:
        st.info("No events match the selected status filter.")
    else:
        if view_toggle == "Visual Cards":
            # Render Proximity Cards
            for idx, r in display_df.iterrows():
                is_q = r["is_qualified"]
                d_sec = r["diff_sec"]
                d_pct = r["diff_pct"]

                if is_q:
                    badge_html = f'<span class="badge-qual">QUALIFIED ⭐ (-{abs(d_sec):.2f}s / {d_pct:.1f}%)</span>'
                    card_border = "border-color: rgba(157, 34, 53, 0.6); background: linear-gradient(135deg, rgba(28, 18, 24, 0.95), rgba(20, 24, 36, 0.95));"
                    delta_color = "#F59E0B"
                    delta_text = f"-{abs(d_sec):.2f}s under cut ({d_pct:.1f}%)"
                elif d_sec <= 1.0:
                    badge_html = f'<span class="badge-close-1s">WITHIN 1.0s (+{d_sec:.2f}s / +{d_pct:.1f}%)</span>'
                    card_border = "border-color: rgba(16, 185, 129, 0.45);"
                    delta_color = "#10B981"
                    delta_text = f"+{d_sec:.2f}s off cut (+{d_pct:.1f}%)"
                elif d_sec <= 2.0:
                    badge_html = f'<span class="badge-close-2s">WITHIN 2.0s (+{d_sec:.2f}s / +{d_pct:.1f}%)</span>'
                    card_border = "border-color: rgba(59, 130, 246, 0.45);"
                    delta_color = "#60A5FA"
                    delta_text = f"+{d_sec:.2f}s off cut (+{d_pct:.1f}%)"
                elif d_pct <= 5.0:
                    badge_html = f'<span class="badge-close-5pct">WITHIN 5% (+{d_sec:.2f}s / +{d_pct:.1f}%)</span>'
                    card_border = "border-color: rgba(245, 158, 11, 0.4);"
                    delta_color = "#F59E0B"
                    delta_text = f"+{d_sec:.2f}s off cut (+{d_pct:.1f}%)"
                else:
                    badge_html = f'<span class="badge-hunt">IN THE HUNT (+{d_sec:.2f}s / +{d_pct:.1f}%)</span>'
                    card_border = "border-color: rgba(138, 141, 143, 0.25);"
                    delta_color = GRAY_MID
                    delta_text = f"+{d_sec:.2f}s off cut (+{d_pct:.1f}%)"

                swims_badge = f"{r['swims_count']} swim{'s' if r['swims_count'] > 1 else ''} logged"

                st.markdown(f"""
                <div class="proximity-card" style="{card_border}">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div>
                            <span style="font-size: 19px; font-weight: 800; color: #FFFFFF;">{r['event_name']}</span>
                            <span style="font-size: 12px; color: {GRAY_MID}; margin-left: 8px;">#{idx + 1} Proximity Rank</span>
                        </div>
                        <div>
                            {badge_html}
                        </div>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(0,0,0,0.3); border-radius: 8px; padding: 10px 14px; margin-bottom: 8px;">
                        <div>
                            <span style="font-size: 11px; text-transform: uppercase; color: {GRAY_MID}; font-weight: 600;">Season Best</span><br>
                            <span style="font-size: 22px; font-weight: 800; color: #FFFFFF;">{r['best_display']}</span>
                        </div>
                        <div style="text-align: center;">
                            <span style="font-size: 11px; text-transform: uppercase; color: {GRAY_MID}; font-weight: 600;">State Qualifying Cut</span><br>
                            <span style="font-size: 18px; font-weight: 700; color: {GRAY_LIGHT};">{r['cut_display']}</span>
                        </div>
                        <div style="text-align: right;">
                            <span style="font-size: 11px; text-transform: uppercase; color: {GRAY_MID}; font-weight: 600;">Differential</span><br>
                            <span style="font-size: 18px; font-weight: 800; color: {delta_color};">{delta_text}</span>
                        </div>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: {GRAY_MID};">
                        <div>
                            <strong style="color: {GRAY_LIGHT};">Achieved at:</strong> {r['best_meet']} ({r['best_date']})
                        </div>
                        <div>
                            <span style="background: rgba(255,255,255,0.06); padding: 2px 8px; border-radius: 4px;">{swims_badge}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        else:
            # Table View
            table_df = display_df[[
                "event_name", "best_display", "cut_display", "diff_sec", "diff_pct", "status", "best_meet", "swims_count"
            ]].copy()
            table_df["diff_sec"] = table_df["diff_sec"].apply(lambda x: f"{x:+.2f}s" if pd.notna(x) else "—")
            table_df["diff_pct"] = table_df["diff_pct"].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "—")
            table_df = table_df.rename(columns={
                "event_name": "Event",
                "best_display": "Season Best",
                "cut_display": "SQT Standard",
                "diff_sec": "Time Delta",
                "diff_pct": "% Off Cut",
                "status": "Cut Status",
                "best_meet": "Meet Achieved",
                "swims_count": "Swims Logged"
            })
            st.dataframe(table_df, use_container_width=True, hide_index=True)

    # Relay Participation Section
    relays_df = db.get_swimmer_relays_df(selected_swimmer_id)
    if not relays_df.empty:
        st.write("")
        st.markdown("### 🤝 Championship Relay Participation")
        st.markdown(f"Relay teams where **{swimmer_name}** has contributed this season:")

        r_cols = st.columns(min(3, len(relays_df)))
        for i, (_, rel_row) in enumerate(relays_df.iterrows()):
            col_target = r_cols[i % len(r_cols)]
            with col_target:
                is_rq = rel_row["is_qualified"]
                r_badge = '<span class="badge-qual">QUALIFIED ⭐</span>' if is_rq else f'<span class="badge-close-1s">+{rel_row["diff_sec"]:.2f}s Off Cut</span>'
                r_delta_text = f"Beats Cut by {abs(rel_row['diff_sec']):.2f}s" if is_rq else f"+{rel_row['diff_sec']:.2f}s off cut"
                r_delta_color = "#10B981" if is_rq else "#F59E0B"

                legs = [rel_row["leg1"], rel_row["leg2"], rel_row["leg3"], rel_row["leg4"]]
                formatted_legs = []
                for idx_leg, swimmer_in_leg in enumerate(legs, 1):
                    if swimmer_in_leg == swimmer_name:
                        formatted_legs.append(f"<strong style='color: #F59E0B;'>{idx_leg}. {swimmer_in_leg} (★)</strong>")
                    elif swimmer_in_leg:
                        formatted_legs.append(f"{idx_leg}. {swimmer_in_leg}")
                legs_display = " • ".join(formatted_legs)

                st.markdown(f"""
                <div class="qual-card" style="margin-bottom: 12px; border-color: {'rgba(157, 34, 53, 0.5)' if is_rq else 'rgba(138, 141, 143, 0.3)'};">
                    <div class="qual-card-header">
                        <div>
                            <strong style="color: #FFFFFF; font-size: 16px;">{rel_row['event_name']} ({rel_row['team_letter']})</strong>
                            <div style="font-size: 12px; color: {GRAY_MID};">{rel_row['leg_position']}</div>
                        </div>
                        <div>{r_badge}</div>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px;">
                        <div><span style="font-size: 20px; font-weight: 800; color: #FFFFFF;">{rel_row['time_display']}</span></div>
                        <div style="font-size: 12px; color: {r_delta_color}; font-weight: 700;">{r_delta_text}</div>
                    </div>
                    <div style="font-size: 11px; color: {GRAY_MID}; margin-bottom: 6px;">
                        SQT Standard: <strong style="color: {GRAY_LIGHT};">{rel_row['cut_display']}</strong> • {rel_row['meet_name']}
                    </div>
                    <div style="font-size: 11px; color: {GRAY_MID}; line-height: 1.4; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 6px;">
                        {legs_display}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Uncontested Events Section
    uncontested_df = db.get_swimmer_uncontested_events_df(selected_swimmer_id)
    if not uncontested_df.empty:
        st.write("")
        with st.expander(f"📋 Uncontested AHSAA Championship Events ({len(uncontested_df)} Events)", expanded=False):
            st.markdown(
                f"These individual events have not been swum by **{swimmer_name}** yet this season. "
                f"Target standard times for {gender_disp}:"
            )
            u_disp = uncontested_df[["event_name", "cut_display"]].rename(columns={
                "event_name": "Event",
                "cut_display": "Target SQT Cut"
            })
            st.dataframe(u_disp, use_container_width=True, hide_index=True)

    # Meet-by-Meet Progression Chart Section
    st.write("")
    st.markdown("### 📈 Meet-over-Meet Timeline Progression")
    prog_df = db.get_swimmer_progression_df(selected_swimmer_id)
    if not prog_df.empty:
        events_swum = list(prog_df["event_name"].unique())
        prog_col1, prog_col2 = st.columns([2, 1])
        with prog_col1:
            selected_event_chart = st.selectbox(
                "Select Event for Meet-by-Meet Progression",
                events_swum,
                key="swimmer_view_chart_event"
            )

        ev_prog = prog_df[prog_df["event_name"] == selected_event_chart].sort_values("meet_date")
        if not ev_prog.empty:
            cut_sec = ev_prog["cut_seconds"].iloc[0] if pd.notna(ev_prog["cut_seconds"].iloc[0]) else None

            line_chart = alt.Chart(ev_prog).mark_line(
                point=alt.OverlayMarkDef(filled=True, size=100, color=MAROON),
                color=MAROON,
                strokeWidth=3
            ).encode(
                x=alt.X("meet_name:N", title="Meet", sort=None),
                y=alt.Y("time_seconds:Q", title="Time (Seconds)", scale=alt.Scale(zero=False)),
                tooltip=[
                    alt.Tooltip("meet_name:N", title="Meet"),
                    alt.Tooltip("time_display:N", title="Time"),
                    alt.Tooltip("time_seconds:Q", title="Seconds", format=".2f"),
                    alt.Tooltip("cut_display:N", title="SQT Standard Cut")
                ]
            ).properties(
                height=340,
                title=f"{swimmer_name} — {selected_event_chart} Season Time Progression"
            )

            if cut_sec:
                cut_data = pd.DataFrame([{"meet_name": m, "cut": cut_sec} for m in ev_prog["meet_name"]])
                cut_rule = alt.Chart(cut_data).mark_line(
                    color="#F59E0B",
                    strokeDash=[6, 4],
                    strokeWidth=2
                ).encode(
                    x=alt.X("meet_name:N", sort=None),
                    y="cut:Q"
                )
                st.altair_chart(line_chart + cut_rule, use_container_width=True)
            else:
                st.altair_chart(line_chart, use_container_width=True)


# -----------------------------------------------------------------------------
# Tab 4: Event Depth Charts
# -----------------------------------------------------------------------------
def tab_depth_charts():
    st.subheader("📊 Event Depth Charts & Team Rankings")
    st.markdown("Compare all swimmers in a specific event against each other and against the official AHSAA State Qualifying standard.")

    bests_df = db.get_season_bests_df()
    if bests_df.empty:
        st.info("No swim times available.")
        return

    e_col1, e_col2 = st.columns(2)
    with e_col1:
        gender_sel = st.selectbox("Gender", ["Boys (M)", "Girls (F)"], key="depth_gender")
        g_code = "M" if "Boys" in gender_sel else "F"
    with e_col2:
        available_events = sorted(
            list(bests_df[bests_df["gender"] == g_code]["event_name"].unique()),
            key=lambda x: db.EVENT_ORDER_MAP.get(x, 99)
        )
        if not available_events:
            st.warning("No events recorded for this gender.")
            return
        event_sel = st.selectbox("Event", available_events, key="depth_event")

    event_df = bests_df[(bests_df["gender"] == g_code) & (bests_df["event_name"] == event_sel)].sort_values("best_seconds")
    if event_df.empty:
        st.info("No swimmers have contested this event yet.")
        return

    cut_sec = event_df["cut_seconds"].iloc[0] if pd.notna(event_df["cut_seconds"].iloc[0]) else None
    cut_disp = event_df["cut_display"].iloc[0] if pd.notna(event_df["cut_display"].iloc[0]) else "—"

    st.markdown(f"**Official SQT Cut for {event_sel}:** `{cut_disp}`")

    # Depth chart
    event_df = event_df.copy()
    event_df["bar_color"] = event_df["best_seconds"].apply(
        lambda s: MAROON if (cut_sec and s <= cut_sec) else GRAY_MID
    )

    bar = alt.Chart(event_df).mark_bar(cornerRadiusEnd=4).encode(
        y=alt.Y("swimmer_name:N", sort="-x", title=None),
        x=alt.X("best_seconds:Q", title="Best Time (Seconds)", scale=alt.Scale(zero=False)),
        color=alt.Color("bar_color:N", scale=None),
        tooltip=[
            alt.Tooltip("swimmer_name:N", title="Swimmer"),
            alt.Tooltip("best_display:N", title="Time"),
            alt.Tooltip("best_seconds:Q", title="Seconds", format=".2f"),
            alt.Tooltip("status:N", title="Status")
        ]
    ).properties(height=max(200, len(event_df) * 36))

    if cut_sec:
        rule = alt.Chart(pd.DataFrame({'x': [cut_sec]})).mark_rule(color="#F59E0B", strokeWidth=3, strokeDash=[5, 5]).encode(x='x:Q')
        st.altair_chart(bar + rule, use_container_width=True)
    else:
        st.altair_chart(bar, use_container_width=True)

    # Data table
    t_df = event_df[["swimmer_name", "grade", "best_display", "cut_display", "diff_sec", "diff_pct", "status", "best_meet"]].copy()
    t_df["diff_sec"] = t_df["diff_sec"].apply(lambda x: f"{x:+.2f}s" if pd.notna(x) else "—")
    t_df["diff_pct"] = t_df["diff_pct"].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "—")
    t_df = t_df.rename(columns={
        "swimmer_name": "Swimmer",
        "grade": "Grade",
        "best_display": "Season Best",
        "cut_display": "SQT Standard",
        "diff_sec": "Differential",
        "diff_pct": "% Off Cut",
        "status": "Cut Status",
        "best_meet": "Meet Achieved"
    })
    st.dataframe(t_df, use_container_width=True, hide_index=True)


# -----------------------------------------------------------------------------
# Tab 5: Relay Teams Hub
# -----------------------------------------------------------------------------
def tab_relays():
    st.subheader("🤝 Relay Teams Hub")
    st.markdown("Track performances across all championship relays and discover optimal relay combinations.")

    relays_df = db.get_relay_bests_df()
    if relays_df.empty:
        st.info("No relay times recorded.")
        return

    r_boys = relays_df[relays_df["gender"] == "M"]
    r_girls = relays_df[relays_df["gender"] == "F"]

    b_col, g_col = st.columns(2)

    with b_col:
        st.markdown("#### 🏊‍♂️ Boys Relays")
        for _, r in r_boys.iterrows():
            badge = '<span class="badge-qual">QUALIFIED ⭐</span>' if r["is_qualified"] else f'<span class="badge-close-1s">+{r["diff_sec"]:.2f}s Off Cut</span>'
            legs_str = f"1. {r['leg1']} • 2. {r['leg2']} • 3. {r['leg3']} • 4. {r['leg4']}"
            st.markdown(f"""
            <div class="qual-card">
                <div class="qual-card-header">
                    <span style="font-size: 17px; font-weight: 700; color: #FFFFFF;">{r['event_name']}</span>
                    {badge}
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                    <div><span style="font-size: 20px; font-weight: 800; color: #FFFFFF;">{r['best_display']}</span></div>
                    <div style="color: {GRAY_MID}; font-size: 13px;">SQT Cut: <strong style="color: #F3F4F6;">{r['cut_display']}</strong></div>
                </div>
                <div style="font-size: 12px; color: {GRAY_MID}; margin-top: 4px;">
                    <strong style="color: {GRAY_LIGHT};">Lineup:</strong> {legs_str}
                </div>
            </div>
            """, unsafe_allow_html=True)

    with g_col:
        st.markdown("#### 🏊‍♀️ Girls Relays")
        for _, r in r_girls.iterrows():
            badge = '<span class="badge-qual">QUALIFIED ⭐</span>' if r["is_qualified"] else f'<span class="badge-close-1s" style="border-color: #F59E0B; color: #F59E0B;">+{r["diff_sec"]:.2f}s Off Cut</span>'
            legs_str = f"1. {r['leg1']} • 2. {r['leg2']} • 3. {r['leg3']} • 4. {r['leg4']}"
            st.markdown(f"""
            <div class="qual-card">
                <div class="qual-card-header">
                    <span style="font-size: 17px; font-weight: 700; color: #FFFFFF;">{r['event_name']}</span>
                    {badge}
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                    <div><span style="font-size: 20px; font-weight: 800; color: #FFFFFF;">{r['best_display']}</span></div>
                    <div style="color: {GRAY_MID}; font-size: 13px;">SQT Cut: <strong style="color: #F3F4F6;">{r['cut_display']}</strong></div>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 12px; color: {GRAY_MID}; margin-top: 4px;">
                    <div><strong style="color: {GRAY_LIGHT};">Lineup:</strong> {legs_str}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # Relay Permutations & Optimal Lineups
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("⚡ Projected Relay Permutations & Optimal Lineups")
    st.markdown(
        "Explore all possible relay combinations and stroke permutations sorted from **fast to slow**. "
        "Calculated by combining each swimmer's fastest recorded relay split with their fastest recorded individual 50 split "
        "(or 100 Free time for the 400 Free Relay)."
    )

    p_col1, p_col2, p_col3 = st.columns([1, 1, 1])
    with p_col1:
        sel_gender_label = st.radio("Gender", ["🏊‍♂️ Boys", "🏊‍♀️ Girls"], horizontal=True, key="relay_perm_gender")
        sel_gender = "M" if "Boys" in sel_gender_label else "F"

    with p_col2:
        relay_events = ["200 Free Relay", "200 Medley Relay", "400 Free Relay"]
        sel_event = st.selectbox("Relay Event", relay_events, key="relay_perm_event")

    perms_df = db.get_relay_permutations_df(sel_event, sel_gender)

    with p_col3:
        all_swimmers = set()
        if not perms_df.empty:
            for col in ["leg1_name", "leg2_name", "leg3_name", "leg4_name"]:
                all_swimmers.update(perms_df[col].dropna().unique())
        swimmer_options = ["All Swimmers"] + sorted(list(all_swimmers))
        sel_swimmer = st.selectbox("Filter by Swimmer", swimmer_options, key="relay_perm_swimmer")

    if perms_df.empty:
        st.warning(f"Not enough swimmers with recorded times to form a {sel_gender_label} {sel_event}.")
        with st.expander("🛠️ Manage Swimmer Splits & Exclude Bad Splits", expanded=False):
            render_splits_manager(default_gender=sel_gender, key_prefix="relays")
        return

    # Filter by swimmer if selected
    filtered_df = perms_df.copy()
    if sel_swimmer != "All Swimmers":
        mask = (
            (filtered_df["leg1_name"] == sel_swimmer) |
            (filtered_df["leg2_name"] == sel_swimmer) |
            (filtered_df["leg3_name"] == sel_swimmer) |
            (filtered_df["leg4_name"] == sel_swimmer)
        )
        filtered_df = filtered_df[mask].reset_index(drop=True)

    # Top Optimal Lineup vs Current Season Best Comparison Cards
    top_perm = perms_df.iloc[0]

    actual_bests = relays_df[(relays_df["gender"] == sel_gender) & (relays_df["event_name"] == sel_event)]
    actual_best_row = actual_bests.iloc[0] if not actual_bests.empty else None

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #38BDF8;">{top_perm['projected_display']}</div>
            <div class="metric-label">🥇 Optimal Projected Time</div>
        </div>
        """, unsafe_allow_html=True)

    with m2:
        act_disp = actual_best_row['best_display'] if actual_best_row is not None else "None Logged"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #FFFFFF;">{act_disp}</div>
            <div class="metric-label">⏱️ Season Best Swum</div>
        </div>
        """, unsafe_allow_html=True)

    with m3:
        if actual_best_row is not None:
            imp_sec = actual_best_row['best_seconds'] - top_perm['projected_seconds']
            if imp_sec > 0:
                imp_text = f"-{imp_sec:.2f}s"
                imp_color = "#10B981"
            elif imp_sec < 0:
                imp_text = f"+{abs(imp_sec):.2f}s"
                imp_color = "#F59E0B"
            else:
                imp_text = "0.00s (Matched)"
                imp_color = "#38BDF8"
        else:
            imp_text = "N/A"
            imp_color = GRAY_MID
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: {imp_color};">{imp_text}</div>
            <div class="metric-label">🚀 Projected Improvement</div>
        </div>
        """, unsafe_allow_html=True)

    with m4:
        cut_disp = top_perm['cut_display']
        if pd.notna(top_perm['cut_seconds']):
            if top_perm['is_qualified']:
                status_html = f'<span class="badge-qual">QUALIFIED ⭐ {top_perm["status"]}</span>'
            else:
                status_html = f'<span class="badge-close-1s" style="border-color: #F59E0B; color: #F59E0B;">{top_perm["status"]} Off Cut</span>'
        else:
            status_html = '<span class="badge-close-2s">No Standard</span>'
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="font-size: 24px; color: #FFFFFF;">{cut_disp}</div>
            <div class="metric-label">🎯 SQT Standard Cut</div>
            <div style="margin-top: 6px;">{status_html}</div>
        </div>
        """, unsafe_allow_html=True)

    # Highlight Optimal Lineup
    st.markdown(f"""
    <div style="background: rgba(20, 24, 36, 0.9); border: 1px solid rgba(56, 189, 248, 0.4); border-radius: 10px; padding: 14px 18px; margin: 16px 0;">
        <span style="font-weight: 700; color: #38BDF8; font-size: 14px;">⚡ OPTIMAL PROJECTED LINEUP:</span>
        <span style="color: #F3F4F6; font-size: 14px; margin-left: 8px;">{top_perm['lineup_display']}</span>
    </div>
    """, unsafe_allow_html=True)

    # Interactive Table
    is_medley = "Medley" in sel_event
    table_rows = []
    for _, row in filtered_df.iterrows():
        if is_medley:
            l1 = f"Back: {row['leg1_name']} ({row['leg1_display']})"
            l2 = f"Breast: {row['leg2_name']} ({row['leg2_display']})"
            l3 = f"Fly: {row['leg3_name']} ({row['leg3_display']})"
            l4 = f"Free: {row['leg4_name']} ({row['leg4_display']})"
        else:
            l1 = f"{row['leg1_name']} ({row['leg1_display']})"
            l2 = f"{row['leg2_name']} ({row['leg2_display']})"
            l3 = f"{row['leg3_name']} ({row['leg3_display']})"
            l4 = f"{row['leg4_name']} ({row['leg4_display']})"

        table_rows.append({
            "Rank": f"#{int(row['rank'])}",
            "Projected Time": row["projected_display"],
            "SQT Cut Status": row["status"] if not row["is_qualified"] else "QUALIFIED ⭐",
            "Leg 1": l1,
            "Leg 2": l2,
            "Leg 3": l3,
            "Leg 4": l4,
        })

    display_df = pd.DataFrame(table_rows)

    c_left, c_right = st.columns([3, 1])
    with c_left:
        st.markdown(f"**Showing {len(display_df)} permutation{'s' if len(display_df) != 1 else ''}** (sorted fast to slow):")
    with c_right:
        csv_data = filtered_df[[
            "rank", "event_name", "gender", "projected_display", "status",
            "leg1_name", "leg1_display", "leg2_name", "leg2_display",
            "leg3_name", "leg3_display", "leg4_name", "leg4_display"
        ]].to_csv(index=False)
        st.download_button(
            "📥 Export Permutations CSV",
            data=csv_data,
            file_name=f"{sel_gender}_{sel_event.replace(' ', '_')}_permutations.csv",
            mime="text/csv",
            use_container_width=True
        )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=min(450, 40 + len(display_df) * 36)
    )

    # Bad Split Exclusion Tool
    with st.expander("🛠️ Manage Swimmer Splits & Exclude Bad Splits", expanded=False):
        render_splits_manager(default_gender=sel_gender, key_prefix="relays")


def render_splits_manager(default_gender: Optional[str] = None, key_prefix: str = "relays"):
    """
    Renders an administrative tool to inspect, filter, exclude, or restore individual split times.
    """
    st.markdown(
        "Occasionally a touchpad error, missed touch, or timing anomaly produces an invalid split time. "
        "Use this tool to exclude bad splits from all relay calculations. Excluded splits remain in the database for reference but are omitted from relay permutations."
    )

    all_splits_df = db.get_all_splits_df(gender=default_gender)
    if all_splits_df.empty:
        st.info("No splits recorded yet.")
        return

    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        sw_filter_list = ["All Swimmers"] + sorted(all_splits_df["swimmer_name"].unique().tolist())
        m_swimmer = st.selectbox("Filter Swimmer", sw_filter_list, key=f"{key_prefix}_m_swimmer")
    with f_col2:
        m_stroke = st.selectbox("Filter Stroke", ["All Strokes", "Free", "Back", "Breast", "Fly"], key=f"{key_prefix}_m_stroke")
    with f_col3:
        m_status = st.selectbox("Filter Status", ["All", "Active Only", "Excluded Only"], key=f"{key_prefix}_m_status")

    view_df = all_splits_df.copy()
    if m_swimmer != "All Swimmers":
        view_df = view_df[view_df["swimmer_name"] == m_swimmer]
    if m_stroke != "All Strokes":
        view_df = view_df[view_df["stroke"] == m_stroke]
    if m_status == "Active Only":
        view_df = view_df[view_df["is_excluded"] == 0]
    elif m_status == "Excluded Only":
        view_df = view_df[view_df["is_excluded"] == 1]

    st.dataframe(
        view_df[[
            "swimmer_name", "meet_name", "event_name", "stroke",
            "split_distance", "split_display", "type_display", "status_display"
        ]].rename(columns={
            "swimmer_name": "Swimmer",
            "meet_name": "Meet",
            "event_name": "Event",
            "stroke": "Stroke",
            "split_distance": "Dist (yd)",
            "split_display": "Split Time",
            "type_display": "Type",
            "status_display": "Status"
        }),
        use_container_width=True,
        hide_index=True,
        height=min(260, 40 + len(view_df) * 36)
    )

    st.markdown("##### ⚡ Quick Exclude / Restore Action")
    if not view_df.empty:
        split_choices = {}
        for _, r in view_df.iterrows():
            lbl = f"{r['swimmer_name']} • {r['stroke']} {r['split_distance']}y ({r['split_display']}) @ {r['meet_name']} [{r['type_display']}] — {r['status_display']}"
            split_choices[lbl] = r

        selected_split_label = st.selectbox(
            "Select a split to toggle exclusion:",
            list(split_choices.keys()),
            key=f"{key_prefix}_select_split"
        )
        selected_row = split_choices[selected_split_label]

        act_col1, act_col2, act_col3 = st.columns([1, 1, 2])
        with act_col1:
            if st.button("🚫 Exclude Split", key=f"{key_prefix}_btn_exclude", use_container_width=True, disabled=(selected_row["is_excluded"] == 1)):
                db.set_split_exclusion(selected_row["split_id"], True)
                db.export_data_to_csv()
                st.success(f"Excluded {selected_row['swimmer_name']}'s {selected_row['split_display']} split!")
                st.rerun()
        with act_col2:
            if st.button("🔄 Restore Split", key=f"{key_prefix}_btn_restore", use_container_width=True, disabled=(selected_row["is_excluded"] == 0)):
                db.set_split_exclusion(selected_row["split_id"], False)
                db.export_data_to_csv()
                st.success(f"Restored {selected_row['swimmer_name']}'s {selected_row['split_display']} split!")
                st.rerun()
        with act_col3:
            if selected_row["is_excluded"] == 1:
                st.info(f"Split is currently **Excluded 🚫** and omitted from relay permutations.")
            else:
                st.caption(f"Split is currently **Active ✅** and factored into relay permutations.")


# -----------------------------------------------------------------------------
# Tab 6: Meets & Data Manager
# -----------------------------------------------------------------------------
def tab_data_manager():
    st.subheader("📁 Meets & Data Manager")
    st.markdown("Manage season results, upload new meet `.cl2` or `.zip` files, and export database tables.")

    meets_df = db.get_all_meets_df()
    st.markdown("#### 🗓️ Season Meets on Record")
    if not meets_df.empty:
        st.dataframe(
            meets_df.rename(columns={
                "meet_name": "Meet Name",
                "meet_date": "Meet Date",
                "individual_swims": "Individual Swims",
                "relay_swims": "Relays Logged"
            })[["Meet Name", "Meet Date", "Individual Swims", "Relays Logged"]],
            use_container_width=True,
            hide_index=True
        )

    st.write("")
    st.markdown("#### 📤 Upload New Meet Results")
    st.markdown("Upload a Hy-Tek `.cl2` file or `.zip` archive from an upcoming meet. The database will automatically parse Sardis High School entries and update SQT differentials.")

    uploaded_file = st.file_uploader("Choose a .cl2 or .zip file", type=["cl2", "zip"])
    if uploaded_file is not None:
        save_path = os.path.join(db.TIMES_DIR, uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"Saved {uploaded_file.name} to times folder!")
        if st.button("🚀 Process & Import Meet Into Database"):
            if uploaded_file.name.endswith(".zip"):
                import zipfile
                with zipfile.ZipFile(save_path, 'r') as zf:
                    zf.extractall(db.TIMES_DIR)
            results = db.import_all_meets_in_times()
            db.export_data_to_csv()
            st.success("Successfully imported and updated season bests!")

            # Auto-export team records & push to GitHub Pages
            with st.spinner("Pushing updated team records to GitHub Pages..."):
                try:
                    import export_records
                    success, msg = export_records.export_and_push(uploaded_file.name)
                    if success:
                        st.success(f"🌐 GitHub Pages: {msg}")
                    else:
                        st.warning(f"⚠️ GitHub Pages push note: {msg}")
                except Exception as e:
                    st.warning(f"⚠️ Could not push to GitHub Pages: {e}")

            st.rerun()

    st.write("")
    st.markdown("#### 🔄 Re-Sync & Export Data")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔁 Re-scan All Meets in Times Folder"):
            with st.spinner("Re-importing meets..."):
                db.import_all_meets_in_times()
                db.export_data_to_csv()
                st.success("Database fully re-synchronized with all files in times/ folder!")
                st.rerun()
    with col2:
        if st.button("💾 Export SQLite Tables to CSV"):
            db.export_data_to_csv()
            st.success("CSVs exported to data/ folder for diffable backup!")
    with col3:
        if st.button("🌐 Push Records to GitHub Pages"):
            with st.spinner("Exporting & pushing records to GitHub Pages..."):
                try:
                    import export_records
                    success, msg = export_records.export_and_push()
                    if success:
                        st.success(f"✅ {msg}")
                    else:
                        st.error(f"❌ {msg}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    st.write("")
    st.markdown("#### ⏱️ Swimmer Split Times & Exclusion Manager")
    render_splits_manager(default_gender=None, key_prefix="datamanager")


# -----------------------------------------------------------------------------
# Main Application Flow
# -----------------------------------------------------------------------------
def main():
    render_header()

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏆 State Qualifiers",
        "🎯 SQT Bubble Watch",
        "🏊‍♂️ Swimmer View",
        "📊 Depth Charts",
        "🤝 Relays",
        "📁 Data Manager"
    ])

    with tab1:
        tab_state_qualifiers()
    with tab2:
        tab_bubble_watch()
    with tab3:
        tab_swimmer_view()
    with tab4:
        tab_depth_charts()
    with tab5:
        tab_relays()
    with tab6:
        tab_data_manager()


if __name__ == "__main__":
    main()
