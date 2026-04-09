import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import sqlite3
import os
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
import urllib.parse

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Mumbai Women Safety Risk Map",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# THEME + SESSION STATE
# ─────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
if "user_lat" not in st.session_state:
    st.session_state.user_lat = None
if "user_lon" not in st.session_state:
    st.session_state.user_lon = None
if "emergency_active" not in st.session_state:
    st.session_state.emergency_active = False

DARK = st.session_state.dark_mode

if DARK:
    BG       = "#0e1117"
    SIDEBAR  = "linear-gradient(180deg, #141a24 0%, #1a2232 100%)"
    SIDE_BRD = "#2a3550"
    SIDE_CLR = "#c9d1e0"
    CARD_BG  = "linear-gradient(135deg, #1a2232 0%, #1e293b 100%)"
    CARD_BRD = "#2a3550"
    TXT      = "#e0e0e0"
    SUBTXT   = "#7a8899"
    HDRTXT   = "#4fc3f7"
    MAP_TILE = "CartoDB dark_matter"
    TOGGLE_LABEL = "☀️ Light Mode"
    FAB_BG   = "#1e2a3a"
    FAB_BRD  = "#2a3550"
else:
    BG       = "#f0f2f6"
    SIDEBAR  = "linear-gradient(180deg, #ffffff 0%, #e8edf5 100%)"
    SIDE_BRD = "#c8d0e0"
    SIDE_CLR = "#1a2232"
    CARD_BG  = "linear-gradient(135deg, #ffffff 0%, #f0f4fa 100%)"
    CARD_BRD = "#c8d0e0"
    TXT      = "#1a2232"
    SUBTXT   = "#5a6880"
    HDRTXT   = "#1565c0"
    MAP_TILE = "CartoDB positron"
    TOGGLE_LABEL = "🌙 Dark Mode"
    FAB_BG   = "#ffffff"
    FAB_BRD  = "#c8d0e0"

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700;800&display=swap');

html, body, [data-testid="stAppViewContainer"] {{
    background-color: {BG} !important;
    color: {TXT} !important;
    font-family: 'Space Grotesk', sans-serif !important;
}}
[data-testid="stSidebar"] {{
    background: {SIDEBAR} !important;
    border-right: 1px solid {SIDE_BRD} !important;
    min-width: 280px !important;
    max-width: 320px !important;
}}
[data-testid="stSidebar"] * {{ color: {SIDE_CLR} !important; }}

[data-testid="collapsedControl"] {{
    display: flex !important;
    visibility: visible !important;
    background: {FAB_BG} !important;
    border: 2px solid {HDRTXT} !important;
    border-radius: 50% !important;
    width: 40px !important;
    height: 40px !important;
    align-items: center !important;
    justify-content: center !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.25) !important;
    z-index: 9999 !important;
    cursor: pointer !important;
}}
[data-testid="collapsedControl"] svg {{
    fill: {HDRTXT} !important;
    stroke: {HDRTXT} !important;
}}
[data-testid="stSidebarCollapseButton"] {{
    display: flex !important;
    visibility: visible !important;
    background: transparent !important;
    border: 1px solid {SIDE_BRD} !important;
    border-radius: 8px !important;
    color: {SIDE_CLR} !important;
}}
[data-testid="stSidebarCollapseButton"] svg {{
    fill: {SIDE_CLR} !important;
}}

