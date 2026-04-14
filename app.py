"""
app.py — QuizAgent CI  |  Design Premium
"""
import streamlit as st
import pandas as pd
import json, time, io, re, requests, hashlib
from datetime import datetime

import config
from database import (
    init_db, search_agents, get_all_agents, upsert_agents,
    set_agent_published, publish_all_agents, unpublish_all_agents,
    delete_agent, add_agent_manual, get_agent_by_id, get_session_by_id,
    get_quiz_by_code, get_all_quizzes, get_quiz, create_quiz, update_quiz, delete_quiz,
    get_questions, add_question, delete_question, reorder_questions,
    create_session, save_quiz_progress,
    submit_session, get_results, session_already_completed, get_stats,
)

st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon="📝",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════════════════
#  DESIGN SYSTEM — CSS agressif qui écrase Streamlit
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
/* ── Variables ── */
:root {
  --blue: #2563EB; --blue-d: #1D4ED8; --blue-x: #1E3A8A;
  --blue-l: #EFF6FF; --blue-m: #BFDBFE;
  --green: #059669; --green-l: #D1FAE5;
  --orange: #D97706; --orange-l: #FEF3C7;
  --red: #DC2626; --red-l: #FEE2E2;
  --purple: #7C3AED; --purple-l: #EDE9FE;
  --bg: #F0F4FF; --surface: #FFFFFF;
  --border: #E2E8F4; --border2: #CBD5E1;
  --text: #0F172A; --text2: #475569; --text3: #94A3B8;
  --shadow: 0 1px 3px rgba(0,0,0,.08), 0 4px 16px rgba(0,0,0,.05);
  --shadow-md: 0 4px 20px rgba(0,0,0,.1), 0 1px 6px rgba(0,0,0,.06);
  --shadow-blue: 0 8px 32px rgba(37,99,235,.25);
  --radius: 14px; --radius-sm: 10px;
}

/* ── Reset & Font ── */
*, *::before, *::after { box-sizing: border-box; }
html, body { font-family: 'Inter', -apple-system, sans-serif !important; background: var(--bg) !important; }
[class*="css"], p, span, div, label, input, textarea, button, select,
h1, h2, h3, h4, h5, h6, .stMarkdown p, .stMarkdown li {
  font-family: 'Inter', -apple-system, sans-serif !important;
}

/* ── Masquer chrome Streamlit ── */
#MainMenu, footer, header, .stDeployButton,
[data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], .stAppDeployButton { display: none !important; }

/* ── Layout ── */
.stApp { background: var(--bg) !important; }
.main .block-container {
  max-width: 600px !important;
  margin: 0 auto !important;
  padding: 0 0 80px 0 !important;
  background: transparent !important;
}
section[data-testid="stSidebar"] { display: none !important; }

/* ── Tous les boutons ── */
.stButton { margin: 4px 0 !important; }
.stButton > button {
  font-family: 'Inter', sans-serif !important;
  font-size: 15px !important;
  font-weight: 700 !important;
  letter-spacing: -0.01em !important;
  width: 100% !important;
  min-height: 52px !important;
  border-radius: var(--radius-sm) !important;
  padding: 14px 20px !important;
  cursor: pointer !important;
  transition: all 0.18s ease !important;
  border: none !important;
  outline: none !important;
}
/* Bouton primaire */
.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {
  background: linear-gradient(135deg, var(--blue) 0%, var(--blue-d) 100%) !important;
  color: #ffffff !important;
  box-shadow: 0 4px 15px rgba(37,99,235,.4) !important;
  border: none !important;
}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="baseButton-primary"]:hover {
  background: linear-gradient(135deg, var(--blue-d) 0%, var(--blue-x) 100%) !important;
  box-shadow: 0 6px 22px rgba(37,99,235,.5) !important;
  transform: translateY(-1px) !important;
}
.stButton > button[kind="primary"]:active { transform: translateY(0) !important; }
/* Bouton secondaire */
.stButton > button:not([kind="primary"]),
.stButton > button[data-testid="baseButton-secondary"] {
  background: var(--surface) !important;
  color: var(--text) !important;
  border: 2px solid var(--border) !important;
  box-shadow: var(--shadow) !important;
}
.stButton > button:not([kind="primary"]):hover {
  border-color: var(--blue) !important;
  color: var(--blue) !important;
  background: var(--blue-l) !important;
}

/* ── Inputs ── */
div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea,
.stTextInput input, .stTextArea textarea {
  font-family: 'Inter', sans-serif !important;
  font-size: 16px !important;
  font-weight: 500 !important;
  border-radius: var(--radius-sm) !important;
  border: 2px solid var(--border) !important;
  padding: 13px 16px !important;
  background: var(--surface) !important;
  color: var(--text) !important;
  box-shadow: var(--shadow) !important;
  transition: border-color 0.15s, box-shadow 0.15s !important;
}
div[data-baseweb="input"] input:focus,
div[data-baseweb="textarea"] textarea:focus,
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: var(--blue) !important;
  box-shadow: 0 0 0 4px rgba(37,99,235,.12) !important;
  outline: none !important;
}
div[data-testid="stNumberInput"] input {
  font-family: 'Inter', sans-serif !important;
  font-size: 16px !important;
  border: 2px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  padding: 12px 14px !important;
}
.stTextInput label, .stTextArea label, .stSelectbox label,
.stNumberInput label, div[data-testid="stWidgetLabel"] p {
  font-family: 'Inter', sans-serif !important;
  font-size: 11px !important;
  font-weight: 800 !important;
  color: var(--text3) !important;
  text-transform: uppercase !important;
  letter-spacing: 0.1em !important;
}

/* ── Selectbox ── */
div[data-baseweb="select"] > div {
  border-radius: var(--radius-sm) !important;
  border: 2px solid var(--border) !important;
  background: var(--surface) !important;
  font-size: 15px !important;
  font-family: 'Inter', sans-serif !important;
}

/* ── Radio ── */
div[data-testid="stRadio"] > div {
  gap: 8px !important;
  display: flex !important;
  flex-direction: column !important;
}
div[data-testid="stRadio"] label {
  background: var(--surface) !important;
  border: 2px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  padding: 13px 16px !important;
  font-size: 15px !important;
  font-weight: 500 !important;
  min-height: 50px !important;
  cursor: pointer !important;
  transition: all 0.15s !important;
  display: flex !important;
  align-items: center !important;
  color: var(--text) !important;
  margin: 0 !important;
}
div[data-testid="stRadio"] label:hover {
  border-color: var(--blue) !important;
  background: var(--blue-l) !important;
  color: var(--blue-d) !important;
}

/* ── Checkbox ── */
div[data-testid="stCheckbox"] label {
  background: var(--surface) !important;
  border: 2px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  padding: 13px 16px !important;
  font-size: 15px !important;
  font-weight: 500 !important;
  min-height: 50px !important;
  margin-bottom: 6px !important;
  display: flex !important;
  align-items: center !important;
  cursor: pointer !important;
  transition: all 0.15s !important;
}
div[data-testid="stCheckbox"] label:hover {
  border-color: var(--blue) !important;
  background: var(--blue-l) !important;
}

/* ── Tabs ── */
div[data-baseweb="tab-list"] {
  background: transparent !important;
  border-bottom: 2px solid var(--border) !important;
  gap: 4px !important;
  padding: 0 16px !important;
}
button[data-baseweb="tab"] {
  font-family: 'Inter', sans-serif !important;
  font-size: 13px !important;
  font-weight: 700 !important;
  letter-spacing: -0.01em !important;
  padding: 10px 16px !important;
  border-radius: 8px 8px 0 0 !important;
  color: var(--text2) !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
  color: var(--blue) !important;
  background: var(--blue-l) !important;
}

/* ── Expander ── */
div[data-testid="stExpander"] {
  background: var(--surface) !important;
  border: 2px solid var(--border) !important;
  border-radius: var(--radius) !important;
  margin: 6px 0 !important;
  overflow: hidden !important;
  box-shadow: var(--shadow) !important;
}
div[data-testid="stExpander"]:hover { border-color: var(--blue-m) !important; }
div[data-testid="stExpander"] details summary {
  font-family: 'Inter', sans-serif !important;
  font-size: 14px !important;
  font-weight: 700 !important;
  padding: 14px 18px !important;
  color: var(--text) !important;
}
div[data-testid="stExpander"] > div:last-child { padding: 0 16px 14px !important; }