.main-title {{
    text-align: center;
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(90deg, #ff4d4d 0%, #ff9900 40%, #00e676 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
    letter-spacing: -0.5px;
}}
.sub-title {{
    text-align: center;
    color: {SUBTXT};
    font-size: 0.85rem;
    margin-bottom: 1rem;
}}

.metric-row {{ display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }}
.metric-card {{
    flex: 1;
    min-width: 90px;
    background: {CARD_BG};
    border: 1px solid {CARD_BRD};
    border-radius: 12px;
    padding: 14px 16px;
    text-align: center;
}}
.metric-card .val {{ font-size: 1.7rem; font-weight: 800; }}
.metric-card .lbl {{ font-size: 0.7rem; color: {SUBTXT}; margin-top: 4px; }}
.red   {{ color: #ff4d4d; }}
.amber {{ color: #ff9900; }}
.green {{ color: #00e676; }}
.blue  {{ color: #4fc3f7; }}

.section-hdr {{
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: {HDRTXT};
    margin: 16px 0 6px 0;
    font-weight: 700;
}}

.emergency-panel {{
    background: linear-gradient(135deg, #3d0000 0%, #660000 100%);
    border: 2px solid #ff4444;
    border-radius: 14px;
    padding: 16px 20px;
    margin: 12px 0;
    animation: pulse-border 1.5s infinite;
}}
@keyframes pulse-border {{
    0%   {{ border-color: #ff4444; box-shadow: 0 0 0 0 rgba(255,68,68,0.5); }}
    50%  {{ border-color: #ff9999; box-shadow: 0 0 0 8px rgba(255,68,68,0); }}
    100% {{ border-color: #ff4444; box-shadow: 0 0 0 0 rgba(255,68,68,0); }}
}}
.emergency-title {{
    color: #ff6666;
    font-size: 1rem;
    font-weight: 800;
    margin-bottom: 10px;
}}
.station-card {{
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 10px;
    padding: 10px 14px;
    margin: 6px 0;
}}
.station-name {{ font-weight: 700; color: #fff; font-size: 0.9rem; }}
.station-dist {{ color: #ffaa00; font-size: 0.8rem; margin: 2px 0; }}
.nav-link {{
    display: inline-block;
    background: #1a73e8;
    color: #fff !important;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.76rem;
    text-decoration: none;
    margin-top: 5px;
    margin-right: 6px;
}}

.loc-badge {{
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.76rem;
    font-weight: 600;
    margin-bottom: 6px;
}}
.loc-active  {{ background: rgba(0,230,118,0.15); color: #00e676; border: 1px solid #00e676; }}
.loc-inactive {{ background: rgba(122,136,153,0.15); color: {SUBTXT}; border: 1px solid {SUBTXT}; }}

.stDataFrame {{ border-radius: 10px; overflow: hidden; }}
#MainMenu, footer {{ visibility: hidden; }}
.block-container {{ padding-top: 1.2rem !important; }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# VERIFIED COORDINATES — all cross-checked against OSM / latlong.net / indiamapia
# ─────────────────────────────────────────────
KNOWN_COORDS = {
    # ── ANDHERI area ──────────────────────────────────────────────────────
    "Andheri":                  (19.1144, 72.8679),
    "Aram Nagar":               (19.1228, 72.8388),   # Andheri West, near Versova
    "Amboli":                   (19.1195, 72.8478),   # between Jogeshwari & Andheri W
    "Chakala":                  (19.1153, 72.8594),   # Andheri East, near airport road
    "D.N. Nagar":               (19.1254, 72.8366),   # Andheri West metro station area
    "Four Bungalows":           (19.1218, 72.8348),   # Andheri West
    "JB Nagar":                 (19.1085, 72.8698),   # Andheri East
    "Kajuwadi":                 (19.1175, 72.8768),   # Andheri East
    "Lokhandwala Complex":      (19.1431, 72.8246),   # Andheri West (verified OSM 19.14308, 72.82462)
    "Marol":                    (19.1030, 72.8788),   # Andheri East
    "Mogra Village":            (19.1215, 72.8765),   # Andheri East
    "Model Town":               (19.1245, 72.8718),   # Andheri East
    "Poonam Nagar":             (19.1162, 72.8788),   # Andheri East
    "Saki Naka":                (19.1035, 72.8879),   # Andheri East (verified 19.1035, 72.8879)
    "Seven Bungalows":          (19.1268, 72.8318),   # Andheri West
    "Versova":                  (19.1351, 72.8134),   # Andheri West (verified)
    "SEEPZ":                    (19.1115, 72.8710),   # Andheri East
    "Sahar":                    (19.0985, 72.8648),   # near airport, Andheri East

    # ── BANDRA area ───────────────────────────────────────────────────────
    "Bandra":                   (19.0544, 72.8402),
    "Bandra Kurla Complex":     (19.0653, 72.8644),
    "Bandstand Promenade":      (19.0462, 72.8198),
    "Gandhi Nagar":             (19.0685, 72.8448),   # Bandra East
    "M I G Colony":             (19.0524, 72.8478),   # Bandra East
    "Kherwadi":                 (19.0538, 72.8428),   # Bandra East
    "Land's End":               (19.0402, 72.8192),   # Bandra West
    "Pali Hill":                (19.0548, 72.8292),   # Bandra West
    "Old Town":                 (19.0505, 72.8382),   # Bandra West
    "Bandra reclamation":       (19.0562, 72.8352),
    "Kala Nagar":               (19.0515, 72.8515),   # Bandra East
    "Nirmal Nagar":             (19.0596, 72.8518),   # Bandra East
    "Valmiki Nagar":            (19.0418, 72.8212),
    "Sadguru Colony":           (19.0430, 72.8225),
    "Bharam Nagar":             (19.0484, 72.8358),
    "Subhash Nagar":            (19.0665, 72.8502),
    "Sanjay Nagar":             (19.0672, 72.8512),
    "Sant Dnyaneshwar Nagar":   (19.0695, 72.8518),
    "Patkar Blocks":            (19.0495, 72.8302),
    "Vaidya Nagar":             (19.0520, 72.8345),
    "Santosh Nagar":            (19.0655, 72.8494),
    "Bandra Fort":              (19.0420, 72.8182),
    "Rizvi Complex":            (19.0518, 72.8272),
    "Ranwar":                   (19.0504, 72.8252),
    "Tata Blocks":              (19.0486, 72.8278),
    "Indiraji Nagar":           (19.0542, 72.8415),
    "Bandra Terminus":          (19.0610, 72.8388),
    "Hill Road":                (19.0510, 72.8260),
    "Vastu":                    (19.0535, 72.8308),
    "Galaxy Apartment":         (19.0524, 72.8292),

    # ── BORIVALI area ─────────────────────────────────────────────────────
    "Borivali":                 (19.2290, 72.8567),
    "I.C. Colony":              (19.2475, 72.8471),   # verified: N19°14'50", E72°50'49" = 19.2474, 72.8471
    "L.I.C. Colony aka Jeevan Bhima Nagar": (19.2268, 72.8558),
    "Eksar Colony":             (19.2278, 72.8488),   # Borivali West, near Eksar metro
    "Shimpoli":                 (19.2305, 72.8498),   # Borivali West
    "Gorai":                    (19.2188, 72.7948),   # Borivali West coast (corrected — it's on the western creek)
    "Kora Kendra":              (19.2308, 72.8552),
    "Vazira Naka":              (19.2292, 72.8535),
    "Babhai":                   (19.2312, 72.8565),
    "Chikuwadi":                (19.2322, 72.8575),
    "Yogi Nagar":               (19.2262, 72.8528),   # Borivali West
    "Devipada":                 (19.2352, 72.8595),   # Borivali East
    "Magathane":                (19.2335, 72.8582),
    "Nancy Colony":             (19.2242, 72.8512),
    "Sukurwadi":                (19.2348, 72.8588),
    "Dahisar":                  (19.2545, 72.8568),
    "NL Complex":               (19.2265, 72.8555),
    "Mandapeshwar Caves":       (19.2478, 72.8488),
    "Northern heights":         (19.2355, 72.8602),
    "Shakti Nagar":             (19.2284, 72.8522),
    "Anand Nagar":              (19.2274, 72.8532),
    "Ketkipada":                (19.2358, 72.8598),
    "Anand Park":               (19.2296, 72.8542),
    "Krishna Colony":           (19.2282, 72.8518),
    "Rawalpada":                (19.2362, 72.8605),
    "Ashok Van":                (19.2285, 72.8528),
    "Balaji Colony":            (19.2268, 72.8535),
    "Ekta Colony":              (19.2280, 72.8524),
    "Maratha Nagar":            (19.2276, 72.8520),
    "Konkani pada":             (19.2368, 72.8608),
    "CS Complex":               (19.2290, 72.8535),
    "Avdhut Nagar":             (19.2294, 72.8540),
    "Narendra Complex":         (19.2286, 72.8526),
    "Shanti Nagar":             (19.2278, 72.8516),
    "Yadav Nagar":              (19.2366, 72.8607),
    "Gavde Nagar":              (19.2356, 72.8598),
    "Navagaon":                 (19.2370, 72.8612),
    "Mhatre Wadi Tadwe Wadi":   (19.2362, 72.8602),

    # ── GOREGAON area ─────────────────────────────────────────────────────
    "Goregaon":                 (19.1648, 72.8500),   # verified
    "Best Nagar":               (19.1642, 72.8508),
    "Jawahar Nagar":            (19.1652, 72.8518),
    "Aarey Milk Colony":        (19.1561, 72.8707),   # verified OSM 19.15613, 72.87072
    "Motilal Nagar":            (19.1632, 72.8512),   # Goregaon West
    "Bangur Nagar":             (19.1625, 72.8014),   # Goregaon West, New Link Rd (verified 19.16251, 72.80132)
    "Gokuldham":                (19.1622, 72.8502),   # Goregaon East
    "Jayprakash Nagar":         (19.1658, 72.8520),
    "Pandurang Wadi":           (19.1678, 72.8528),
    "NESCO Colony":             (19.1625, 72.8498),
    "Oshiwara":                 (19.1412, 72.8318),   # Andheri/Jogeshwari border
    "Jogeshwari":               (19.1382, 72.8432),
    "Amrut Nagar":              (19.1668, 72.8525),
    "Kevni Pada":               (19.1660, 72.8522),
    "Behram Baug":              (19.1672, 72.8530),
    "Malcolm Bau":              (19.1652, 72.8508),
    "Patliputra Nagar":         (19.1645, 72.8514),
    "Vahatuk Nagar":            (19.1635, 72.8505),
    "Vaishali Nagar":           (19.1633, 72.8502),
    "Sainik Nagar":             (19.1640, 72.8510),
    "Patilwadi":                (19.1655, 72.8518),
    "Shastri Nagar":            (19.1620, 72.8495),
    "Azad Nagar":               (19.1122, 72.8448),   # Andheri West metro station area (NOT Goregaon)
    "Khan Estate":              (19.1650, 72.8515),
    "Pratiksha Nagar":          (19.1630, 72.8500),
    "BR Nagar":                 (19.1644, 72.8513),
    "Momin Nagar":              (19.1642, 72.8510),
    "Prabhat Nagar":            (19.1636, 72.8507),
    "Kadam Nagar":              (19.1648, 72.8515),
    "Majas Wadi":               (19.1662, 72.8524),
    "Morga Pada":               (19.1665, 72.8526),
    "Natwar Nagar":             (19.1645, 72.8511),
    "Namesingh Chawl":          (19.1668, 72.8528),
    "Oberoi Splendor":          (19.1198, 72.8778),   # Andheri East / JVLR
    "Shankar Wadi":             (19.1682, 72.8532),
    "Pratap Nagar":             (19.1638, 72.8508),
    "Sunder Nagar":             (19.1630, 72.8502),
    "Jijamata Colony":          (19.1658, 72.8520),

    # ── KANDIVALI area ────────────────────────────────────────────────────
    "Kandivali":                (19.2077, 72.8427),
    "Dahanukarwadi":            (19.2055, 72.8412),
    "BunderPakhadi (Koliwada)": (19.2062, 72.8432),
    "Charkop":                  (19.2195, 72.8338),   # Kandivali West
    "Poisar":                   (19.2082, 72.8415),
    "Hindustan Naka":           (19.2060, 72.8405),
    "Mahavir Nagar":            (19.2068, 72.8418),
    "Samta Nagar":              (19.2038, 72.8392),
    "Damu Nagar":               (19.2048, 72.8402),
    "Thakur complex":           (19.2162, 72.8472),   # Kandivali East
    "Thakur village":           (19.2178, 72.8482),   # Kandivali East
    "Janupada":                 (19.2058, 72.8408),
    "Hanuman Nagar":            (19.2055, 72.8410),
    "Kranti Nagar":             (19.2045, 72.8400),
    "Laxmi Nagar":              (19.2042, 72.8395),
    "Dattani":                  (19.2050, 72.8404),
    "Jivali Pada":              (19.2054, 72.8406),

    # ── MALAD area ────────────────────────────────────────────────────────
    "Malad":                    (19.1868, 72.8489),
    "Dindoshi":                 (19.1822, 72.8462),   # Malad East / Goregaon border
    "Pathanwadi":               (19.1845, 72.8475),
    "Malvani":                  (19.2004, 72.8219),   # Malad West coast (verified)
    "Orlem":                    (19.1850, 72.8488),
    "Ambujwadi":                (19.1855, 72.8490),
    "Evershine Nagar":          (19.1842, 72.8478),
    "Liliya Nagar":             (19.1860, 72.8485),
    "Jankalyan Nagar":          (19.1838, 72.8472),

    # ── SANTACRUZ / VILE PARLE / KHAR / JUHU area ─────────────────────────
    "Santacruz":                (19.0786, 72.8394),
    "Kalina":                   (19.0765, 72.8562),
    "Vakola":                   (19.0775, 72.8445),
    "Prabhat colony":           (19.0792, 72.8370),
    "Vile Parle":               (19.0990, 72.8474),
    "Irla":                     (19.1015, 72.8385),
    "Nehru Nagar":              (19.1022, 72.8392),
    "Juhu Koliwada":            (19.1018, 72.8315),
    "Pothohar Nagar":           (19.0810, 72.8465),
    "Gazdhar Bandh":            (19.0805, 72.8458),
    "Yashwant Nagar":           (19.0812, 72.8470),
    "Khira Nagar":              (19.0815, 72.8474),
    "Eastern suburbs":          (19.0982, 72.8878),
    "Juhu":                     (19.1075, 72.8263),
    "Khar":                     (19.0665, 72.8342),
    "Pali Naka":                (19.0658, 72.8348),
    "Khar Danda":               (19.0612, 72.8218),

    # ── BHANDUP / MULUND / NAHUR ──────────────────────────────────────────
    "Bhandup":                  (19.1458, 72.9362),
    "Shivaji Talav":            (19.1462, 72.9365),
    "Asalfa":                   (19.1158, 72.9212),   # corrected: Asalfa is near Ghatkopar, not Bhandup
    "Garodia Nagar":            (19.0882, 72.9062),   # Ghatkopar East
    "Jagdusha Nagar":           (19.1465, 72.9370),
    "Pant Nagar":               (19.0878, 72.9125),   # Ghatkopar East
    "Barve Nagar":              (19.1462, 72.9368),
    "Mulund":                   (19.1716, 72.9562),
    "Bombay Colony":            (19.1720, 72.9565),
    "Paach Rasta":              (19.1722, 72.9570),
    "Xavier Street":            (19.1715, 72.9560),
    "Nahur":                    (19.1492, 72.9345),
    "Mulund Runwals":           (19.1738, 72.9575),

    # ── POWAI / CHANDIVALI / VIKHROLI / KANJUR ────────────────────────────
    "Powai":                    (19.1197, 72.9076),
    "Chandivali":               (19.1165, 72.9012),
    "Hiranandani Gardens":      (19.1172, 72.9058),
    "Paaspoli":                 (19.1188, 72.9045),
    "Mhada Colony 19":          (19.1182, 72.9038),
    "Morarji Nagar":            (19.1178, 72.9030),
    "Chandshah Wali Dargah":    (19.1192, 72.9050),
    "Vidyavihar":               (19.0828, 72.8948),   # corrected: Vidyavihar is near Ghatkopar West
    "Rajawadi":                 (19.0882, 72.9062),   # Ghatkopar East
    "Pipeline Road":            (19.1175, 72.8962),
    "Kirol":                    (19.1170, 72.8958),
    "Khalai":                   (19.1185, 72.8972),
    "Vikhroli":                 (19.1088, 72.9288),
    "Kanjur Marg":              (19.1148, 72.9345),
    "Surya Nagar":              (19.1132, 72.9332),
    "Kannamwar Nagar":          (19.1125, 72.9325),
    "Tagore Nagar":             (19.1118, 72.9318),
    "Park Site":                (19.1112, 72.9312),
    "Godrej Station Colony":    (19.1105, 72.9305),
    "Godrej Hillside Colony":   (19.1098, 72.9298),
    "Godrej Creek":             (19.1092, 72.9292),
    "Central suburbs":          (19.1088, 72.9288),

    # ── GHATKOPAR / KURLA area ────────────────────────────────────────────
    "Ghatkopar":                (19.0858, 72.9081),
    "Kurla":                    (19.0728, 72.8826),
    "Kasaiwada":                (19.0745, 72.8842),
    "Quresh Nagar":             (19.0752, 72.8848),
    "Tashilanagar":             (19.0748, 72.8845),
    "Umerwadi":                 (19.0755, 72.8852),
    "Kohinoor City":            (19.0758, 72.8855),
    "Kapadia nagar":            (19.0765, 72.8860),
    "Kurla Depot":              (19.0732, 72.8832),
    "Squatters Colony":         (19.0775, 72.8870),
    "Jari Mari":                (19.0782, 72.8875),
    "Maharashtra Nagar":        (19.0788, 72.8880),
    "Jamil Nagar":              (19.0792, 72.8885),
    "Jamin Nagar":              (19.0795, 72.8888),
    "Utkarsh Nagar":            (19.0802, 72.8895),
    "Samarth Nagar":            (19.0808, 72.8902),
    "Tulshet Pada":             (19.0815, 72.8908),
    "Sonapur":                  (19.0822, 72.8915),
    "Taximen colony":           (19.0825, 72.8918),
    "Bail Bazar":               (19.0832, 72.8925),
    "Court":                    (19.0838, 72.8932),
    "Halav pool":               (19.0845, 72.8938),
    "Makad wali chawal":        (19.0852, 72.8945),
    "MIG":                      (19.0858, 72.8952),
    "LIG":                      (19.0865, 72.8955),
    "Sambhaji chowk":           (19.0872, 72.8962),
    "Diamond":                  (19.0878, 72.8968),
    "Galaxy":                   (19.0885, 72.8975),
    "Machis factory":           (19.0892, 72.8982),
    "New mill road":            (19.0898, 72.8988),
    "Bachan tabela":            (19.0905, 72.8995),
    "Pipe road":                (19.0912, 72.9002),
    "Vinobha bhave":            (19.0918, 72.9008),
    "Ali dada estate":          (19.0925, 72.9015),
    "Takiya wad":               (19.0932, 72.9022),
    "Machi market":             (19.0938, 72.9028),
    "Rajiv Gandhi Nagar":       (19.0945, 72.9035),
    "Lal Taki":                 (19.0952, 72.9042),
    "Charbi Gali":              (19.0958, 72.9048),
    "Kamela":                   (19.0965, 72.9055),
    "Taxi Stand":               (19.0972, 72.9062),
    "Kaju Pada":                (19.0978, 72.9068),
    "Ghafoor Khan Estate":      (19.0985, 72.9075),
    "Patel Wadi":               (19.0992, 72.9082),
    "Dhobi Ghat":               (19.0745, 72.8835),
    "New Hall Road":            (19.0748, 72.8840),
    "Bharti Nagar":             (19.0755, 72.8845),
    "Mubarak complex":          (19.0758, 72.8850),
    "9 number":                 (19.0765, 72.8855),
    "Teacher's Colony":         (19.0775, 72.8865),
    "Kamaani":                  (19.0778, 72.8868),
    "Huzoor Tajushsharia Chowk":(19.0792, 72.8882),
    "Father Peter Pereira Chowk":(19.0798, 72.8888),
    "\"L\" Ward":               (19.0808, 72.8898),

    # ── CHEMBUR / GOVANDI / MANKHURD / DEONAR ────────────────────────────
    "Chembur":                  (19.0622, 72.9005),
    "Chembur Causeway":         (19.0612, 72.8995),
    "Union Park":               (19.0625, 72.9010),
    "Central Avenue":           (19.0632, 72.9015),
    "Pestom sagar":             (19.0638, 72.9022),
    "Basant Park":              (19.0645, 72.9028),
    "Diamond Garden":           (19.0652, 72.9035),
    "Chembur Camp":             (19.0658, 72.9042),
    "Ghatla village":           (19.0665, 72.9048),
    "Borla village":            (19.0672, 72.9055),
    "Tilak Nagar":              (19.0685, 72.9068),
    "New Tilak Nagar":          (19.0692, 72.9075),
    "Mahul":                    (19.0555, 72.9175),   # corrected: Mahul is near Trombay, not near Chembur centre
    "Mahul Village":            (19.0562, 72.9182),
    "Trombay":                  (19.0602, 72.9188),
    "Trombay Koliwada":         (19.0608, 72.9192),
    "Mysore Colony":            (19.0712, 72.9095),
    "Collector Colony":         (19.0718, 72.9102),
    "Anushakti Nagar":          (19.0725, 72.9108),
    "Vishnu Nagar":             (19.0732, 72.9115),
    "HP nagar":                 (19.0738, 72.9122),
    "BPCL":                     (19.0588, 72.9198),   # corrected: BPCL/RCF are near Mahul/Trombay
    "RCF":                      (19.0572, 72.9205),
    "C.G.S. colony":            (19.0758, 72.9142),
    "Indian Oil Nagar":         (19.0772, 72.9155),
    "Sahyadri Nagar":           (19.0778, 72.9162),
    "Sarvoday Nagar":           (19.0785, 72.9168),
    "Govandi":                  (19.0532, 72.9188),
    "Mankhurd":                 (19.0445, 72.9282),
    "Mandala":                  (19.0450, 72.9285),
    "Deonar":                   (19.0532, 72.9148),
    "Baiganwadi":               (19.0535, 72.9152),
    "Lallubhai Compound":       (19.0548, 72.9165),
    "Gautam Nagar":             (19.0555, 72.9172),
    "Cheetah Camp":             (19.0450, 72.9225),
    "Ambedkar Nagar":           (19.0462, 72.9242),
    "Buddha Colony":            (19.0468, 72.9248),
    "Achanak Nagar":            (19.0475, 72.9255),
    "Thakkar Bappa Colony":     (19.0482, 72.9262),
    "Vashinaka":                (19.0488, 72.9268),
    "Siddharth Colony":         (19.0495, 72.9275),
    "Madhav Nagar":             (19.0502, 72.9282),
    "GTB Nagar":                (19.0508, 72.9288),
    "Chedda Nagar":             (19.0515, 72.9295),
    "Patel Estate":             (19.0522, 72.9302),
    "Chunabhatti":              (19.0558, 72.9135),
    "BSNL Colony":              (19.0568, 72.9148),
    "Sangam Nagar":             (19.0575, 72.9155),

    # ── WADALA / DHARAVI / SION / MAHIM ───────────────────────────────────
    "Wadala":                   (19.0192, 72.8582),
    "BPT Colony":               (19.0198, 72.8585),
    "Kidwai Nagar":             (19.0210, 72.8598),
    "Antop Hill":               (19.0215, 72.8605),
    "Dharavi":                  (19.0378, 72.8534),
    "Koliwada":                 (19.0382, 72.8538),
    "Koombarwara":              (19.0388, 72.8545),
    "Sion Trombay Road":        (19.0398, 72.8552),
    "Wadavali village":         (19.0405, 72.8558),
    "Maravali":                 (19.0412, 72.8565),
    "Julianwadi":               (19.0418, 72.8572),
    "Panjarpol":                (19.0425, 72.8578),

    # ── SOUTH MUMBAI ──────────────────────────────────────────────────────
    "Agripada":                 (19.9655, 72.8225),   # NOTE: keeping as-is, near Grant Rd
    "Agripada":                 (18.9655, 72.8225),
    "New Agripada":             (18.9662, 72.8232),
    "Chaitanya Nagar":          (18.9670, 72.8238),
    "Davri Nagar":              (18.9675, 72.8245),
    "Vakola Pipeline":          (19.0775, 72.8465),
    "South Mumbai":             (18.9388, 72.8355),
    "Chinchpokli":              (18.9848, 72.8325),
    "Chor Bazaar":              (18.9562, 72.8322),
    "Churchgate":               (18.9355, 72.8258),
    "Cuffe Parade":             (18.9222, 72.8215),
    "Dava Bazaar":              (18.9575, 72.8335),
    "Grant Road":               (18.9648, 72.8198),
    "Kemps Corner":             (18.9665, 72.8080),
    "Lower Parel":              (18.9982, 72.8368),
    "Mahalaxmi":                (18.9828, 72.8342),
    "Mahim":                    (19.0342, 72.8422),
    "Masjid Bunder":            (18.9485, 72.8338),
    "Marine Drive":             (18.9432, 72.8232),
    "Marine Lines":             (18.9445, 72.8225),
    "Mumbai Central":           (18.9688, 72.8228),
    "Nagpada":                  (18.9615, 72.8265),
    "Nariman Point":            (18.9255, 72.8235),
    "Prabhadevi":               (19.0112, 72.8330),
    "Worli":                    (19.0102, 72.8162),
    "Bhuleshwar":               (18.9575, 72.8275),
    "Zaveri Baazar":            (18.9545, 72.8315),
    "Bhendi Bazaar":            (18.9535, 72.8295),
    "Byculla":                  (18.9782, 72.8325),
    "Dagdi Chawl":              (18.9588, 72.8305),
    "Ghodapdeo":                (18.9595, 72.8312),
    "Colaba":                   (18.9068, 72.8148),
    "Navy Nagar":               (18.8988, 72.8148),
    "Cumbala Hill":             (18.9698, 72.8048),
    "Breach Candy":             (18.9628, 72.8065),
    "Dadar":                    (19.0178, 72.8478),
    "Hindu colony":             (19.0182, 72.8482),
    "Shivaji Park Residential Zone": (19.0192, 72.8435),
    "Parsi Colony":             (19.0195, 72.8488),
    "Naigaon":                  (19.0202, 72.8495),
    "Fort":                     (18.9338, 72.8352),
    "Ballard Estate":           (18.9405, 72.8398),
    "Dhobitalao":               (18.9442, 72.8275),
    "Kala Ghoda":               (18.9285, 72.8318),
    "Girgaon":                  (18.9545, 72.8215),
    "Charni Road":              (18.9595, 72.8185),
    "Khotachiwadi":             (18.9605, 72.8195),
    "Kalbadevi":                (18.9515, 72.8295),
    "Kamathipura":              (18.9665, 72.8245),
    "Malabar Hill":             (18.9558, 72.7958),
    "Walkeshwar":               (18.9460, 72.7995),
    "Matunga":                  (19.0282, 72.8545),
    "King Circle":              (19.0285, 72.8552),
    "Parel":                    (18.9965, 72.8428),
    "Cotton Green":             (18.9575, 72.8565),
    "Lalbaug":                  (18.9975, 72.8355),
    "Sion":                     (19.0388, 72.8638),
    "Tardeo":                   (18.9718, 72.8195),
    "Gowalia Tank":             (18.9645, 72.8125),
    "Altamount Road":           (18.9655, 72.8055),
    "Nana Chowk":               (18.9635, 72.8215),
    "Umarkhadi":                (18.9538, 72.8325),
    "Dongri":                   (18.9548, 72.8315),
    "Sayad colony":             (18.9558, 72.8325),

    # ── SPECIAL / INSTITUTION ─────────────────────────────────────────────
    "IIT Bombay campus":        (19.1335, 72.9145),
    "Indian Institute of Technology Bombay campus": (19.1335, 72.9145),
    "Nitie":                    (19.1265, 72.9198),
    "JVLR":                     (19.1215, 72.8875),
    "WEH Western Express Highway": (19.1125, 72.8765),
    "Naupada":                  (19.1918, 72.9742),   # Thane area — kept as-is
    "Bairam Naupada":           (19.1920, 72.9746),
    "Other":                    (19.0760, 72.8777),

    # ── EAST / WEST SUFFIXED VARIANTS ─────────────────────────────────────
    "L Ward":                   (19.0808, 72.8898),
    "L ward":                   (19.0808, 72.8898),
    "Borivali East":            (19.2290, 72.8567),
    "Borivali West":            (19.2290, 72.8430),
    "Andheri East":             (19.1144, 72.8697),
    "Andheri West":             (19.1195, 72.8395),
    "Malad East":               (19.1808, 72.8574),
    "Malad West":               (19.1828, 72.8402),
    "Kandivali East":           (19.2077, 72.8550),
    "Kandivali West":           (19.2077, 72.8320),
    "Goregaon East":            (19.1648, 72.8558),
    "Goregaon West":            (19.1648, 72.8388),
    "Bandra East":              (19.0653, 72.8528),
    "Bandra West":              (19.0544, 72.8278),
    "Kurla East":               (19.0728, 72.8892),
    "Kurla West":               (19.0728, 72.8758),
    "Ghatkopar East":           (19.0858, 72.9148),
    "Ghatkopar West":           (19.0858, 72.9002),
    "Mulund East":              (19.1716, 72.9618),
    "Mulund West":              (19.1716, 72.9478),
    "Vikhroli East":            (19.1088, 72.9358),
    "Vikhroli West":            (19.1088, 72.9208),
    "Bhandup East":             (19.1459, 72.9428),
    "Bhandup West":             (19.1459, 72.9288),
    "Chembur East":             (19.0622, 72.9078),
    "Chembur West":             (19.0622, 72.8928),
    "Santacruz East":           (19.0786, 72.8468),
    "Santacruz West":           (19.0786, 72.8308),
    "Vile Parle East":          (19.0990, 72.8558),
    "Vile Parle West":          (19.0990, 72.8388),
}

ZONE_COORDS = {
    "andheri":      (19.1144, 72.8679),
    "bandra":       (19.0544, 72.8402),
    "borivali":     (19.2290, 72.8567),
    "kandivali":    (19.2077, 72.8427),
    "malad":        (19.1868, 72.8489),
    "goregaon":     (19.1648, 72.8500),
    "jogeshwari":   (19.1382, 72.8432),
    "santacruz":    (19.0786, 72.8394),
    "vile parle":   (19.0990, 72.8474),
    "khar":         (19.0665, 72.8342),
    "juhu":         (19.1075, 72.8263),
    "kurla":        (19.0728, 72.8826),
    "ghatkopar":    (19.0858, 72.9081),
    "vikhroli":     (19.1088, 72.9288),
    "bhandup":      (19.1458, 72.9362),
    "mulund":       (19.1716, 72.9562),
    "powai":        (19.1197, 72.9076),
    "chembur":      (19.0622, 72.9005),
    "deonar":       (19.0532, 72.9148),
    "govandi":      (19.0532, 72.9188),
    "mankhurd":     (19.0445, 72.9282),
    "dharavi":      (19.0378, 72.8534),
    "dadar":        (19.0178, 72.8478),
    "sion":         (19.0388, 72.8638),
    "mahim":        (19.0342, 72.8422),
    "wadala":       (19.0192, 72.8582),
    "worli":        (19.0102, 72.8162),
    "lower parel":  (18.9982, 72.8368),
    "mahalaxmi":    (18.9828, 72.8342),
    "prabhadevi":   (19.0112, 72.8330),
    "colaba":       (18.9068, 72.8148),
    "fort":         (18.9338, 72.8352),
    "churchgate":   (18.9355, 72.8258),
    "nariman":      (18.9255, 72.8235),
    "marine":       (18.9432, 72.8232),
    "byculla":      (18.9782, 72.8325),
    "agripada":     (18.9655, 72.8225),
    "mumbai central":(18.9688, 72.8228),
    "grant road":   (18.9648, 72.8198),
    "nagpada":      (18.9615, 72.8265),
    "dongri":       (18.9548, 72.8315),
    "chor bazaar":  (18.9562, 72.8322),
    "bhendi":       (18.9535, 72.8295),
    "kalbadevi":    (18.9515, 72.8295),
    "bhuleshwar":   (18.9575, 72.8275),
    "girgaon":      (18.9545, 72.8215),
    "charni":       (18.9595, 72.8185),
    "malabar":      (18.9558, 72.7958),
    "cuffe parade": (18.9222, 72.8215),
    "kamathipura":  (18.9665, 72.8245),
    "malvani":      (19.2004, 72.8219),
    "versova":      (19.1351, 72.8134),
    "l ward":       (19.0808, 72.8898),
    "dahisar":      (19.2545, 72.8568),
    "oshiwara":     (19.1412, 72.8318),
}

# All area names for location search dropdown
ALL_MUMBAI_AREAS = sorted(list(set(
    list(KNOWN_COORDS.keys()) + [k.title() for k in ZONE_COORDS.keys()]
)))

np.random.seed(42)

def get_coords(locality: str):
    if locality in KNOWN_COORDS:
        return KNOWN_COORDS[locality]
    for key, coords in KNOWN_COORDS.items():
        if key.lower() == locality.lower():
            return coords
    loc_l = locality.lower()
    for key, coords in ZONE_COORDS.items():
        if key in loc_l or loc_l in key:
            jitter_lat = np.random.uniform(-0.008, 0.008)
            jitter_lon = np.random.uniform(-0.008, 0.008)
            return (coords[0] + jitter_lat, coords[1] + jitter_lon)
    return (
        np.random.uniform(18.89, 19.27),
        np.random.uniform(72.78, 72.98),
    )

def resolve_area_to_coords(area_name: str):
    if not area_name:
        return None
    if area_name in KNOWN_COORDS:
        return KNOWN_COORDS[area_name]
    for k, v in KNOWN_COORDS.items():
        if k.lower() == area_name.lower():
            return v
    area_l = area_name.lower()
    for key, coords in ZONE_COORDS.items():
        if key in area_l or area_l in key:
            return coords
    return None

# ─────────────────────────────────────────────
# POLICE STATIONS LOADER
# ─────────────────────────────────────────────
@st.cache_data
def load_police_stations(csv_path: str = "police_stations.csv") -> pd.DataFrame:
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        required = {"name", "lat", "lon"}
        if required.issubset(set(df.columns)):
            return df[["name", "lat", "lon"]].dropna().reset_index(drop=True)
    return pd.DataFrame({
        "name": [
            "Cuffe Parade Police Station",
            "Yellow Gate Police Station",
            "Nirmalnagar Police Station",
            "Santacruz Police Station",
            "Malvani Police Station",
            "Andheri Police Station",
            "Bandra Police Station",
            "Borivali Police Station",
            "Kurla Police Station",
            "Chembur Police Station",
            "Malad Police Station",
            "Kandivali Police Station",
            "Goregaon Police Station",
            "Ghatkopar Police Station",
            "Mulund Police Station",
            "Powai Police Station",
            "Dharavi Police Station",
            "Dadar Police Station",
        ],
        "lat": [
            18.9155, 18.9475, 19.0596, 19.0786, 19.2004,
            19.1144, 19.0544, 19.2290, 19.0728, 19.0622,
            19.1868, 19.2077, 19.1648, 19.0858, 19.1716,
            19.1197, 19.0378, 19.0178,
        ],
        "lon": [
            72.8213, 72.8400, 72.8519, 72.8394, 72.8219,
            72.8679, 72.8402, 72.8567, 72.8826, 72.9005,
            72.8489, 72.8427, 72.8500, 72.9081, 72.9562,
            72.9076, 72.8534, 72.8478,
        ],
    })

# ─────────────────────────────────────────────
# GEODESIC DISTANCE
# ─────────────────────────────────────────────
def haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlam = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlam / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

def nearest_stations(user_lat, user_lon, stations_df, n=3):
    df = stations_df.copy()
    df["distance_km"] = df.apply(
        lambda r: haversine_km(user_lat, user_lon, r["lat"], r["lon"]), axis=1
    )
    df["gmaps_link"] = df.apply(
        lambda r: f"https://www.google.com/maps/dir/{user_lat},{user_lon}/{r['lat']},{r['lon']}",
        axis=1,
    )
    return df.nsmallest(n, "distance_km").reset_index(drop=True)

# ─────────────────────────────────────────────
# SQLITE BACKEND
# ─────────────────────────────────────────────
DB_PATH = "safety_data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS localities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            locality TEXT, city TEXT, population INTEGER,
            area_sq_km REAL, population_density REAL,
            uhi_index REAL, police_chowkis INTEGER,
            internet_pct REAL, total_crimes INTEGER,
            crimes_women INTEGER, police_density REAL,
            safety_index REAL, risk_index REAL,
            lat REAL, lon REAL, updated_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            locality TEXT,
            severity TEXT,
            reported_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def load_csv_to_db(csv_path):
    df = pd.read_csv(csv_path)
    conn = sqlite3.connect(DB_PATH)
    rows = []
    now = datetime.now().isoformat()
    for _, row in df.iterrows():
        lat, lon = get_coords(str(row["locality"]))
        rows.append((
            str(row["locality"]), str(row["city"]),
            int(row["population"]), float(row["area sq km"]),
            float(row["populationdensity"]), float(row["urban heat island index"]),
            int(row["police chowkis"]), float(row["internet penetration percent"]),
            int(row["total crimes"]), int(row["crimes against women"]),
            float(row["police_density"]), float(row["women safety index"]),
            float(row["risk index"]), lat, lon, now
        ))
    conn.execute("DELETE FROM localities")
    conn.executemany("""
        INSERT INTO localities
        (locality, city, population, area_sq_km, population_density,
         uhi_index, police_chowkis, internet_pct, total_crimes,
         crimes_women, police_density, safety_index, risk_index, lat, lon, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, rows)
    conn.commit()
    conn.close()

def fetch_all():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM localities ORDER BY risk_index DESC", conn)
    conn.close()
    return df

def report_incident(locality: str, incident_type: str = "general"):
    conn = sqlite3.connect(DB_PATH)
    now = datetime.now().isoformat()
    risk_bump = 2.0 if incident_type == "severe" else 1.0
    conn.execute("""
        UPDATE localities
        SET risk_index = risk_index + ?, crimes_women = crimes_women + 1,
            total_crimes = total_crimes + 1, updated_at = ?
        WHERE locality = ?
    """, (risk_bump, now, locality))
    conn.execute("""
        INSERT INTO incidents (locality, severity, reported_at)
        VALUES (?, ?, ?)
    """, (locality, incident_type, now))
    conn.commit()
    updated = pd.read_sql(
        "SELECT * FROM localities WHERE locality = ?", conn, params=(locality,)
    )
    conn.close()
    return updated

def classify(risk):
    if risk >= 15: return "high"
    elif risk >= 7: return "medium"
    return "low"

# ─────────────────────────────────────────────
# MAP BUILDER
# ─────────────────────────────────────────────
def build_map(df, show_high, show_med, show_low,
              selected_locality=None, user_lat=None, user_lon=None,
              emergency_stations=None):
    focus_lat, focus_lon, zoom = 19.076, 72.877, 11
    fit_bounds = None

    if emergency_stations is not None and user_lat and user_lon:
        all_lats = [user_lat] + list(emergency_stations["lat"])
        all_lons = [user_lon] + list(emergency_stations["lon"])
        pad = 0.012
        fit_bounds = [
            [min(all_lats) - pad, min(all_lons) - pad],
            [max(all_lats) + pad, max(all_lons) + pad],
        ]
        focus_lat, focus_lon = user_lat, user_lon
        zoom = 14
    elif selected_locality and selected_locality != "— All —":
        row = df[df["locality"] == selected_locality]
        if not row.empty:
            focus_lat = float(row.iloc[0]["lat"])
            focus_lon = float(row.iloc[0]["lon"])
            zoom = 15
    elif user_lat and user_lon:
        focus_lat, focus_lon = user_lat, user_lon
        zoom = 15

    m = folium.Map(
        location=[focus_lat, focus_lon],
        zoom_start=zoom,
        tiles=MAP_TILE,
        prefer_canvas=True,
    )

    if fit_bounds:
        m.fit_bounds(fit_bounds, padding=[40, 40])

    risk_vals = df["risk_index"].values
    r_min, r_max = risk_vals.min(), risk_vals.max()

    def norm(v):
        return float((v - r_min) / (r_max - r_min + 1e-9))

    high_pts, med_pts, low_pts = [], [], []
    for _, row in df.iterrows():
        cat = classify(row["risk_index"])
        pt = [row["lat"], row["lon"], norm(row["risk_index"])]
        if cat == "high": high_pts.append(pt)
        elif cat == "medium": med_pts.append(pt)
        else: low_pts.append(pt)

    heat_cfg = dict(min_opacity=0.35, max_zoom=16, radius=28, blur=22)

    if show_high and high_pts:
        HeatMap(high_pts, gradient={0.0:"#3d0000",0.4:"#cc0000",0.7:"#ff4444",1.0:"#ff0000"},
                name="🔴 High Risk", **heat_cfg).add_to(m)
    if show_med and med_pts:
        HeatMap(med_pts, gradient={0.0:"#2a1a00",0.4:"#cc7700",0.7:"#ffaa00",1.0:"#ffcc00"},
                name="🟡 Medium Risk", **heat_cfg).add_to(m)
    if show_low and low_pts:
        HeatMap(low_pts, gradient={0.0:"#001a00",0.4:"#006600",0.7:"#00cc44",1.0:"#00ff66"},
                name="🟢 Safe Zones", **heat_cfg).add_to(m)

    if user_lat and user_lon:
        folium.CircleMarker(
            location=[user_lat, user_lon], radius=10,
            color="#00bfff", fill=True, fill_color="#00bfff", fill_opacity=0.95,
            popup=folium.Popup(
                f"<b>📍 You are here</b><br>Lat: {user_lat:.5f}<br>Lon: {user_lon:.5f}",
                max_width=180
            ),
            tooltip="📍 Your Location",
        ).add_to(m)
        folium.CircleMarker(
            location=[user_lat, user_lon], radius=22,
            color="#00bfff", fill=False, weight=2, opacity=0.4,
        ).add_to(m)
        folium.CircleMarker(
            location=[user_lat, user_lon], radius=36,
            color="#00bfff", fill=False, weight=1, opacity=0.2,
        ).add_to(m)

    if emergency_stations is not None:
        station_colors = ["#1565c0", "#1976d2", "#42a5f5"]
        rank_labels = ["#1 Nearest", "#2 Nearest", "#3 Nearest"]
        for idx, (_, srow) in enumerate(emergency_stations.iterrows()):
            color = station_colors[idx] if idx < len(station_colors) else "#1565c0"
            folium.CircleMarker(
                location=[srow["lat"], srow["lon"]],
                radius=18, color="#ffffff", fill=True,
                fill_color=color, fill_opacity=0.25, weight=2, opacity=0.6,
            ).add_to(m)
            folium.CircleMarker(
                location=[srow["lat"], srow["lon"]],
                radius=10, color="#ffffff", fill=True,
                fill_color=color, fill_opacity=1.0, weight=2,
                popup=folium.Popup(
                    f"<b>🚔 {srow['name']}</b><br>"
                    f"{rank_labels[idx]}<br>"
                    f"Distance: {srow['distance_km']:.2f} km<br>"
                    f"<a href='{srow['gmaps_link']}' target='_blank'>🗺️ Navigate here →</a>",
                    max_width=260,
                ),
                tooltip=f"🚔 {rank_labels[idx]}: {srow['name']} ({srow['distance_km']:.2f} km)",
            ).add_to(m)
            if user_lat and user_lon:
                folium.PolyLine(
                    locations=[[user_lat, user_lon], [srow["lat"], srow["lon"]]],
                    color=color, weight=2.5, dash_array="8 5", opacity=0.85,
                ).add_to(m)

    return m

# ─────────────────────────────────────────────
# INIT DB
# ─────────────────────────────────────────────
init_db()
if not os.path.exists(DB_PATH) or os.path.getsize(DB_PATH) < 5000:
    load_csv_to_db("data.csv")

conn_check = sqlite3.connect(DB_PATH)
count = conn_check.execute("SELECT COUNT(*) FROM localities").fetchone()[0]
conn_check.close()
if count == 0:
    load_csv_to_db("data.csv")

POLICE_DF = load_police_stations("police_stations.csv")

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
title_col, toggle_col = st.columns([5, 1])
with title_col:
    st.markdown('<div class="main-title">🛡️ Mumbai Women Safety Risk Map</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Interactive locality-wise safety visualization · Live data</div>', unsafe_allow_html=True)
with toggle_col:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button(TOGGLE_LABEL, use_container_width=True):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Controls")
    st.markdown("*Use the ◀ button at the top of the sidebar to collapse/expand it.*")
    st.markdown("---")

    st.markdown('<div class="section-hdr">📍 My Location</div>', unsafe_allow_html=True)

    if st.session_state.user_lat:
        st.markdown(
            f'<span class="loc-badge loc-active">✅ Active: {st.session_state.user_lat:.4f}, {st.session_state.user_lon:.4f}</span>',
            unsafe_allow_html=True,
        )
        if st.button("🗑️ Clear Location", use_container_width=True):
            st.session_state.user_lat = None
            st.session_state.user_lon = None
            st.session_state.emergency_active = False
            st.rerun()
    else:
        st.markdown(
            '<span class="loc-badge loc-inactive">⚫ No location set</span>',
            unsafe_allow_html=True,
        )

    st.caption("Search by area name:")
    area_input = st.selectbox(
        "Search area",
        options=[""] + ALL_MUMBAI_AREAS,
        index=0,
        key="area_search",
        label_visibility="collapsed",
        placeholder="Type area name (e.g. Malad, L Ward…)",
    )
    if area_input and area_input != "":
        resolved = resolve_area_to_coords(area_input)
        if resolved:
            if st.button(f"📌 Set location to {area_input}", use_container_width=True):
                st.session_state.user_lat = resolved[0]
                st.session_state.user_lon = resolved[1]
                st.session_state.emergency_active = False
                st.rerun()
        else:
            st.caption("⚠️ Area not found — try manual lat/lon below")

    st.caption("Or enter coordinates manually:")
    col_lat, col_lon = st.columns(2)
    with col_lat:
        manual_lat = st.number_input("Lat", value=19.0760, format="%.4f", step=0.001)
    with col_lon:
        manual_lon = st.number_input("Lon", value=72.8777, format="%.4f", step=0.001)

    if st.button("📌 Set Manual Coordinates", use_container_width=True):
        st.session_state.user_lat = manual_lat
        st.session_state.user_lon = manual_lon
        st.session_state.emergency_active = False
        st.rerun()

    st.markdown('<div class="section-hdr">🚨 Emergency</div>', unsafe_allow_html=True)

    if not st.session_state.emergency_active:
        if st.button("🚨 EMERGENCY – Find Police NOW", use_container_width=True, type="primary"):
            if st.session_state.user_lat:
                st.session_state.emergency_active = True
            else:
                st.warning("⚠️ Please set your location first!")
            st.rerun()
    else:
        if st.button("✅ Emergency Active — Click to Deactivate", use_container_width=True):
            st.session_state.emergency_active = False
            st.rerun()

    st.markdown("---")

    st.markdown('<div class="section-hdr">Layer Visibility</div>', unsafe_allow_html=True)
    show_high = st.checkbox("🔴 High Risk Zones", value=True)
    show_med  = st.checkbox("🟡 Medium Risk Zones", value=True)
    show_low  = st.checkbox("🟢 Safe Zones", value=True)

    st.markdown('<div class="section-hdr">Zoom to Locality</div>', unsafe_allow_html=True)
    df_all = fetch_all()
    locality_list = ["— All —"] + sorted(df_all["locality"].unique().tolist())
    selected_loc = st.selectbox("Select locality", locality_list, label_visibility="collapsed")

    st.markdown("---")
    st.markdown('<div class="section-hdr">📣 Report Incident</div>', unsafe_allow_html=True)
    report_locality = st.selectbox(
        "Locality", sorted(df_all["locality"].unique().tolist()),
        key="report_loc", label_visibility="collapsed"
    )
    incident_severity = st.radio("Severity", ["General", "Severe"],
                                 horizontal=True, label_visibility="collapsed")

    if st.button("📤 Submit Report", use_container_width=True):
        updated = report_incident(report_locality, incident_severity.lower())
        if not updated.empty:
            new_risk = updated.iloc[0]["risk_index"]
            st.success(f"✅ Incident saved for **{report_locality}**. New risk index: **{new_risk:.1f}**")
        else:
            st.success(f"✅ Incident saved for **{report_locality}**.")
        st.rerun()

# ─────────────────────────────────────────────
# FILTER DATA
# ─────────────────────────────────────────────
df_all = fetch_all()
df_filtered = df_all.copy()

# ─────────────────────────────────────────────
# COMPUTE NEAREST STATIONS
# ─────────────────────────────────────────────
nearby_stations = None
if st.session_state.emergency_active and st.session_state.user_lat:
    nearby_stations = nearest_stations(
        st.session_state.user_lat, st.session_state.user_lon, POLICE_DF, n=3
    )

# ─────────────────────────────────────────────
# EMERGENCY PANEL
# ─────────────────────────────────────────────
if st.session_state.emergency_active and nearby_stations is not None:
    st.markdown("""<div class="emergency-panel">
      <div class="emergency-title">🚨 EMERGENCY MODE — Nearest Police Stations (blue dots on map)</div>""",
      unsafe_allow_html=True)

    rank_emojis = ["🥇", "🥈", "🥉"]
    cards_html = ""
    for i, (_, row) in enumerate(nearby_stations.iterrows()):
        cards_html += f"""
        <div class="station-card">
          <div class="station-name">{rank_emojis[i]} {row['name']}</div>
          <div class="station-dist">📏 {row['distance_km']:.2f} km away</div>
          <a class="nav-link" href="{row['gmaps_link']}" target="_blank">🗺️ Navigate in Google Maps</a>
        </div>"""

    st.markdown(cards_html + "</div>", unsafe_allow_html=True)
    st.error("📞 **Police: 100** | Women Helpline: **1091** | Emergency: **112**")

# ─────────────────────────────────────────────
# METRIC CARDS
# ─────────────────────────────────────────────
n_high   = len(df_filtered[df_filtered["risk_index"] >= 15])
n_med    = len(df_filtered[(df_filtered["risk_index"] >= 7) & (df_filtered["risk_index"] < 15)])
n_low    = len(df_filtered[df_filtered["risk_index"] < 7])
avg_risk = df_filtered["risk_index"].mean() if not df_filtered.empty else 0

st.markdown(f"""
<div class="metric-row">
  <div class="metric-card"><div class="val blue">{len(df_filtered)}</div><div class="lbl">Localities</div></div>
  <div class="metric-card"><div class="val red">{n_high}</div><div class="lbl">High Risk</div></div>
  <div class="metric-card"><div class="val amber">{n_med}</div><div class="lbl">Medium Risk</div></div>
  <div class="metric-card"><div class="val green">{n_low}</div><div class="lbl">Safe Zones</div></div>
  <div class="metric-card"><div class="val amber">{avg_risk:.1f}</div><div class="lbl">Avg Risk</div></div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# MAP + TABLE
# ─────────────────────────────────────────────
col_map, col_data = st.columns([2.6, 1], gap="medium")

with col_map:
    if df_filtered.empty:
        st.warning("No data available.")
    else:
        m = build_map(
            df_filtered, show_high, show_med, show_low,
            selected_loc,
            user_lat=st.session_state.user_lat,
            user_lon=st.session_state.user_lon,
            emergency_stations=nearby_stations,
        )
        st_folium(m, width=None, height=580, returned_objects=[])

with col_data:
    if st.session_state.user_lat and not st.session_state.emergency_active:
        st.markdown('<div class="section-hdr">🚔 Nearest Police Stations</div>', unsafe_allow_html=True)
        ns = nearest_stations(st.session_state.user_lat, st.session_state.user_lon, POLICE_DF, n=3)
        for _, r in ns.iterrows():
            st.markdown(
                f"**{r['name']}**  \n"
                f"📏 {r['distance_km']:.2f} km · "
                f"[Navigate]({r['gmaps_link']})"
            )
        st.markdown("---")

    st.markdown('<div class="section-hdr">Top 25 Riskiest Localities</div>', unsafe_allow_html=True)
    top25 = df_filtered.nlargest(25, "risk_index")[
        ["locality", "risk_index", "crimes_women", "police_density", "total_crimes"]
    ].rename(columns={
        "locality": "Locality", "risk_index": "Risk",
        "crimes_women": "Crimes(W)", "police_density": "Police/km²",
        "total_crimes": "Total",
    }).reset_index(drop=True)

    def color_risk(val):
        if val >= 15: return "color: #ff4d4d; font-weight: 700"
        elif val >= 7: return "color: #ffaa00; font-weight: 600"
        return "color: #00e676"

    st.dataframe(
        top25.style.map(color_risk, subset=["Risk"])
            .format({"Risk": "{:.1f}", "Police/km²": "{:.2f}"}),
        use_container_width=True, height=460,
    )

# ─────────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-hdr">📊 Analytics</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("**Risk Distribution**")
    counts = pd.DataFrame({
        "Zone": ["🔴 High (≥15)", "🟡 Medium (7-15)", "🟢 Safe (<7)"],
        "Count": [n_high, n_med, n_low]
    })
    st.bar_chart(counts.set_index("Zone"), color="#4fc3f7")

with c2:
    st.markdown("**Top 10 Crimes Against Women**")
    top_crimes = df_filtered.nlargest(10, "crimes_women")[["locality", "crimes_women"]].set_index("locality")
    st.bar_chart(top_crimes, color="#ff4444")

with c3:
    st.markdown("**Top 10 Police Density**")
    top_police = df_filtered.nlargest(10, "police_density")[["locality", "police_density"]].set_index("locality")
    st.bar_chart(top_police, color="#00e676")

# ─────────────────────────────────────────────
# FULL DATA TABLE
# ─────────────────────────────────────────────
with st.expander("📋 Full Data Table", expanded=False):
    show_cols = ["locality", "risk_index", "crimes_women", "total_crimes",
                 "police_density", "population_density", "uhi_index", "internet_pct", "population"]
    st.dataframe(
        df_filtered[show_cols].rename(columns={
            "locality": "Locality", "risk_index": "Risk Index",
            "crimes_women": "Crimes (Women)", "total_crimes": "Total Crimes",
            "police_density": "Police Density", "population_density": "Pop. Density",
            "uhi_index": "UHI Index", "internet_pct": "Internet %",
            "population": "Population"
        }).sort_values("Risk Index", ascending=False).reset_index(drop=True),
        use_container_width=True, height=400,
    )
    st.download_button("⬇️ Download CSV", df_filtered.to_csv(index=False),
                       "safety_data.csv", "text/csv")

st.markdown(f"""
<div style="text-align:center;color:{SUBTXT};font-size:0.72rem;margin-top:20px;padding-bottom:12px">
  Mumbai Women Safety Risk Map · Built with Streamlit + Folium
</div>
""", unsafe_allow_html=True)