/* ── Form ── */
div[data-testid="stForm"] { border: none !important; padding: 0 !important; background: transparent !important; }
div[data-testid="stFormSubmitButton"] button {
  background: linear-gradient(135deg, var(--blue), var(--blue-d)) !important;
  color: white !important;
  border: none !important;
  box-shadow: 0 4px 15px rgba(37,99,235,.35) !important;
}

/* ── Alertes ── */
div[data-testid="stAlert"] {
  border-radius: var(--radius-sm) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 14px !important;
  margin: 6px 0 !important;
}

/* ── Dataframe ── */
div[data-testid="stDataFrame"] { border-radius: var(--radius) !important; overflow: hidden !important; }

/* ── Download button ── */
div[data-testid="stDownloadButton"] button {
  background: linear-gradient(135deg, var(--green), #047857) !important;
  color: white !important;
  border: none !important;
  box-shadow: 0 4px 14px rgba(5,150,105,.3) !important;
}

/* ── HR ── */
hr { border: none !important; border-top: 2px solid var(--border) !important; margin: 20px 0 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--blue-m); border-radius: 99px; }

/* ══════════════════════════════════════════════════
   COMPOSANTS HTML CUSTOM
══════════════════════════════════════════════════ */

/* ── Top nav ── */
.app-header {
  background: linear-gradient(135deg, var(--blue-x) 0%, var(--blue-d) 100%);
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 0;
  box-shadow: 0 2px 20px rgba(30,58,138,.2);
}
.app-header-icon { font-size: 1.4rem; }
.app-header-title { color: #fff; font-size: 1rem; font-weight: 800; letter-spacing: -0.02em; }
.app-header-sub { color: rgba(255,255,255,.5); font-size: .78rem; margin-left: auto; }

/* ── Hero ── */
.hero-wrap {
  background: linear-gradient(145deg, var(--blue-x) 0%, var(--blue-d) 45%, #3B82F6 100%);
  margin: 0;
  padding: 52px 28px 48px;
  text-align: center;
  position: relative;
  overflow: hidden;
}
.hero-wrap::before {
  content: '';
  position: absolute; top: -80px; right: -80px;
  width: 300px; height: 300px; border-radius: 50%;
  background: rgba(255,255,255,.05);
  pointer-events: none;
}
.hero-wrap::after {
  content: '';
  position: absolute; bottom: -100px; left: -60px;
  width: 280px; height: 280px; border-radius: 50%;
  background: rgba(255,255,255,.04);
  pointer-events: none;
}
.hero-badge {
  display: inline-block;
  background: rgba(255,255,255,.15);
  color: rgba(255,255,255,.9);
  font-size: .75rem; font-weight: 700;
  padding: 5px 14px; border-radius: 99px;
  margin-bottom: 16px;
  letter-spacing: .06em; text-transform: uppercase;
  position: relative; z-index: 1;
}
.hero-icon { font-size: 3.4rem; margin-bottom: 12px; position: relative; z-index: 1; }
.hero-title {
  color: #fff; font-size: 2.2rem; font-weight: 900;
  margin: 0 0 8px; letter-spacing: -.05em; line-height: 1.1;
  position: relative; z-index: 1;
}
.hero-sub { color: rgba(255,255,255,.72); font-size: 1rem; margin: 0; position: relative; z-index: 1; }
.hero-org { color: rgba(255,255,255,.45); font-size: .85rem; margin-top: 6px; position: relative; z-index: 1; }
.hero-btns { padding: 0 20px; margin-top: -1px; background: var(--bg); padding-top: 20px; }

/* ── Section label ── */
.section-label {
  font-size: 11px; font-weight: 800; color: var(--text3);
  text-transform: uppercase; letter-spacing: .1em;
  padding: 0 20px; margin: 24px 0 10px; display: block;
}

/* ── Cards ── */
.ui-card {
  background: var(--surface);
  border: 1.5px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  margin: 0 16px 12px;
  box-shadow: var(--shadow);
}

/* ── Agent button ── */
.agent-btn-wrap { padding: 0 16px; margin-bottom: 6px; }

/* ── Agent info card ── */
.agent-info {
  display: flex; align-items: center; gap: 14px;
  background: var(--surface);
  border: 1.5px solid var(--border);
  border-radius: var(--radius);
  padding: 16px 20px;
  margin: 0 16px 16px;
  box-shadow: var(--shadow);
}
.agent-avatar {
  width: 46px; height: 46px; border-radius: 50%; flex-shrink: 0;
  background: linear-gradient(135deg, #BFDBFE, var(--blue-l));
  color: var(--blue-d); font-weight: 800; font-size: 15px;
  display: flex; align-items: center; justify-content: center;
}
.agent-name { font-size: 1.05rem; font-weight: 800; color: var(--text); }
.agent-mat { font-size: .82rem; color: var(--text3); margin-top: 2px; }

/* ── TIMER FIXE ── */
#qtbar {
  position: fixed !important; top: 0 !important;
  left: 0 !important; right: 0 !important;
  z-index: 999999 !important;
  background: rgba(240,244,255,.96) !important;
  backdrop-filter: blur(20px) !important;
  -webkit-backdrop-filter: blur(20px) !important;
  border-bottom: 1px solid var(--border) !important;
  box-shadow: 0 2px 20px rgba(0,0,0,.07) !important;
  padding: 8px 16px 7px !important;
}
#qtbar .qti { max-width: 600px; margin: 0 auto; }
.qtbox {
  border-radius: var(--radius-sm);
  padding: 12px 20px;
  display: flex; align-items: center; gap: 16px;
}
.qt-n { background: linear-gradient(135deg, var(--blue-x), var(--blue)); box-shadow: 0 4px 16px rgba(37,99,235,.3); }
.qt-w { background: linear-gradient(135deg, #92400E, var(--orange)); box-shadow: 0 4px 16px rgba(217,119,6,.3); }
.qt-d { background: linear-gradient(135deg, #7F1D1D, var(--red)); box-shadow: 0 4px 16px rgba(220,38,38,.35); animation: hb .65s infinite; }
@keyframes hb { 0%,100%{opacity:1} 50%{opacity:.82} }
.qt-ico { font-size: 1.8rem; }
.qt-time { color: #fff; font-size: 2.2rem; font-weight: 900; letter-spacing: 5px; margin: 0; line-height: 1; font-variant-numeric: tabular-nums; }
.qt-lbl { color: rgba(255,255,255,.72); font-size: .7rem; font-weight: 700; margin: 4px 0 0; text-transform: uppercase; letter-spacing: .1em; }

/* ── Progress ── */
.prog-wrap { padding: 0 16px; margin: 10px 0 16px; }
.prog-top { display: flex; justify-content: space-between; font-size: .82rem; color: var(--text2); font-weight: 600; margin-bottom: 8px; }
.prog-bg { background: #DBEAFE; border-radius: 99px; height: 7px; overflow: hidden; }
.prog-fill { background: linear-gradient(90deg, var(--blue), #60A5FA); height: 7px; border-radius: 99px; transition: width .4s ease; }

/* ── Question card ── */
.qcard {
  background: var(--surface);
  border-left: 5px solid var(--blue);
  border-top: 1.5px solid var(--border);
  border-right: 1.5px solid var(--border);
  border-bottom: 1.5px solid var(--border);
  border-radius: 0 var(--radius) var(--radius) 0;
  padding: 16px 18px 10px;
  margin: 14px 16px 0;
  box-shadow: var(--shadow);
}
.qmeta { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }
.qbadge-num { background: var(--blue); color: #fff; font-size: .7rem; font-weight: 900; padding: 3px 10px; border-radius: 99px; }
.qbadge-type { color: var(--text3); font-size: .75rem; font-weight: 600; }
.qbadge-pts { background: #F1F5F9; color: var(--text2); font-size: .7rem; font-weight: 800; padding: 3px 10px; border-radius: 99px; margin-left: auto; }
.qtext { font-size: 15.5px; font-weight: 700; color: var(--text); margin: 0 0 12px; line-height: 1.5; }
.qinput-wrap { padding: 0 0 4px; }

/* ── Score card ── */
.score-wrap {
  background: linear-gradient(145deg, var(--blue-x) 0%, var(--blue-d) 50%, #3B82F6 100%);
  border-radius: 22px;
  padding: 40px 28px;
  margin: 16px 16px 20px;
  text-align: center;
  box-shadow: var(--shadow-blue);
  position: relative; overflow: hidden;
}
.score-wrap::before { content:''; position:absolute; top:-60px; right:-60px; width:220px; height:220px; border-radius:50%; background:rgba(255,255,255,.06); }
.sw-emoji { font-size: 3.4rem; margin-bottom: 8px; position: relative; z-index: 1; }
.sw-name { color: rgba(255,255,255,.75); font-size: .95rem; margin: 0 0 8px; font-weight: 500; position: relative; z-index: 1; }
.sw-val { color: #fff; font-size: 3.2rem; font-weight: 900; margin: 0; letter-spacing: -2px; position: relative; z-index: 1; }
.sw-pct { color: rgba(255,255,255,.88); font-size: 1.6rem; font-weight: 800; margin: 2px 0 8px; position: relative; z-index: 1; }
.sw-quiz { color: rgba(255,255,255,.5); font-size: .88rem; margin: 0; position: relative; z-index: 1; }
.submitted-wrap {
  background: linear-gradient(135deg, var(--blue-l), #fff);
  border: 2px solid var(--blue-m);
  border-radius: 20px;
  padding: 36px 24px;
  margin: 16px 16px 20px;
  text-align: center;
  box-shadow: var(--shadow);
}

/* ── Admin Login ── */
.login-wrap {
  background: var(--surface);
  border: 1.5px solid var(--border);
  border-radius: var(--radius);
  padding: 28px 24px;
  margin: 24px 16px;
  box-shadow: var(--shadow-md);
}

/* ── KPI Grid ── */
.kpi-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; padding: 0 16px; margin-bottom: 20px; }
.kpi {
  border-radius: var(--radius);
  padding: 20px 18px;
  box-shadow: var(--shadow);
  position: relative; overflow: hidden;
  cursor: default;
  transition: transform .2s, box-shadow .2s;
}
.kpi:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
.kpi::after { content:''; position:absolute; bottom:-28px; right:-28px; width:100px; height:100px; border-radius:50%; opacity:.08; }
.kpi-b { background: linear-gradient(135deg,#EFF6FF,#DBEAFE); border: 1.5px solid #BFDBFE; }
.kpi-b::after { background: var(--blue); }
.kpi-g { background: linear-gradient(135deg,#ECFDF5,#D1FAE5); border: 1.5px solid #6EE7B7; }
.kpi-g::after { background: var(--green); }
.kpi-o { background: linear-gradient(135deg,#FFFBEB,#FEF3C7); border: 1.5px solid #FCD34D; }
.kpi-o::after { background: var(--orange); }
.kpi-p { background: linear-gradient(135deg,#F5F3FF,#EDE9FE); border: 1.5px solid #C4B5FD; }
.kpi-p::after { background: var(--purple); }
.kpi-ico { font-size: 1.8rem; margin-bottom: 10px; display: block; }
.kpi-val { font-size: 2.2rem; font-weight: 900; margin: 0; letter-spacing: -1px; line-height: 1; }
.kpi-b .kpi-val{color:var(--blue)} .kpi-g .kpi-val{color:var(--green)}
.kpi-o .kpi-val{color:var(--orange)} .kpi-p .kpi-val{color:var(--purple)}
.kpi-lbl { font-size: .68rem; font-weight: 800; color: var(--text3); margin: 5px 0 0; text-transform: uppercase; letter-spacing: .1em; }

/* ── Stat double ── */
.stat-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; padding: 0 16px; margin-bottom: 12px; }
.stat-box { background: var(--surface); border: 1.5px solid var(--border); border-radius: var(--radius); padding: 18px; text-align: center; box-shadow: var(--shadow); }
.stat-val { font-size: 2rem; font-weight: 900; margin: 0; letter-spacing: -1px; }
.stat-lbl { font-size: .7rem; font-weight: 700; color: var(--text3); margin: 4px 0 0; text-transform: uppercase; letter-spacing: .08em; }

/* ── Score bars ── */
.score-bars { padding: 0 16px; }
.sb-row { display: flex; align-items: center; gap: 10px; margin: 8px 0; }
.sb-lbl { font-size: .82rem; font-weight: 600; color: var(--text); min-width: 110px; max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sb-bg { flex: 1; background: #DBEAFE; border-radius: 99px; height: 10px; overflow: hidden; }
.sb-fill { height: 10px; border-radius: 99px; }
.sb-val { font-size: .82rem; font-weight: 800; min-width: 36px; text-align: right; }

/* ── Activity feed ── */
.activity { padding: 0 16px; }
.act-item { display: flex; align-items: center; gap: 12px; padding: 12px 0; border-bottom: 1px solid var(--border); }
.act-item:last-child { border-bottom: none; }
.act-av { width: 40px; height: 40px; border-radius: 50%; flex-shrink: 0; background: linear-gradient(135deg, #BFDBFE, var(--blue-l)); color: var(--blue-d); font-weight: 800; font-size: 13px; display: flex; align-items: center; justify-content: center; }
.act-name { font-weight: 700; font-size: 14px; color: var(--text); }
.act-quiz { font-size: .77rem; color: var(--text3); margin-top: 1px; }
.act-right { margin-left: auto; text-align: right; flex-shrink: 0; }
.act-pct { font-size: 1rem; font-weight: 900; }
.act-time { font-size: .7rem; color: var(--text3); }

/* ── Agent card admin ── */
.ag-card { background: var(--surface); border: 1.5px solid var(--border); border-radius: var(--radius); padding: 14px 16px; margin: 6px 0; box-shadow: var(--shadow); }
.ag-card:hover { border-color: var(--blue-m); }
.ag-top { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.ag-av { width: 38px; height: 38px; border-radius: 50%; flex-shrink: 0; background: linear-gradient(135deg, #BFDBFE, var(--blue-l)); color: var(--blue-d); display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 13px; }

/* ── Quiz card admin ── */
.qz-card { background: var(--surface); border: 1.5px solid var(--border); border-radius: var(--radius); overflow: hidden; margin: 8px 0; box-shadow: var(--shadow); }
.qz-card-header { padding: 14px 16px; display: flex; align-items: center; gap: 10px; }
.qz-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.qz-dot-on { background: var(--green); box-shadow: 0 0 0 3px var(--green-l); }
.qz-dot-off { background: var(--text3); }
.qz-title { font-size: 1rem; font-weight: 800; color: var(--text); }
.qz-code { font-size: .75rem; font-weight: 700; color: var(--text3); margin-top: 1px; }

/* ── Badges ── */
.bdg { display: inline-block; padding: 3px 10px; border-radius: 99px; font-size: .7rem; font-weight: 800; }
.bdg-g { background: var(--green-l); color: var(--green); }
.bdg-o { background: var(--orange-l); color: var(--orange); }
.bdg-b { background: var(--blue-l); color: var(--blue-d); }
.bdg-gr { background: #F1F5F9; color: var(--text2); }
.bdg-r { background: var(--red-l); color: var(--red); }
</style>
""", unsafe_allow_html=True)

init_db()

try:
    from streamlit_autorefresh import st_autorefresh
    _AR = True
except ImportError:
    _AR = False

_D = {
    "page": "home", "current_agent": None, "current_quiz": None,
    "quiz_questions": None, "quiz_start_time": None, "quiz_answers": {},
    "session_id": None, "admin_logged": False, "quiz_submitted": False,
    "final_score": None, "edit_quiz_id": None, "adding_q_type": "single",
    "_restored": False,
}
for k, v in _D.items():
    if k not in st.session_state:
        st.session_state[k] = v


def go(p):
    st.session_state.page = p
    st.rerun()

def S(k): return st.session_state[k]
def SET(k, v): st.session_state[k] = v


# ── Helpers HTML ──────────────────────────────────────────────────────────────
def section(t): st.markdown(f'<span class="section-label">{t}</span>', unsafe_allow_html=True)
def bdg(t, c="b"): return f'<span class="bdg bdg-{c}">{t}</span>'
def pad(n=1): st.markdown(f'<div style="height:{n*8}px"></div>', unsafe_allow_html=True)


# ── Persistance session ───────────────────────────────────────────────────────
def _tok():
    return hashlib.md5(f"{config.ADMIN_PASSWORD}{datetime.now().strftime('%Y%m%d')}".encode()).hexdigest()[:16]

def _save():
    try:
        to_set = {}
        if S("current_agent"): to_set["a"] = str(S("current_agent")["id"])
        if S("admin_logged"):   to_set["t"] = _tok()
        if S("session_id") and not S("quiz_submitted"): to_set["s"] = str(S("session_id"))
        if S("page") != "home": to_set["p"] = S("page")
        for k, v in to_set.items():
            if st.query_params.get(k) != v:
                st.query_params[k] = v
        for k in list(st.query_params.keys()):
            if k not in to_set:
                del st.query_params[k]
    except Exception:
        pass

def _restore():
    if S("_restored"): return
    SET("_restored", True)
    try:
        qp = st.query_params
        if "a" in qp and not S("current_agent"):
            a = get_agent_by_id(int(qp["a"]))
            if a: SET("current_agent", a)
        if "t" in qp and not S("admin_logged"):
            if qp["t"] == _tok(): SET("admin_logged", True)
        if "s" in qp and S("current_agent") and not S("session_id"):
            sid = int(qp["s"])
            sess = get_session_by_id(sid)
            if sess and not sess.get("completed"):
                quiz = get_quiz(sess["quiz_id"])
                if quiz:
                    epoch = float(sess.get("start_time_epoch") or time.time())
                    remaining = quiz["duree_minutes"] * 60 - (time.time() - epoch)
                    if remaining > 15:
                        qs = get_questions(quiz["id"])
                        try:
                            ans = json.loads(sess.get("answers_json") or "{}")
                            ans = {int(k) if str(k).isdigit() else k: v for k, v in ans.items()}
                        except Exception:
                            ans = {}
                        SET("current_quiz", quiz); SET("quiz_questions", qs)
                        SET("quiz_start_time", epoch); SET("quiz_answers", ans)
                        SET("session_id", sid); SET("quiz_submitted", False)
                        SET("page", "agent_quiz")
        if "p" in qp and S("page") == "home":
            pg = qp["p"]
            if pg in ("agent_quiz_code", "agent_quiz") and S("current_agent"):
                SET("page", pg)
            elif pg in ("admin_dashboard", "admin_quiz_edit") and S("admin_logged"):
                SET("page", pg)
    except Exception:
        pass

_restore()


# ── PDF export ────────────────────────────────────────────────────────────────
def _make_pdf(quiz, questions):
    from fpdf import FPDF

    TYPES = {"single": "Choix unique", "multiple": "Choix multiple",
             "numeric": "Valeur numerique", "text": "Texte libre"}

    class PDF(FPDF):
        def header(self):
            self.set_fill_color(30, 58, 138)
            self.rect(0, 0, 210, 40, "F")
            self.set_text_color(255, 255, 255)
            self.set_font("Helvetica", "B", 18)
            self.set_xy(12, 8)
            self.cell(186, 9, quiz["titre"][:55], ln=True)
            self.set_font("Helvetica", "", 10)
            self.set_xy(12, 20)
            total = sum(q["points"] for q in questions)
            self.cell(186, 6, f"Code: {quiz['code']}   |   {quiz['duree_minutes']} min   |   {len(questions)} questions   |   {total:.0f} point(s)", ln=True)
            if quiz.get("description"):
                self.set_xy(12, 29)
                self.set_font("Helvetica", "I", 9)
                self.set_text_color(180, 210, 255)
                self.cell(186, 6, quiz["description"][:80], ln=True)
            self.set_text_color(0, 0, 0)
            self.ln(14)

        def footer(self):
            self.set_y(-13)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(160, 160, 160)
            self.cell(0, 8, f"QuizAgent CI  —  {datetime.now().strftime('%d/%m/%Y %H:%M')}  —  Page {self.page_no()}", align="C")

    pdf = PDF()
    pdf.set_auto_page_break(True, margin=16)
    pdf.add_page()

    for i, q in enumerate(questions):
        pts = f"{q['points']:.0f} pt" + ("s" if q["points"] != 1 else "")

        # Header question
        pdf.set_fill_color(239, 246, 255)
        pdf.set_draw_color(191, 219, 254)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(29, 78, 216)
        pdf.cell(20, 7, f"  Q{i+1}", fill=True, border="LTB")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(90, 7, TYPES.get(q["type"], ""), border="TB")
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(0, 7, pts, align="R", border="RTB", ln=True)

        # Barre bleue + texte
        pdf.set_fill_color(37, 99, 235)
        x0, y0 = pdf.get_x(), pdf.get_y()
        pdf.rect(x0, y0, 3, 10, "F")
        pdf.set_x(x0 + 5)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(15, 23, 42)
        pdf.multi_cell(174, 6, q["texte"])
        pdf.ln(3)

        if q["type"] in ("single", "multiple"):
            for o in q["options"]:
                if o["is_correct"]:
                    pdf.set_fill_color(209, 250, 229)
                    pdf.set_draw_color(5, 150, 105)
                    pdf.set_text_color(6, 95, 70)
                    txt, style = "  ✓  " + o["texte"], "B"
                else:
                    pdf.set_fill_color(249, 250, 251)
                    pdf.set_draw_color(226, 232, 244)
                    pdf.set_text_color(15, 23, 42)
                    txt, style = "  ○  " + o["texte"], ""
                pdf.set_x(16)
                pdf.set_font("Helvetica", style, 10)
                pdf.multi_cell(172, 7, txt, border=1, fill=True)
                pdf.ln(1)
        elif q["type"] == "numeric":
            pdf.set_x(16)
            pdf.set_fill_color(209, 250, 229)
            pdf.set_text_color(6, 95, 70)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(172, 8, f"  Reponse : {q.get('reponse_correcte_num')}", fill=True, border=1, ln=True)
        elif q["type"] == "text":
            raw = (q.get("reponse_correcte_txt") or "").strip()
            pdf.set_x(16)
            pdf.set_font("Helvetica", "B", 10)
            if raw:
                pdf.set_fill_color(209, 250, 229)
                pdf.set_text_color(6, 95, 70)
                pdf.multi_cell(172, 8, f"  Reponses : {raw}", fill=True, border=1)
            else:
                pdf.set_fill_color(241, 245, 249)
                pdf.set_text_color(100, 116, 139)
                pdf.cell(172, 8, "  Question ouverte", fill=True, border=1, ln=True)

        pdf.ln(7)

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE — HOME
# ══════════════════════════════════════════════════════════════════════════════
def render_home():
    org = f'<p class="hero-org">{config.ORG_NAME}</p>' if config.ORG_NAME else ""
    st.markdown(f"""
    <div class="hero-wrap">
      <div class="hero-badge">📋 Plateforme d'évaluation</div>
      <div class="hero-icon">📝</div>
      <h1 class="hero-title">{config.APP_TITLE}</h1>
      <p class="hero-sub">{config.APP_SUBTITLE}</p>
      {org}
    </div>
    <div class="hero-btns">
    """, unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("👤  Je suis Agent", key="h_agent", use_container_width=True, type="primary"):
            go("agent_search")
    with c2:
        if st.button("⚙️  Administration", key="h_admin", use_container_width=True):
            go("admin_login")
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  AGENT — Recherche
# ══════════════════════════════════════════════════════════════════════════════
def render_agent_search():
    st.markdown('<div class="app-header"><span class="app-header-icon">👤</span><span class="app-header-title">Identification</span></div>', unsafe_allow_html=True)
    section("Tapez votre nom ou matricule")
    st.markdown('<div style="padding:0 16px">', unsafe_allow_html=True)
    q = st.text_input(" ", placeholder="Ex : Konan, Diallo, AGT001…", label_visibility="collapsed", key="sq")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div style="padding:0 16px">', unsafe_allow_html=True)
    if st.button("← Retour à l'accueil", key="as_back", use_container_width=True):
        go("home")
    st.markdown('</div>', unsafe_allow_html=True)

    q = (q or "").strip()
    if len(q) < 2:
        if len(q) == 1: st.caption("  Continuez à taper…")
        return

    agents = search_agents(q)
    if not agents:
        st.markdown('<div style="padding:0 16px">', unsafe_allow_html=True)
        st.warning("Aucun agent trouvé. Contactez votre superviseur.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    section(f"{len(agents)} résultat(s) — appuyez sur votre nom")
    for a in agents:
        label = f"👤  {a['nom']} {a['prenom']}".strip()
        if a["matricule"]: label += f"  ·  {a['matricule']}"
        st.markdown('<div class="agent-btn-wrap">', unsafe_allow_html=True)
        if st.button(label, key=f"sel_{a['id']}", use_container_width=True, type="primary"):
            SET("current_agent", a); _save(); go("agent_quiz_code")
        st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  AGENT — Code quiz
# ══════════════════════════════════════════════════════════════════════════════
def render_agent_quiz_code():
    agent = S("current_agent")
    if not agent: go("agent_search"); return

    st.markdown('<div class="app-header"><span class="app-header-icon">📋</span><span class="app-header-title">Accès au Quiz</span></div>', unsafe_allow_html=True)

    init = (agent["nom"][0] + (agent["prenom"][0] if agent["prenom"] else "")).upper()
    st.markdown(f"""
    <div class="agent-info">
      <div class="agent-avatar">{init}</div>
      <div>
        <div class="agent-name">{agent["nom"]} {agent["prenom"]}</div>
        <div class="agent-mat">{agent["matricule"] or "Agent de terrain"}</div>
      </div>
    </div>""", unsafe_allow_html=True)

    section("Code du quiz — communiqué par votre superviseur")
    st.markdown('<div style="padding:0 16px">', unsafe_allow_html=True)
    code = st.text_input(" ", placeholder="Ex : QZ001", max_chars=20, label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="padding:0 16px">', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2])
    with c1:
        if st.button("← Retour", key="aqc_back", use_container_width=True):
            go("agent_search")
    with c2:
        if st.button("▶  Commencer", key="aqc_start", type="primary", use_container_width=True):
            _start_quiz(agent, code)
    st.markdown('</div>', unsafe_allow_html=True)


def _start_quiz(agent, code):
    if not (code or "").strip(): st.warning("Saisissez un code."); return
    quiz = get_quiz_by_code(code.strip())
    if not quiz: st.error("Code incorrect ou quiz désactivé."); return
    qs = get_questions(quiz["id"], shuffled=bool(quiz.get("randomize_questions", 0)))
    if not qs: st.error("Ce quiz ne contient pas encore de questions."); return
    if session_already_completed(agent["id"], quiz["id"]):
        st.warning("Vous avez déjà soumis ce quiz."); return
    epoch = time.time()
    sid = create_session(agent["id"], quiz["id"], sum(q["points"] for q in qs), epoch)
    SET("current_quiz", quiz); SET("quiz_questions", qs)
    SET("quiz_start_time", epoch); SET("quiz_answers", {})
    SET("quiz_submitted", False); SET("session_id", sid)
    _save(); go("agent_quiz")


# ══════════════════════════════════════════════════════════════════════════════
#  AGENT — Quiz
# ══════════════════════════════════════════════════════════════════════════════
def _calc(questions, answers):
    score, records = 0.0, []
    for q in questions:
        qid = q["id"]; resp = answers.get(qid, ""); ok = 0
        if q["type"] == "single":
            ok = 1 if resp in [o["id"] for o in q["options"] if o["is_correct"]] else 0
        elif q["type"] == "multiple":
            cor = set(o["id"] for o in q["options"] if o["is_correct"])
            giv = set(resp) if isinstance(resp, list) else set()
            ok = 1 if giv == cor and cor else 0
        elif q["type"] == "numeric":
            try:
                exp = float(q["reponse_correcte_num"]) if q["reponse_correcte_num"] is not None else None
                giv = float(str(resp).replace(",", ".")) if str(resp).strip() else None
                ok = 1 if exp is not None and giv is not None and abs(giv - exp) < 0.01 else 0
            except: ok = 0
        elif q["type"] == "text":
            raw = (q.get("reponse_correcte_txt") or "").strip()
            if raw: ok = 1 if str(resp).lower().strip() in [a.lower().strip() for a in raw.split("|") if a.strip()] else 0
            else:   ok = 1
        if ok: score += q["points"]
        records.append({"question_id": qid,
                         "reponse": json.dumps(resp, ensure_ascii=False) if isinstance(resp, list) else str(resp),
                         "is_correct": ok})
    return score, records


def _submit():
    if S("quiz_submitted"): return
    ql = S("quiz_questions")
    score, records = _calc(ql, S("quiz_answers"))
    submit_session(S("session_id"), score, records)
    SET("final_score", {"score": score, "max_score": sum(q["points"] for q in ql)})
    SET("quiz_submitted", True)


def render_agent_quiz():
    if S("quiz_submitted"): go("agent_result"); return

    quiz = S("current_quiz"); questions = S("quiz_questions")
    if _AR: st_autorefresh(interval=2000, key="qr")

    remaining = max(0, quiz["duree_minutes"] * 60 - (time.time() - S("quiz_start_time")))
    if remaining <= 0:
        _submit(); SET("page", "agent_result"); st.rerun(); return

    mins, secs = int(remaining // 60), int(remaining % 60)
    if remaining > 300:   cls, lbl, ico = "qt-n", "Temps restant", "⏱"
    elif remaining > 60:  cls, lbl, ico = "qt-w", "Moins de 5 min !", "⚠️"
    else:                 cls, lbl, ico = "qt-d", "Dépêchez-vous !", "🚨"

    st.markdown(f"""
    <div id="qtbar">
      <div class="qti">
        <div class="qtbox {cls}">
          <span class="qt-ico">{ico}</span>
          <div><p class="qt-time">{mins:02d}:{secs:02d}</p><p class="qt-lbl">{lbl}</p></div>
        </div>
      </div>
    </div>
    <div style="height:88px"></div>
    <script>
    (function(){{
      var b=document.getElementById('qtbar');
      if(b&&b.parentNode!==document.body)document.body.insertBefore(b,document.body.firstChild);
    }})();
    </script>""", unsafe_allow_html=True)

    answered = sum(1 for v in S("quiz_answers").values() if v not in ("", [], None))
    pct = answered / len(questions) * 100 if questions else 0
    st.markdown(f"""
    <div class="prog-wrap">
      <div class="prog-top"><span><b>{quiz['titre']}</b></span><span>{answered}/{len(questions)} répondue(s)</span></div>
      <div class="prog-bg"><div class="prog-fill" style="width:{pct:.0f}%"></div></div>
    </div>""", unsafe_allow_html=True)

    ICONS = {"single": "⭕", "multiple": "☑️", "numeric": "🔢", "text": "📝"}
    HINTS = {"single": "Une seule réponse", "multiple": "Plusieurs réponses", "numeric": "Entrez un nombre", "text": "Réponse libre"}

    for i, q in enumerate(questions):
        qid = q["id"]
        pts = f"{q['points']:.0f} pt" + ("s" if q["points"] != 1 else "")
        st.markdown(f"""
        <div class="qcard">
          <div class="qmeta">
            <span class="qbadge-num">Q{i+1}</span>
            <span class="qbadge-type">{ICONS[q['type']]} {HINTS[q['type']]}</span>
            <span class="qbadge-pts">{pts}</span>
          </div>
          <p class="qtext">{q['texte']}</p>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div style="padding:4px 16px 0">', unsafe_allow_html=True)
        if q["type"] == "single":
            opts = q["options"]; cur = S("quiz_answers").get(qid)
            idx = next((j for j, o in enumerate(opts) if o["id"] == cur), None)
            sel = st.radio(" ", range(len(opts)), format_func=lambda x, _o=opts: _o[x]["texte"],
                           index=idx, key=f"q_{qid}", label_visibility="collapsed")
            if sel is not None: S("quiz_answers")[qid] = opts[sel]["id"]
        elif q["type"] == "multiple":
            cur = S("quiz_answers").get(qid, [])
            sel = []
            for o in q["options"]:
                if st.checkbox(o["texte"], value=(o["id"] in cur), key=f"q_{qid}_{o['id']}"): sel.append(o["id"])
            S("quiz_answers")[qid] = sel
        elif q["type"] == "numeric":
            val = S("quiz_answers").get(qid, "")
            v = st.text_input(" ", value=str(val) if val != "" else "", key=f"q_{qid}",
                               placeholder="Entrez un nombre…", label_visibility="collapsed")
            S("quiz_answers")[qid] = v
        elif q["type"] == "text":
            val = S("quiz_answers").get(qid, "")
            v = st.text_area(" ", value=val, key=f"q_{qid}", height=90,
                              placeholder="Votre réponse…", label_visibility="collapsed")
            S("quiz_answers")[qid] = v
        st.markdown('</div>', unsafe_allow_html=True)
        pad()

    # Sauvegarde auto
    if S("session_id") and not S("quiz_submitted"):
        try:
            save_quiz_progress(S("session_id"), json.dumps(S("quiz_answers")), S("quiz_start_time"))
        except Exception: pass

    st.markdown('<hr style="margin:20px 16px">', unsafe_allow_html=True)
    st.markdown('<div style="padding:0 16px">', unsafe_allow_html=True)
    if st.button("✅  Soumettre mes réponses", key="q_submit", type="primary", use_container_width=True):
        _submit(); go("agent_result"); return
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  AGENT — Résultat
# ══════════════════════════════════════════════════════════════════════════════
def render_agent_result():
    res = S("final_score"); quiz = S("current_quiz"); agent = S("current_agent")
    if not res or not agent or not quiz: go("home"); return

    show = bool(quiz.get("show_score", 1))
    score, maxs = res["score"], res["max_score"]
    pct = (score / maxs * 100) if maxs > 0 else 0

    if show:
        emoji = "🏆" if pct >= 80 else ("👍" if pct >= 60 else "📚")
        st.markdown(f"""
        <div class="score-wrap">
          <div class="sw-emoji">{emoji}</div>
          <p class="sw-name">{agent['nom']} {agent['prenom']}</p>
          <p class="sw-val">{score:.1f} / {maxs:.1f}</p>
          <p class="sw-pct">{pct:.0f} %</p>
          <p class="sw-quiz">{quiz['titre']}</p>
        </div>""", unsafe_allow_html=True)
        st.markdown('<div style="padding:0 16px">', unsafe_allow_html=True)
        if pct >= 80: st.success("Excellent résultat ! Félicitations ! 🎉")
        elif pct >= 60: st.info("Bon résultat. Continuez vos efforts !")
        else: st.warning("Il faut encore travailler ce sujet. Courage !")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="submitted-wrap">
          <div style="font-size:2.8rem;margin-bottom:10px">✅</div>
          <div style="font-size:1.15rem;font-weight:800;color:var(--blue-x)">Réponses enregistrées</div>
          <div style="color:var(--text3);font-size:.9rem;margin-top:6px">{agent['nom']} {agent['prenom']} · {quiz['titre']}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown(f'<p style="text-align:center;color:var(--text3);font-size:.82rem;margin:6px 0 16px">Soumis le {datetime.now().strftime("%d/%m/%Y à %H:%M")}</p>', unsafe_allow_html=True)
    st.markdown('<div style="padding:0 16px">', unsafe_allow_html=True)
    if st.button("🏠  Retour à l'accueil", key="r_home", use_container_width=True):
        for k in ("current_quiz","quiz_questions","quiz_start_time","quiz_answers","session_id","quiz_submitted","final_score","current_agent"):
            SET(k, _D.get(k))
        _save(); go("home")
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN — Login
# ══════════════════════════════════════════════════════════════════════════════
def render_admin_login():
    if S("admin_logged"): go("admin_dashboard"); return
    st.markdown('<div class="app-header"><span class="app-header-icon">⚙️</span><span class="app-header-title">Administration</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="login-wrap">', unsafe_allow_html=True)
    st.markdown('<h3 style="margin:0 0 16px;font-size:1.1rem;font-weight:800">🔐 Connexion</h3>', unsafe_allow_html=True)
    pwd = st.text_input("Mot de passe", type="password", placeholder="Mot de passe administrateur", label_visibility="collapsed")
    pad()
    c1, c2 = st.columns([1, 2])
    with c1:
        if st.button("← Retour", key="al_back", use_container_width=True): go("home")
    with c2:
        if st.button("Se connecter", key="al_login", type="primary", use_container_width=True):
            if pwd == config.ADMIN_PASSWORD:
                SET("admin_logged", True); _save(); go("admin_dashboard")
            else: st.error("Mot de passe incorrect.")
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN — Dashboard
# ══════════════════════════════════════════════════════════════════════════════
def render_admin_dashboard():
    if not S("admin_logged"): go("admin_login"); return
    st.markdown(f'<div class="app-header"><span class="app-header-icon">⚙️</span><span class="app-header-title">{config.APP_TITLE}</span><span class="app-header-sub">Admin</span></div>', unsafe_allow_html=True)

    t0, t1, t2, t3 = st.tabs(["📊 Vue d'ensemble", "👥 Agents", "📝 Quiz", "📋 Résultats"])
    with t0: _tab_overview()
    with t1: _tab_agents()
    with t2: _tab_quizzes()
    with t3: _tab_results()

    st.markdown('<hr>', unsafe_allow_html=True)
    st.markdown('<div style="padding:0 16px">', unsafe_allow_html=True)
    if st.button("🚪  Déconnexion", key="a_logout", use_container_width=True):
        SET("admin_logged", False); _save(); go("home")
    st.markdown('</div>', unsafe_allow_html=True)


# ── Vue d'ensemble ────────────────────────────────────────────────────────────
def _tab_overview():
    stats = get_stats()
    pad()
    st.markdown(f"""
    <div class="kpi-grid">
      <div class="kpi kpi-b"><span class="kpi-ico">👥</span><p class="kpi-val">{stats['total_agents']}</p><p class="kpi-lbl">Agents total</p></div>
      <div class="kpi kpi-g"><span class="kpi-ico">✅</span><p class="kpi-val">{stats['pub_agents']}</p><p class="kpi-lbl">Publiés</p></div>
      <div class="kpi kpi-p"><span class="kpi-ico">📝</span><p class="kpi-val">{stats['active_quizzes']}</p><p class="kpi-lbl">Quiz actifs</p></div>
      <div class="kpi kpi-o"><span class="kpi-ico">📊</span><p class="kpi-val">{stats['total_submissions']}</p><p class="kpi-lbl">Soumissions</p></div>
    </div>""", unsafe_allow_html=True)

    avg = stats["avg_score"]
    rate = min(100, round(stats["total_submissions"] / max(1, stats["pub_agents"]) * 100))
    col_avg = "var(--green)" if avg >= 70 else ("var(--orange)" if avg >= 50 else "var(--red)")
    st.markdown(f"""
    <div class="stat-row">
      <div class="stat-box">
        <p class="stat-val" style="color:{col_avg}">{avg:.1f}%</p>
        <p class="stat-lbl">Score moyen</p>
      </div>
      <div class="stat-box">
        <p class="stat-val" style="color:var(--blue)">{rate}%</p>
        <p class="stat-lbl">Taux complétion</p>
      </div>
    </div>""", unsafe_allow_html=True)

    if stats["per_quiz"]:
        section("Scores moyens par quiz")
        bars = ""
        for q in stats["per_quiz"]:
            p = min(100, q["avg_pct"] or 0)
            c = "var(--green)" if p >= 70 else ("var(--orange)" if p >= 50 else "var(--red)")
            bars += f'<div class="sb-row"><span class="sb-lbl" title="{q["titre"]}">{q["titre"][:22]}</span><div class="sb-bg"><div class="sb-fill" style="width:{p:.0f}%;background:{c}"></div></div><span class="sb-val" style="color:{c}">{p:.0f}%</span></div>'
        st.markdown(f'<div class="score-bars">{bars}</div>', unsafe_allow_html=True)

    if stats["recent"]:
        section("10 dernières soumissions")
        items = ""
        for r in stats["recent"]:
            p = (r["score"] / r["max_score"] * 100) if r["max_score"] > 0 else 0
            c = "var(--green)" if p >= 70 else ("var(--orange)" if p >= 50 else "var(--red)")
            init = (r["nom"][0] + (r["prenom"][0] if r["prenom"] else "")).upper()
            try:
                dt = datetime.fromisoformat(r["completed_at"])
                diff = datetime.now() - dt
                tstr = f"Il y a {diff.seconds//60} min" if diff.seconds < 3600 else (f"Il y a {diff.seconds//3600}h" if diff.days == 0 else dt.strftime("%d/%m %H:%M"))
            except: tstr = (r["completed_at"] or "")[:16]
            items += f'<div class="act-item"><div class="act-av">{init}</div><div><div class="act-name">{r["nom"]} {r["prenom"]}</div><div class="act-quiz">{r["titre"]}</div></div><div class="act-right"><div class="act-pct" style="color:{c}">{p:.0f}%</div><div class="act-time">{tstr}</div></div></div>'
        st.markdown(f'<div class="activity" style="background:var(--surface);border:1.5px solid var(--border);border-radius:var(--radius);padding:4px 16px;margin:0 16px;box-shadow:var(--shadow)">{items}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="padding:0 16px">', unsafe_allow_html=True)
        st.info("Aucune soumission pour l'instant.")
        st.markdown('</div>', unsafe_allow_html=True)

    section("Actions rapides")
    st.markdown('<div style="padding:0 16px">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("➕  Nouveau quiz", key="ov_new_qz", use_container_width=True, type="primary"):
            SET("edit_quiz_id", None); _save(); go("admin_quiz_edit")
    with c2:
        if st.button("✅  Publier tous les agents", key="ov_pub_all", use_container_width=True):
            publish_all_agents(); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ── Agents ────────────────────────────────────────────────────────────────────
def _ndf(df):
    df.columns = [str(c).lower().strip() for c in df.columns]
    nom = next((c for c in ["nom","name","lastname","noms"] if c in df.columns), None)
    if not nom: return None
    pre = next((c for c in ["prenom","prénom","firstname"] if c in df.columns), None)
    mat = next((c for c in ["matricule","id","code"] if c in df.columns), None)
    out = pd.DataFrame()
    out["nom"] = df[nom]; out["prenom"] = df[pre] if pre else ""
    out["matricule"] = df[mat] if mat else ""
    return out

def _tab_agents():
    s1, s2, s3 = st.tabs(["✏️ Ajouter", "📥 Importer", "📋 Liste"])
    with s1:
        pad()
        with st.form("fag", clear_on_submit=True):
            c1,c2,c3 = st.columns(3)
            with c1: nom = st.text_input("Nom *")
            with c2: pre = st.text_input("Prénom")
            with c3: mat = st.text_input("Matricule")
            if st.form_submit_button("Ajouter l'agent", type="primary", use_container_width=True):
                if not nom.strip(): st.error("Nom obligatoire.")
                elif add_agent_manual(nom.strip(), pre.strip(), mat.strip()): st.success(f"{nom} ajouté."); st.rerun()
                else: st.warning("Cet agent existe déjà.")

    with s2:
        pad()
        st.markdown('<div style="padding:0 16px">', unsafe_allow_html=True)
        st.markdown("**📂 Fichier CSV ou Excel**")
        st.caption("Colonnes : `nom`, `prenom`, `matricule`")
        up = st.file_uploader("Fichier", type=["csv","xlsx","xls"], label_visibility="collapsed")
        if up:
            try:
                df_r = pd.read_csv(up) if up.name.lower().endswith(".csv") else pd.read_excel(up)
                df = _ndf(df_r)
                if df is None: st.error("Colonne 'nom' introuvable.")
                else:
                    st.dataframe(df.head(5), use_container_width=True)
                    st.caption(f"{len(df)} agent(s) dans le fichier")
                    if st.button("✅  Importer", key="ag_imp_file", type="primary", use_container_width=True):
                        n = upsert_agents(df); st.success(f"{n} importé(s)."); st.rerun()
            except Exception as e: st.error(f"Erreur : {e}")
        st.markdown("---")
        st.markdown("**🌐 Google Sheets (lien public)**")
        gs = st.text_input("URL", placeholder="https://docs.google.com/spreadsheets/d/…", label_visibility="collapsed")
        if st.button("Importer depuis Google Sheets", key="ag_imp_gs", use_container_width=True): _gs(gs)
        st.markdown('</div>', unsafe_allow_html=True)

    with s3:
        ags = get_all_agents()
        if not ags: st.info("Aucun agent dans la base."); return
        nb = sum(1 for a in ags if a["published"])
        st.markdown(f'<p style="padding:12px 16px 4px;color:var(--text3);font-size:.85rem"><b style="color:var(--text)">{len(ags)}</b> agent(s) &nbsp;·&nbsp;{bdg(f"{nb} publié(s)","g")} &nbsp;{bdg(f"{len(ags)-nb} brouillon(s)","o")}</p>', unsafe_allow_html=True)
        st.markdown('<div style="padding:0 16px">', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Publier tous", key="ag_pub_all", use_container_width=True, type="primary"):
                publish_all_agents(); st.rerun()
        with c2:
            if st.button("⛔ Dépublier tous", key="ag_unpub_all", use_container_width=True):
                unpublish_all_agents(); st.rerun()
        filtre = st.text_input("🔍 Filtrer", placeholder="Nom, matricule…", key="af", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)
        shown = [a for a in ags if not filtre or filtre.lower() in f"{a['nom']} {a['prenom']} {a['matricule']}".lower()]
        st.markdown('<div style="padding:0 16px">', unsafe_allow_html=True)
        for a in shown:
            init = (a["nom"][0] + (a["prenom"][0] if a["prenom"] else "")).upper()
            pub_b = bdg("✓ Publié","g") if a["published"] else bdg("Brouillon","o")
            mat_s = f' · <span style="color:var(--text3)">{a["matricule"]}</span>' if a["matricule"] else ""
            st.markdown(f'<div class="ag-card"><div class="ag-top"><div class="ag-av">{init}</div><div><b>{a["nom"]} {a["prenom"]}</b>{mat_s}<br>{pub_b}</div></div>', unsafe_allow_html=True)
            c1, c2 = st.columns([3,1])
            with c1:
                if st.button("🔓 Dépublier" if a["published"] else "✅ Publier", key=f"p_{a['id']}", use_container_width=True):
                    set_agent_published(a["id"], 0 if a["published"] else 1); st.rerun()
            with c2:
                if st.button("🗑️", key=f"d_{a['id']}", use_container_width=True):
                    delete_agent(a["id"]); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

def _gs(url):
    if not (url or "").strip(): st.warning("Collez une URL."); return
    try:
        m = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", url)
        if not m: st.error("URL invalide."); return
        sid = m.group(1); gm = re.search(r"gid=(\d+)", url)
        gid = gm.group(1) if gm else "0"
        r = requests.get(f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid={gid}", timeout=15)
        r.raise_for_status()
        df = _ndf(pd.read_csv(io.StringIO(r.text)))
        if df is None: st.error("Colonne 'nom' introuvable."); return
        n = upsert_agents(df); st.success(f"{n} importé(s)."); st.rerun()
    except Exception as e: st.error(f"Erreur : {e}")


# ── Quiz ──────────────────────────────────────────────────────────────────────
def _tab_quizzes():
    pad()
    st.markdown('<div style="padding:0 16px">', unsafe_allow_html=True)
    if st.button("➕  Créer un nouveau quiz", key="qz_create", type="primary", use_container_width=True):
        SET("edit_quiz_id", None); go("admin_quiz_edit")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    quizzes = get_all_quizzes()
    if not quizzes:
        st.markdown('<div style="padding:0 16px">', unsafe_allow_html=True)
        st.info("Aucun quiz. Cliquez sur 'Créer' pour commencer.")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    for quiz in quizzes:
        nb = len(get_questions(quiz["id"]))
        s  = bdg("Actif","g") if quiz["actif"] else bdg("Inactif","gr")
        sc = bdg("Score visible","b") if quiz.get("show_score",1) else bdg("Score masqué","o")
        rn = bdg("Aléatoire","b") if quiz.get("randomize_questions",0) else ""
        with st.expander(f"{'🟢' if quiz['actif'] else '⚫'} {quiz['titre']}  ·  `{quiz['code']}`"):
            st.markdown(f"{s} &nbsp;{sc} &nbsp;{rn} &nbsp;{bdg(str(quiz['duree_minutes'])+' min','gr')} &nbsp;{bdg(str(nb)+' Q','gr')}", unsafe_allow_html=True)
            if quiz["description"]: st.caption(quiz["description"])
            pad()
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("✏️ Modifier", key=f"eq_{quiz['id']}", use_container_width=True):
                    SET("edit_quiz_id", quiz["id"]); go("admin_quiz_edit")
            with c2:
                if st.button("🟢 Activer" if not quiz["actif"] else "🔴 Désactiver", key=f"tq_{quiz['id']}", use_container_width=True):
                    update_quiz(quiz["id"],quiz["titre"],quiz["code"],quiz["duree_minutes"],quiz["description"],0 if quiz["actif"] else 1,quiz.get("show_score",1),quiz.get("randomize_questions",0)); st.rerun()
            with c3:
                if st.button("🗑 Suppr.", key=f"dq_{quiz['id']}", use_container_width=True):
                    delete_quiz(quiz["id"]); st.rerun()
            if nb > 0:
                qs = get_questions(quiz["id"])
                pdf_data = _make_pdf(quiz, qs)
                st.download_button("📄  Corrigé PDF", data=pdf_data,
                                    file_name=f"corrige_{quiz['code']}.pdf",
                                    mime="application/pdf",
                                    key=f"pdf_{quiz['id']}", use_container_width=True)


# ── Résultats ─────────────────────────────────────────────────────────────────
def _tab_results():
    quizzes = get_all_quizzes()
    opts = {0: "— Tous les quiz —"}
    opts.update({q["id"]: f"{q['titre']} ({q['code']})" for q in quizzes})
    st.markdown('<div style="padding:0 16px">', unsafe_allow_html=True)
    sel = st.selectbox("Quiz", list(opts.keys()), format_func=lambda x: opts[x], label_visibility="collapsed")
    results = get_results(sel if sel else None)
    st.markdown('</div>', unsafe_allow_html=True)
    if not results:
        st.markdown('<div style="padding:0 16px">', unsafe_allow_html=True)
        st.info("Aucun résultat disponible.")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    df = pd.DataFrame(results)
    df["pct"] = (df["score"] / df["max_score"] * 100).round(1)
    df["agent"] = df["nom"] + " " + df["prenom"]
    disp = df[["agent","matricule","quiz_titre","score","max_score","pct","completed_at"]].copy()
    disp.columns = ["Agent","Matricule","Quiz","Score","Sur","%","Date"]
    st.dataframe(disp, use_container_width=True)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        disp.to_excel(w, index=False, sheet_name="Résultats")
        ws = w.sheets["Résultats"]
        for col in ws.columns:
            ml = max((len(str(c.value)) for c in col if c.value), default=10)
            ws.column_dimensions[col[0].column_letter].width = min(ml + 4, 40)
    buf.seek(0)
    st.markdown('<div style="padding:0 16px">', unsafe_allow_html=True)
    st.download_button("📥  Télécharger Excel", data=buf.getvalue(),
                        file_name=f"resultats_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN — Éditeur Quiz
# ══════════════════════════════════════════════════════════════════════════════
_TYPES = {"single":"⭕  Choix unique","multiple":"☑️  Choix multiple",
          "numeric":"🔢  Valeur numérique","text":"📝  Texte libre"}

def render_admin_quiz_edit():
    if not S("admin_logged"): go("admin_login"); return
    qid = S("edit_quiz_id"); is_new = qid is None
    existing = get_quiz(qid) if not is_new else None
    st.markdown(f'<div class="app-header"><span class="app-header-icon">📝</span><span class="app-header-title">{"Nouveau Quiz" if is_new else "Modifier le Quiz"}</span></div>', unsafe_allow_html=True)

    st.markdown('<div style="padding:0 16px">', unsafe_allow_html=True)
    with st.form("fqi"):
        titre = st.text_input("Titre *", value=existing["titre"] if existing else "", placeholder="Ex : Évaluation module Femme")
        c1, c2 = st.columns(2)
        with c1: code = st.text_input("Code *", value=existing["code"] if existing else "", placeholder="QZ001", max_chars=20)
        with c2: duree = st.number_input("Durée (min)", min_value=1, max_value=600, value=existing["duree_minutes"] if existing else 30)
        desc = st.text_area("Description", value=existing["description"] if existing else "", height=68)
        c1, c2 = st.columns(2)
        with c1: show_sc = st.checkbox("Afficher le score", value=bool(existing.get("show_score",1)) if existing else True)
        with c2: rnd = st.checkbox("Questions aléatoires", value=bool(existing.get("randomize_questions",0)) if existing else False)
        if st.form_submit_button("💾  Enregistrer", type="primary", use_container_width=True):
            if not titre.strip() or not code.strip(): st.error("Titre et code obligatoires.")
            else:
                if is_new:
                    try:
                        nid = create_quiz(titre.strip(),code.strip(),int(duree),desc.strip(),int(show_sc),int(rnd))
                        SET("edit_quiz_id", nid); st.success("Quiz créé !"); st.rerun()
                    except Exception as e: st.error(f"Erreur (code déjà existant ?) : {e}")
                else:
                    update_quiz(qid,titre.strip(),code.strip(),int(duree),desc.strip(),existing["actif"],int(show_sc),int(rnd))
                    st.success("Quiz mis à jour."); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    cur_id = S("edit_quiz_id")
    if not cur_id:
        st.markdown('<div style="padding:0 16px">', unsafe_allow_html=True)
        if st.button("← Retour", key="qe_back_top", use_container_width=True): go("admin_dashboard")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    questions = get_questions(cur_id)
    section(f"Questions ({len(questions)})")

    st.markdown('<div style="padding:0 16px">', unsafe_allow_html=True)
    if questions:
        for i, q in enumerate(questions):
            with st.expander(f"Q{i+1}  ·  {_TYPES[q['type']]}  ·  {q['texte'][:48]}{'…' if len(q['texte'])>48 else ''}"):
                if q["type"] in ("single","multiple"):
                    for o in q["options"]: st.markdown(f"{'✅' if o['is_correct'] else '◻️'} {o['texte']}")
                elif q["type"] == "numeric": st.markdown(f"**Réponse :** `{q['reponse_correcte_num']}`")
                elif q["type"] == "text": st.markdown(f"**Réponses :** `{q['reponse_correcte_txt']}`")
                st.caption(f"{q['points']} point(s)")
                if st.button("🗑️ Supprimer", key=f"dq_{q['id']}"):
                    delete_question(q["id"]); reorder_questions(cur_id); st.rerun()
    else:
        st.info("Aucune question. Ajoutez-en ci-dessous.")
    st.markdown('</div>', unsafe_allow_html=True)

    section("Ajouter une question")
    st.markdown('<div style="padding:0 16px">', unsafe_allow_html=True)
    q_type = st.selectbox("Type", list(_TYPES.keys()), format_func=lambda x: _TYPES[x], key="aqt", label_visibility="collapsed")
    with st.form("faq", clear_on_submit=True):
        q_txt = st.text_area("Question *", height=88, placeholder="Saisissez votre question…")
        q_pts = st.number_input("Points", min_value=0.5, max_value=20.0, value=1.0, step=0.5)
        opts_d = []
        if q_type in ("single","multiple"):
            st.markdown("**Options** — cochez ✅ la/les bonne(s) réponse(s)")
            for j in range(6):
                c1, c2 = st.columns([5,1])
                with c1: ot = st.text_input(f"Option {j+1}", key=f"ot_{j}", label_visibility="collapsed", placeholder=f"Option {j+1}…")
                with c2: oc = st.checkbox("✅", key=f"oc_{j}")
                if ot.strip(): opts_d.append({"texte": ot.strip(), "is_correct": oc})
        elif q_type == "numeric": c_num = st.number_input("Réponse correcte", value=0.0, format="%.4f")
        elif q_type == "text":    c_txt = st.text_input("Réponse(s)", placeholder="rep1 | rep2  (laisser vide = question ouverte)")
        if st.form_submit_button("➕  Ajouter la question", type="primary", use_container_width=True):
            err = None
            if not q_txt.strip(): err = "Texte obligatoire."
            elif q_type in ("single","multiple"):
                if not opts_d: err = "Ajoutez au moins une option."
                elif not any(o["is_correct"] for o in opts_d): err = "Cochez au moins une bonne réponse."
                elif q_type == "single" and sum(o["is_correct"] for o in opts_d) > 1: err = "Une seule bonne réponse."
            if err: st.error(err)
            else:
                ordre = len(questions)
                if q_type in ("single","multiple"): add_question(cur_id,q_txt.strip(),q_type,ordre,q_pts,options=opts_d)
                elif q_type == "numeric":           add_question(cur_id,q_txt.strip(),q_type,ordre,q_pts,num=c_num)
                elif q_type == "text":              add_question(cur_id,q_txt.strip(),q_type,ordre,q_pts,txt=(c_txt.strip() if c_txt else ""))
                st.success("Question ajoutée ✓"); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<hr>', unsafe_allow_html=True)
    st.markdown('<div style="padding:0 16px">', unsafe_allow_html=True)
    if st.button("← Retour au dashboard", key="qe_back_bot", use_container_width=True): go("admin_dashboard")
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTEUR
# ══════════════════════════════════════════════════════════════════════════════
_R = {
    "home": render_home, "agent_search": render_agent_search,
    "agent_quiz_code": render_agent_quiz_code, "agent_quiz": render_agent_quiz,
    "agent_result": render_agent_result, "admin_login": render_admin_login,
    "admin_dashboard": render_admin_dashboard, "admin_quiz_edit": render_admin_quiz_edit,
}
fn = _R.get(st.session_state.get("page","home"))
if fn: fn()
else: go("home")
