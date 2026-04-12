"""
app.py — QuizAgent CI  |  Interface principale Streamlit
"""

import streamlit as st
import pandas as pd
import json, time, io, re, requests
from datetime import datetime

import config
from database import (
    init_db, search_agents, get_all_agents, upsert_agents,
    set_agent_published, publish_all_agents, unpublish_all_agents,
    delete_agent, add_agent_manual,
    get_quiz_by_code, get_all_quizzes, get_quiz, create_quiz, update_quiz, delete_quiz,
    get_questions, add_question, delete_question, reorder_questions,
    create_session, submit_session, get_results, session_already_completed,
)

# ── Config page ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon="📝",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Design System ─────────────────────────────────────────────────────────────
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">

<style>
/* ── Reset & font ── */
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"], .stMarkdown p, label, input,
textarea, button, select, .stRadio label, .stCheckbox label {
    font-family: 'Outfit', sans-serif !important;
}

/* ── Masquer chrome Streamlit ── */
#MainMenu, footer, header, .stDeployButton { display: none !important; }

/* ── Conteneur ── */
.block-container {
    padding: 0 1rem 5rem 1rem !important;
    max-width: 640px !important;
    margin: 0 auto !important;
}

/* ── Variables CSS ── */
:root {
    --blue:        #2563EB;
    --blue-dark:   #1D4ED8;
    --blue-xdark:  #1E3A6E;
    --blue-light:  #EFF6FF;
    --blue-mid:    #DBEAFE;
    --surface:     #FFFFFF;
    --bg:          #F7F9FD;
    --border:      #E2E8F4;
    --text:        #0F172A;
    --muted:       #64748B;
    --green:       #059669;
    --orange:      #D97706;
    --red:         #DC2626;
    --radius:      12px;
    --shadow-sm:   0 1px 3px rgba(15,23,42,.08), 0 1px 2px rgba(15,23,42,.04);
    --shadow:      0 4px 16px rgba(15,23,42,.08), 0 1px 4px rgba(15,23,42,.04);
    --shadow-lg:   0 8px 32px rgba(37,99,235,.18), 0 2px 8px rgba(15,23,42,.06);
}

/* ── Topbar ── */
.topbar {
    background: var(--blue-xdark);
    margin: 0 -1rem 1.8rem -1rem;
    padding: 16px 20px;
    display: flex;
    align-items: center;
    gap: 12px;
}
.topbar-icon  { font-size: 1.4rem; }
.topbar-title { color: #fff; font-size: 1.1rem; font-weight: 700; }
.topbar-back  {
    margin-left: auto;
    background: rgba(255,255,255,.12);
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    font-family: 'Outfit', sans-serif;
}
.topbar-back:hover { background: rgba(255,255,255,.22); }

/* ── Hero (home) ── */
.hero {
    background: linear-gradient(145deg, var(--blue-xdark) 0%, var(--blue) 100%);
    border-radius: 20px;
    padding: 40px 28px 36px;
    text-align: center;
    margin-bottom: 24px;
    box-shadow: var(--shadow-lg);
}
.hero-icon  { font-size: 3rem; margin-bottom: 8px; }
.hero-title {
    color: #fff;
    font-size: 2rem;
    font-weight: 900;
    letter-spacing: -.5px;
    margin: 0 0 6px;
}
.hero-sub   { color: rgba(255,255,255,.75); font-size: 1rem; margin: 0; }

/* ── Cards ── */
.card {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: var(--radius);
    padding: 18px 20px;
    margin: 10px 0;
    box-shadow: var(--shadow-sm);
}
.card-title {
    font-size: .75rem;
    font-weight: 700;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: .08em;
    margin: 0 0 12px;
}

/* ── Section label ── */
.section-label {
    font-size: .72rem;
    font-weight: 700;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: .1em;
    margin: 24px 0 8px;
}

/* ── Boutons Streamlit ── */
.stButton > button {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    border-radius: 10px !important;
    padding: 13px 20px !important;
    width: 100% !important;
    transition: all .18s ease !important;
    letter-spacing: .01em !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--blue) 0%, var(--blue-dark) 100%) !important;
    border: none !important;
    color: #fff !important;
    box-shadow: 0 4px 14px rgba(37,99,235,.35) !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(37,99,235,.45) !important;
}
.stButton > button[kind="secondary"] {
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    color: var(--text) !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {
    font-family: 'Outfit', sans-serif !important;
    font-size: 15px !important;
    border-radius: 10px !important;
    border: 1.5px solid var(--border) !important;
    padding: 11px 14px !important;
    background: var(--surface) !important;
    color: var(--text) !important;
    transition: border-color .15s !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--blue) !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,.12) !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div {
    font-family: 'Outfit', sans-serif !important;
    font-size: 15px !important;
    border-radius: 10px !important;
    border: 1.5px solid var(--border) !important;
}

/* ── Titre des labels ── */
.stTextInput label, .stTextArea label, .stSelectbox label,
.stNumberInput label, .stRadio label, .stCheckbox label {
    font-family: 'Outfit', sans-serif !important;
    font-size: 13.5px !important;
    font-weight: 600 !important;
    color: var(--text) !important;
}

/* ── Timer ── */
.timer-wrap {
    border-radius: 16px;
    padding: 18px 16px;
    text-align: center;
    margin-bottom: 16px;
    transition: background .4s;
}
.timer-normal  { background: linear-gradient(135deg, #1E3A6E, #2563EB); box-shadow: 0 6px 24px rgba(37,99,235,.28); }
.timer-warning { background: linear-gradient(135deg, #92400E, #D97706); box-shadow: 0 6px 24px rgba(217,119,6,.3); }
.timer-danger  { background: linear-gradient(135deg, #7F1D1D, #DC2626); box-shadow: 0 6px 24px rgba(220,38,38,.35); animation: heartbeat .8s infinite; }

@keyframes heartbeat {
    0%,100% { transform: scale(1);    opacity: 1; }
    50%      { transform: scale(1.02); opacity: .88; }
}
.timer-time   { color: #fff; font-size: 3rem; font-weight: 900; letter-spacing: 5px; margin: 0; line-height: 1; }
.timer-label  { color: rgba(255,255,255,.65); font-size: .8rem; font-weight: 600; margin-top: 4px; text-transform: uppercase; letter-spacing: .1em; }

/* ── Barre de progression ── */
.prog-wrap { margin: 10px 0 18px; }
.prog-meta { display: flex; justify-content: space-between; font-size: .82rem; color: var(--muted); margin-bottom: 6px; font-weight: 500; }
.prog-bg   { background: var(--blue-mid); border-radius: 99px; height: 7px; overflow: hidden; }
.prog-fill { background: linear-gradient(90deg, var(--blue), var(--blue-dark)); height: 7px; border-radius: 99px; transition: width .4s ease; }

/* ── Carte question ── */
.q-card {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-left: 4px solid var(--blue);
    border-radius: 0 var(--radius) var(--radius) 0;
    padding: 16px 18px 8px;
    margin: 14px 0 0;
    box-shadow: var(--shadow-sm);
}
.q-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
}
.q-num  { background: var(--blue-light); color: var(--blue); font-size: .75rem; font-weight: 800; padding: 3px 9px; border-radius: 99px; }
.q-pts  { background: #F1F5F9; color: var(--muted); font-size: .75rem; font-weight: 700; padding: 3px 9px; border-radius: 99px; margin-left: auto; }
.q-type { color: var(--muted); font-size: .78rem; font-weight: 500; }
.q-text { font-size: 15px; font-weight: 600; color: var(--text); margin: 0 0 12px; line-height: 1.45; }

/* ── Radio / Checkbox ── */
.stRadio > div { gap: 4px !important; }
.stRadio > div > label {
    background: var(--bg);
    border: 1.5px solid var(--border);
    border-radius: 8px !important;
    padding: 10px 14px !important;
    font-size: 14.5px !important;
    font-weight: 500 !important;
    transition: all .15s !important;
    cursor: pointer !important;
}
.stRadio > div > label:hover { border-color: var(--blue) !important; background: var(--blue-light) !important; }
.stCheckbox > label {
    font-size: 14.5px !important;
    font-weight: 500 !important;
    padding: 8px 12px !important;
    background: var(--bg);
    border: 1.5px solid var(--border);
    border-radius: 8px;
    margin-bottom: 4px;
    transition: all .15s;
}
.stCheckbox > label:hover { border-color: var(--blue); background: var(--blue-light); }

/* ── Score final ── */
.score-card {
    background: linear-gradient(145deg, #1E3A6E 0%, #2563EB 60%, #3B82F6 100%);
    border-radius: 20px;
    padding: 36px 28px;
    text-align: center;
    box-shadow: var(--shadow-lg);
    margin: 8px 0 20px;
}
.score-emoji { font-size: 3.2rem; margin-bottom: 6px; }
.score-name  { color: rgba(255,255,255,.8); font-size: 1rem; font-weight: 500; margin: 0 0 8px; }
.score-value { color: #fff; font-size: 3rem; font-weight: 900; margin: 0; letter-spacing: -1px; }
.score-pct   { color: rgba(255,255,255,.9); font-size: 1.5rem; font-weight: 700; margin: 2px 0 8px; }
.score-quiz  { color: rgba(255,255,255,.6); font-size: .88rem; margin: 0; }

/* ── Agent result ── */
.agent-row {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: var(--radius);
    padding: 13px 16px;
    margin: 6px 0;
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
    transition: all .15s;
    box-shadow: var(--shadow-sm);
}
.agent-row:hover { border-color: var(--blue); background: var(--blue-light); }
.agent-avatar {
    width: 38px; height: 38px;
    background: var(--blue-mid);
    color: var(--blue);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 14px; flex-shrink: 0;
}
.agent-name { font-weight: 600; font-size: 15px; color: var(--text); }
.agent-mat  { font-size: 12px; color: var(--muted); }

/* ── Badges ── */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 99px;
    font-size: .75rem;
    font-weight: 700;
}
.badge-green  { background: #D1FAE5; color: #065F46; }
.badge-orange { background: #FEF3C7; color: #92400E; }
.badge-blue   { background: var(--blue-mid); color: var(--blue-dark); }
.badge-gray   { background: #F1F5F9; color: #475569; }
.badge-red    { background: #FEE2E2; color: #991B1B; }

/* ── Quiz list card (admin) ── */
.quiz-card {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: var(--radius);
    padding: 16px 18px;
    margin: 8px 0;
    box-shadow: var(--shadow-sm);
}
.quiz-card-title { font-size: 1rem; font-weight: 700; color: var(--text); margin: 0 0 4px; }
.quiz-card-meta  { font-size: .82rem; color: var(--muted); }

/* ── Metric cards ── */
.metric-row { display: flex; gap: 10px; margin: 14px 0; }
.metric {
    flex: 1;
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: var(--radius);
    padding: 14px;
    text-align: center;
    box-shadow: var(--shadow-sm);
}
.metric-val { font-size: 1.7rem; font-weight: 800; color: var(--blue); margin: 0; }
.metric-lbl { font-size: .72rem; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: .06em; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { gap: 6px !important; border-bottom: 2px solid var(--border) !important; }
.stTabs [data-baseweb="tab"] {
    font-family: 'Outfit', sans-serif !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    padding: 10px 16px !important;
    border-radius: 8px 8px 0 0 !important;
}

/* ── Expander ── */
div[data-testid="stExpander"] {
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius) !important;
    margin: 6px 0 !important;
    overflow: hidden !important;
    box-shadow: var(--shadow-sm) !important;
}
div[data-testid="stExpander"] summary {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14.5px !important;
    padding: 14px 16px !important;
}

/* ── Form submit ── */
div[data-testid="stForm"] { border: none !important; padding: 0 !important; background: transparent !important; }

/* ── Alertes ── */
.stAlert { border-radius: var(--radius) !important; font-family: 'Outfit', sans-serif !important; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border-radius: var(--radius) !important; overflow: hidden !important; }

/* ── Caption ── */
.stCaption { font-family: 'Outfit', sans-serif !important; }

/* ── Divider ── */
hr { border: none !important; border-top: 1.5px solid var(--border) !important; margin: 20px 0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Init ──────────────────────────────────────────────────────────────────────
init_db()

try:
    from streamlit_autorefresh import st_autorefresh
    _REFRESH_OK = True
except ImportError:
    _REFRESH_OK = False

_DEFAULTS = {
    "page": "home",
    "current_agent": None,
    "current_quiz": None,
    "quiz_questions": None,
    "quiz_start_time": None,
    "quiz_answers": {},
    "session_id": None,
    "admin_logged": False,
    "quiz_submitted": False,
    "final_score": None,
    "edit_quiz_id": None,
    "adding_q_type": "single",
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


def go(page: str):
    st.session_state.page = page
    st.rerun()


# ═══════════════════════════════════════════════════════════════
#  COMPOSANTS UI RÉUTILISABLES
# ═══════════════════════════════════════════════════════════════

def topbar(title: str, icon: str = "📝", show_back: bool = False, back_page: str = "home"):
    back_btn = (
        f'<button class="topbar-back" onclick="window.location.reload()">← Retour</button>'
        if show_back else ""
    )
    st.markdown(
        f'<div class="topbar">'
        f'<span class="topbar-icon">{icon}</span>'
        f'<span class="topbar-title">{title}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def badge(text: str, color: str = "blue") -> str:
    return f'<span class="badge badge-{color}">{text}</span>'


def metric_row(items: list):
    """items = [(valeur, label), ...]"""
    cols_html = "".join(
        f'<div class="metric"><p class="metric-val">{v}</p><p class="metric-lbl">{l}</p></div>'
        for v, l in items
    )
    st.markdown(f'<div class="metric-row">{cols_html}</div>', unsafe_allow_html=True)


def section(title: str):
    st.markdown(f'<p class="section-label">{title}</p>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  PAGE — HOME
# ═══════════════════════════════════════════════════════════════

def render_home():
    org = f"<br><small style='opacity:.7'>{config.ORG_NAME}</small>" if config.ORG_NAME else ""
    st.markdown(
        f'<div class="hero">'
        f'<div class="hero-icon">📝</div>'
        f'<h1 class="hero-title">{config.APP_TITLE}</h1>'
        f'<p class="hero-sub">{config.APP_SUBTITLE}{org}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("👤  Je suis Agent", use_container_width=True, type="primary"):
            go("agent_search")
    with c2:
        if st.button("⚙️  Administration", use_container_width=True):
            go("admin_login")


# ═══════════════════════════════════════════════════════════════
#  AGENT — Recherche
# ═══════════════════════════════════════════════════════════════

def render_agent_search():
    topbar("Identification", "👤")
    section("Recherchez votre nom")

    query = st.text_input(
        "Nom · Prénom · Matricule",
        placeholder="Ex : Konan, Diallo, AGT001…",
        label_visibility="collapsed",
    )

    if st.button("← Retour à l'accueil", use_container_width=True):
        go("home")

    if not query or len(query.strip()) < 2:
        if query:
            st.caption("Continuez à taper…")
        return

    agents = search_agents(query.strip())

    if not agents:
        st.warning("Aucun agent trouvé. Si votre nom n'apparaît pas, contactez votre superviseur.")
        return

    section(f"{len(agents)} résultat(s)")
    for a in agents:
        initials = (a["nom"][0] + (a["prenom"][0] if a["prenom"] else "")).upper()
        label = f"**{a['nom']}** {a['prenom']}"
        if a["matricule"]:
            label += f"  ·  {a['matricule']}"

        # Affichage HTML de la ligne agent
        st.markdown(
            f'<div class="agent-row" style="pointer-events:none">'
            f'<div class="agent-avatar">{initials}</div>'
            f'<div><div class="agent-name">{a["nom"]} {a["prenom"]}</div>'
            f'<div class="agent-mat">{a["matricule"] or "—"}</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button(f"Choisir  →", key=f"sel_{a['id']}", use_container_width=True, type="primary"):
            st.session_state.current_agent = a
            go("agent_quiz_code")
        st.markdown("")


# ═══════════════════════════════════════════════════════════════
#  AGENT — Code du quiz
# ═══════════════════════════════════════════════════════════════

def render_agent_quiz_code():
    agent = st.session_state.current_agent
    if not agent:
        go("agent_search"); return

    topbar("Accès au Quiz", "📋")

    initials = (agent["nom"][0] + (agent["prenom"][0] if agent["prenom"] else "")).upper()
    st.markdown(
        f'<div class="card" style="display:flex;align-items:center;gap:14px;margin-bottom:20px">'
        f'<div class="agent-avatar" style="width:48px;height:48px;font-size:17px">{initials}</div>'
        f'<div>'
        f'<div style="font-size:1.1rem;font-weight:700">{agent["nom"]} {agent["prenom"]}</div>'
        f'<div style="color:var(--muted);font-size:.85rem">{agent["matricule"] or "Agent"}</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    section("Entrez le code communiqué par votre superviseur")
    code = st.text_input("Code du quiz", placeholder="Ex : QZ001", max_chars=20,
                          label_visibility="collapsed")

    c1, c2 = st.columns([1, 2])
    with c1:
        if st.button("← Retour", use_container_width=True):
            go("agent_search")
    with c2:
        if st.button("▶  Commencer le quiz", type="primary", use_container_width=True):
            _start_quiz(agent, code)


def _start_quiz(agent, code):
    if not code.strip():
        st.warning("Veuillez saisir un code.")
        return
    quiz = get_quiz_by_code(code.strip())
    if not quiz:
        st.error("Code incorrect ou quiz désactivé.")
        return
    questions = get_questions(quiz["id"])
    if not questions:
        st.error("Ce quiz ne contient pas encore de questions.")
        return
    if session_already_completed(agent["id"], quiz["id"]):
        st.warning("Vous avez déjà soumis ce quiz. Contactez votre superviseur.")
        return
    max_score = sum(q["points"] for q in questions)
    st.session_state.current_quiz = quiz
    st.session_state.quiz_questions = questions
    st.session_state.quiz_start_time = time.time()
    st.session_state.quiz_answers = {}
    st.session_state.quiz_submitted = False
    st.session_state.session_id = create_session(agent["id"], quiz["id"], max_score)
    go("agent_quiz")


# ═══════════════════════════════════════════════════════════════
#  AGENT — Passer le quiz
# ═══════════════════════════════════════════════════════════════

def _calculate_score(questions, answers: dict):
    score, records = 0.0, []
    for q in questions:
        qid = q["id"]
        resp = answers.get(qid, "")
        ok = 0

        if q["type"] == "single":
            correct = [o["id"] for o in q["options"] if o["is_correct"]]
            ok = 1 if resp in correct else 0

        elif q["type"] == "multiple":
            correct = set(o["id"] for o in q["options"] if o["is_correct"])
            given = set(resp) if isinstance(resp, list) else set()
            ok = 1 if given == correct and correct else 0

        elif q["type"] == "numeric":
            try:
                exp = float(q["reponse_correcte_num"]) if q["reponse_correcte_num"] is not None else None
                giv = float(str(resp).replace(",", ".")) if str(resp).strip() else None
                ok = 1 if (exp is not None and giv is not None and abs(giv - exp) < 0.01) else 0
            except Exception:
                ok = 0

        elif q["type"] == "text":
            raw = (q.get("reponse_correcte_txt") or "").strip()
            if raw:
                acceptable = [a.lower().strip() for a in raw.split("|") if a.strip()]
                ok = 1 if str(resp).lower().strip() in acceptable else 0
            else:
                ok = 1  # question ouverte

        if ok:
            score += q["points"]
        records.append({
            "question_id": qid,
            "reponse": json.dumps(resp, ensure_ascii=False) if isinstance(resp, list) else str(resp),
            "is_correct": ok,
        })
    return score, records


def _do_submit():
    if st.session_state.quiz_submitted:
        return
    q_list = st.session_state.quiz_questions
    score, records = _calculate_score(q_list, st.session_state.quiz_answers)
    submit_session(st.session_state.session_id, score, records)
    st.session_state.final_score = {"score": score, "max_score": sum(q["points"] for q in q_list)}
    st.session_state.quiz_submitted = True


def render_agent_quiz():
    if st.session_state.quiz_submitted:
        go("agent_result"); return

    quiz = st.session_state.current_quiz
    questions = st.session_state.quiz_questions
    agent = st.session_state.current_agent

    if _REFRESH_OK:
        st_autorefresh(interval=1000, key="quiz_refresh")

    elapsed = time.time() - st.session_state.quiz_start_time
    total = quiz["duree_minutes"] * 60
    remaining = max(0, total - elapsed)

    if remaining <= 0:
        _do_submit()
        st.session_state.page = "agent_result"
        st.rerun(); return

    mins, secs = int(remaining // 60), int(remaining % 60)
    if remaining > 300:
        tcls = "timer-normal"
        tlbl = "Temps restant"
    elif remaining > 60:
        tcls = "timer-warning"
        tlbl = "⚠️ Moins de 5 minutes !"
    else:
        tcls = "timer-danger"
        tlbl = "🚨 Moins d'une minute !"

    st.markdown(
        f'<div class="timer-wrap {tcls}">'
        f'<p class="timer-time">{mins:02d}:{secs:02d}</p>'
        f'<p class="timer-label">{tlbl}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    answered = sum(
        1 for v in st.session_state.quiz_answers.values()
        if v not in ("", [], None)
    )
    pct = answered / len(questions) if questions else 0

    st.markdown(
        f'<div class="prog-wrap">'
        f'<div class="prog-meta"><span>{quiz["titre"]}</span>'
        f'<span>{answered} / {len(questions)} répondue(s)</span></div>'
        f'<div class="prog-bg"><div class="prog-fill" style="width:{pct*100:.0f}%"></div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    TYPE_ICONS = {"single": "⭕", "multiple": "☑️", "numeric": "🔢", "text": "📝"}
    TYPE_HINTS = {
        "single": "Une seule réponse",
        "multiple": "Plusieurs réponses possibles",
        "numeric": "Entrez un nombre",
        "text": "Réponse libre",
    }

    for i, q in enumerate(questions):
        qid = q["id"]
        pts_lbl = f"{q['points']:.0f} pt" + ("s" if q["points"] != 1 else "")

        st.markdown(
            f'<div class="q-card">'
            f'<div class="q-header">'
            f'<span class="q-num">Q{i+1}</span>'
            f'<span class="q-type">{TYPE_ICONS[q["type"]]} {TYPE_HINTS[q["type"]]}</span>'
            f'<span class="q-pts">{pts_lbl}</span>'
            f'</div>'
            f'<p class="q-text">{q["texte"]}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

        if q["type"] == "single":
            opts = q["options"]
            cur_id = st.session_state.quiz_answers.get(qid)
            cur_idx = next((j for j, o in enumerate(opts) if o["id"] == cur_id), None)
            sel = st.radio(
                "Réponse",
                range(len(opts)),
                format_func=lambda x, _o=opts: _o[x]["texte"],
                index=cur_idx,
                key=f"q_{qid}",
                label_visibility="collapsed",
            )
            if sel is not None:
                st.session_state.quiz_answers[qid] = opts[sel]["id"]

        elif q["type"] == "multiple":
            cur = st.session_state.quiz_answers.get(qid, [])
            selected = []
            for o in q["options"]:
                checked = st.checkbox(o["texte"], value=(o["id"] in cur), key=f"q_{qid}_{o['id']}")
                if checked:
                    selected.append(o["id"])
            st.session_state.quiz_answers[qid] = selected

        elif q["type"] == "numeric":
            val = st.session_state.quiz_answers.get(qid, "")
            nv = st.text_input("Nombre", value=str(val) if val != "" else "",
                                key=f"q_{qid}", placeholder="0", label_visibility="collapsed")
            st.session_state.quiz_answers[qid] = nv

        elif q["type"] == "text":
            val = st.session_state.quiz_answers.get(qid, "")
            tv = st.text_area("Texte", value=val, key=f"q_{qid}",
                               height=80, placeholder="Votre réponse…", label_visibility="collapsed")
            st.session_state.quiz_answers[qid] = tv

        st.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        f'<p style="text-align:center;color:var(--muted);font-size:.85rem;margin-bottom:12px">'
        f'Les questions sans réponse seront comptées comme incorrectes.</p>',
        unsafe_allow_html=True,
    )
    if st.button("✅  Soumettre mes réponses", type="primary", use_container_width=True):
        _do_submit()
        go("agent_result")


# ═══════════════════════════════════════════════════════════════
#  AGENT — Résultat
# ═══════════════════════════════════════════════════════════════

def render_agent_result():
    res = st.session_state.final_score
    quiz = st.session_state.current_quiz
    agent = st.session_state.current_agent
    if not res or not agent or not quiz:
        go("home"); return

    score, max_sc = res["score"], res["max_score"]
    pct = (score / max_sc * 100) if max_sc > 0 else 0

    if pct >= 80:
        emoji, msg = "🏆", ("Excellent ! Félicitations !", "success")
    elif pct >= 60:
        emoji, msg = "👍", ("Bon résultat. Continuez vos efforts !", "info")
    else:
        emoji, msg = "📚", ("Il faut encore travailler ce sujet. Courage !", "warning")

    st.markdown(
        f'<div class="score-card">'
        f'<div class="score-emoji">{emoji}</div>'
        f'<p class="score-name">{agent["nom"]} {agent["prenom"]}</p>'
        f'<p class="score-value">{score:.1f} / {max_sc:.1f}</p>'
        f'<p class="score-pct">{pct:.0f} %</p>'
        f'<p class="score-quiz">{quiz["titre"]}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if msg[1] == "success":
        st.success(msg[0])
    elif msg[1] == "info":
        st.info(msg[0])
    else:
        st.warning(msg[0])

    st.markdown(
        f'<p style="text-align:center;color:var(--muted);font-size:.82rem;margin:8px 0 16px">'
        f'Résultat enregistré le {datetime.now().strftime("%d/%m/%Y à %H:%M")}</p>',
        unsafe_allow_html=True,
    )
    if st.button("🏠  Retour à l'accueil", use_container_width=True):
        for k in ("current_quiz", "quiz_questions", "quiz_start_time",
                  "quiz_answers", "session_id", "quiz_submitted", "final_score"):
            st.session_state[k] = _DEFAULTS[k]
        go("home")


# ═══════════════════════════════════════════════════════════════
#  ADMIN — Connexion
# ═══════════════════════════════════════════════════════════════

def render_admin_login():
    if st.session_state.admin_logged:
        go("admin_dashboard"); return

    topbar("Administration", "⚙️")

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 🔐 Connexion administrateur")
    pwd = st.text_input("Mot de passe", type="password", label_visibility="collapsed",
                         placeholder="Mot de passe…")
    c1, c2 = st.columns([1, 2])
    with c1:
        if st.button("← Retour", use_container_width=True):
            go("home")
    with c2:
        if st.button("Se connecter", type="primary", use_container_width=True):
            if pwd == config.ADMIN_PASSWORD:
                st.session_state.admin_logged = True
                go("admin_dashboard")
            else:
                st.error("Mot de passe incorrect.")
    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  ADMIN — Dashboard
# ═══════════════════════════════════════════════════════════════

def render_admin_dashboard():
    if not st.session_state.admin_logged:
        go("admin_login"); return

    topbar(f"Administration — {config.APP_TITLE}", "⚙️")

    all_agents = get_all_agents()
    all_quizzes = get_all_quizzes()
    all_results = get_results()
    metric_row([
        (len(all_agents), "Agents"),
        (sum(1 for a in all_agents if a["published"]), "Publiés"),
        (len(all_quizzes), "Quiz"),
        (len(all_results), "Résultats"),
    ])

    t_agents, t_quiz, t_results = st.tabs(["👥 Agents", "📝 Quiz", "📊 Résultats"])
    with t_agents:
        _tab_agents()
    with t_quiz:
        _tab_quizzes()
    with t_results:
        _tab_results()

    st.markdown("---")
    if st.button("🚪  Déconnexion", use_container_width=True):
        st.session_state.admin_logged = False
        go("home")


# ── Agents tab ────────────────────────────────────────────────

def _normalize_df(df: pd.DataFrame):
    df.columns = [str(c).lower().strip() for c in df.columns]
    nom = next((c for c in ["nom", "name", "lastname", "noms"] if c in df.columns), None)
    if not nom:
        return None
    pre = next((c for c in ["prenom", "prénom", "firstname", "prenoms"] if c in df.columns), None)
    mat = next((c for c in ["matricule", "id", "code", "identifiant"] if c in df.columns), None)
    out = pd.DataFrame()
    out["nom"] = df[nom]
    out["prenom"] = df[pre] if pre else ""
    out["matricule"] = df[mat] if mat else ""
    return out


def _tab_agents():
    sub_add, sub_import, sub_list = st.tabs(["✏️ Ajouter", "📥 Importer", "📋 Liste"])

    with sub_add:
        with st.form("form_add_agent", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1: nom = st.text_input("Nom *")
            with c2: pre = st.text_input("Prénom")
            with c3: mat = st.text_input("Matricule")
            if st.form_submit_button("Ajouter l'agent", type="primary", use_container_width=True):
                if not nom.strip():
                    st.error("Le nom est obligatoire.")
                elif add_agent_manual(nom.strip(), pre.strip(), mat.strip()):
                    st.success(f"Agent {nom} ajouté.")
                    st.rerun()
                else:
                    st.warning("Cet agent existe déjà.")

    with sub_import:
        st.markdown("**Fichier CSV ou Excel**")
        st.caption("Colonnes : `nom`, `prenom` (optionnel), `matricule` (optionnel)")
        up = st.file_uploader("Fichier", type=["csv", "xlsx", "xls"], label_visibility="collapsed")
        if up:
            try:
                df_raw = pd.read_csv(up) if up.name.lower().endswith(".csv") else pd.read_excel(up)
                df = _normalize_df(df_raw)
                if df is None:
                    st.error("Colonne 'nom' introuvable.")
                else:
                    st.dataframe(df.head(5), use_container_width=True)
                    st.caption(f"{len(df)} agent(s) dans le fichier")
                    if st.button("✅  Importer", type="primary", use_container_width=True):
                        n = upsert_agents(df)
                        st.success(f"{n} agent(s) importé(s).")
                        st.rerun()
            except Exception as e:
                st.error(f"Erreur : {e}")

        st.markdown("---")
        st.markdown("**Google Sheets**")
        st.caption("Classeur partagé publiquement · *Partager → Toute personne avec le lien*")
        gs = st.text_input("URL Google Sheets", placeholder="https://docs.google.com/spreadsheets/d/…",
                            label_visibility="collapsed")
        if st.button("Importer depuis Google Sheets", use_container_width=True):
            _import_gsheets(gs)

    with sub_list:
        agents = get_all_agents()
        if not agents:
            st.info("Aucun agent dans la base.")
            return
        nb_pub = sum(1 for a in agents if a["published"])
        st.markdown(
            f'<p style="color:var(--muted);font-size:.88rem;margin-bottom:12px">'
            f'<b>{len(agents)}</b> agent(s) · '
            f'{badge(f"{nb_pub} publié(s)", "green")} &nbsp;'
            f'{badge(f"{len(agents)-nb_pub} brouillon(s)", "orange")}</p>',
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Publier tous", use_container_width=True, type="primary"):
                publish_all_agents(); st.rerun()
        with c2:
            if st.button("⛔ Dépublier tous", use_container_width=True):
                unpublish_all_agents(); st.rerun()
        st.markdown("---")
        filtre = st.text_input("🔍 Filtrer", placeholder="Nom, matricule…",
                                key="af", label_visibility="collapsed")
        filtered = [
            a for a in agents
            if not filtre or filtre.lower() in f"{a['nom']} {a['prenom']} {a['matricule']}".lower()
        ]
        for a in filtered:
            c1, c2, c3 = st.columns([4, 1.5, 0.7])
            with c1:
                pub_badge = badge("✓ Publié", "green") if a["published"] else badge("Brouillon", "orange")
                init = (a["nom"][0] + (a["prenom"][0] if a["prenom"] else "")).upper()
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:10px;padding:4px 0">'
                    f'<div class="agent-avatar" style="width:32px;height:32px;font-size:12px;flex-shrink:0">{init}</div>'
                    f'<div><span style="font-weight:600">{a["nom"]} {a["prenom"]}</span>'
                    f'<span style="color:var(--muted);font-size:.8rem;margin-left:6px">{a["matricule"] or ""}</span><br>'
                    f'{pub_badge}</div></div>',
                    unsafe_allow_html=True,
                )
            with c2:
                lbl = "Dépublier" if a["published"] else "Publier"
                if st.button(lbl, key=f"pub_{a['id']}", use_container_width=True):
                    set_agent_published(a["id"], 0 if a["published"] else 1)
                    st.rerun()
            with c3:
                if st.button("🗑", key=f"da_{a['id']}", use_container_width=True):
                    delete_agent(a["id"]); st.rerun()


def _import_gsheets(url: str):
    if not url.strip():
        st.warning("Collez une URL Google Sheets.")
        return
    try:
        m = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", url)
        if not m:
            st.error("URL invalide.")
            return
        sid = m.group(1)
        gid_m = re.search(r"gid=(\d+)", url)
        gid = gid_m.group(1) if gid_m else "0"
        csv_url = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid={gid}"
        r = requests.get(csv_url, timeout=15)
        r.raise_for_status()
        df_raw = pd.read_csv(io.StringIO(r.text))
        df = _normalize_df(df_raw)
        if df is None:
            st.error("Colonne 'nom' introuvable.")
            return
        n = upsert_agents(df)
        st.success(f"{n} agent(s) importé(s) depuis Google Sheets.")
        st.rerun()
    except Exception as e:
        st.error(f"Erreur d'importation : {e}")


# ── Quiz tab ──────────────────────────────────────────────────

def _tab_quizzes():
    if st.button("➕  Créer un nouveau quiz", type="primary", use_container_width=True):
        st.session_state.edit_quiz_id = None
        go("admin_quiz_edit")
    st.markdown("---")
    quizzes = get_all_quizzes()
    if not quizzes:
        st.info("Aucun quiz. Cliquez sur « Créer » pour commencer.")
        return
    for quiz in quizzes:
        nb_q = len(get_questions(quiz["id"]))
        status = badge("Actif", "green") if quiz["actif"] else badge("Inactif", "gray")
        with st.expander(f"{'🟢' if quiz['actif'] else '⚫'} {quiz['titre']}  ·  `{quiz['code']}`"):
            duree_badge = badge(f"{quiz['duree_minutes']} min", "blue")
            nb_q_badge  = badge(f"{nb_q} question(s)", "gray")
            st.markdown(
                f"{status} &nbsp; {duree_badge} &nbsp; {nb_q_badge}",
                unsafe_allow_html=True,
            )
            if quiz["description"]:
                st.caption(quiz["description"])
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("✏️ Modifier", key=f"eq_{quiz['id']}", use_container_width=True):
                    st.session_state.edit_quiz_id = quiz["id"]
                    go("admin_quiz_edit")
            with c2:
                lbl = "🔴 Désactiver" if quiz["actif"] else "🟢 Activer"
                if st.button(lbl, key=f"tq_{quiz['id']}", use_container_width=True):
                    update_quiz(quiz["id"], quiz["titre"], quiz["code"],
                                quiz["duree_minutes"], quiz["description"], 0 if quiz["actif"] else 1)
                    st.rerun()
            with c3:
                if st.button("🗑 Supprimer", key=f"dq_{quiz['id']}", use_container_width=True):
                    delete_quiz(quiz["id"]); st.rerun()


# ── Résultats tab ─────────────────────────────────────────────

def _tab_results():
    quizzes = get_all_quizzes()
    opts = {0: "— Tous les quiz —"}
    opts.update({q["id"]: f"{q['titre']}  ({q['code']})" for q in quizzes})

    sel = st.selectbox("Quiz", list(opts.keys()), format_func=lambda x: opts[x],
                        label_visibility="collapsed")
    results = get_results(sel if sel else None)

    if not results:
        st.info("Aucun résultat disponible.")
        return

    df = pd.DataFrame(results)
    df["pct"] = (df["score"] / df["max_score"] * 100).round(1)
    df["agent"] = df["nom"] + " " + df["prenom"]

    metric_row([
        (len(df), "Participants"),
        (f"{df['pct'].mean():.1f}%", "Moyenne"),
        (f"{df['pct'].max():.1f}%", "Meilleur"),
        (f"{df['pct'].min():.1f}%", "Minimum"),
    ])

    display = df[["agent", "matricule", "quiz_titre", "score", "max_score", "pct", "completed_at"]].copy()
    display.columns = ["Agent", "Matricule", "Quiz", "Score", "Sur", "%", "Date"]
    st.dataframe(display, use_container_width=True)

    # Export Excel
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        display.to_excel(w, index=False, sheet_name="Résultats")
        ws = w.sheets["Résultats"]
        for col in ws.columns:
            ml = max((len(str(c.value)) for c in col if c.value), default=10)
            ws.column_dimensions[col[0].column_letter].width = min(ml + 4, 40)
    buf.seek(0)
    fname = f"resultats_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    st.download_button("📥  Télécharger Excel", data=buf.getvalue(),
                        file_name=fname,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True)


# ═══════════════════════════════════════════════════════════════
#  ADMIN — Éditeur de Quiz
# ═══════════════════════════════════════════════════════════════

_TYPE_LABELS = {
    "single":   "⭕  Choix unique",
    "multiple": "☑️  Choix multiple",
    "numeric":  "🔢  Valeur numérique",
    "text":     "📝  Texte libre",
}


def render_admin_quiz_edit():
    if not st.session_state.admin_logged:
        go("admin_login"); return

    quiz_id = st.session_state.edit_quiz_id
    is_new = quiz_id is None
    existing = get_quiz(quiz_id) if not is_new else None

    topbar("Nouveau Quiz" if is_new else "Modifier le Quiz", "📝")

    # ── Infos de base ──
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### Informations du quiz")
    with st.form("form_quiz_info"):
        titre = st.text_input("Titre *", value=existing["titre"] if existing else "",
                               placeholder="Ex : Évaluation MICS7 — Module Femme")
        c1, c2 = st.columns(2)
        with c1:
            code = st.text_input("Code d'accès *",
                                  value=existing["code"] if existing else "",
                                  placeholder="Ex : QZ001",
                                  max_chars=20,
                                  help="Code que les agents saisissent pour accéder au quiz.")
        with c2:
            duree = st.number_input("Durée (minutes)", min_value=1, max_value=600,
                                     value=existing["duree_minutes"] if existing else 30)
        desc = st.text_area("Description (optionnelle)",
                             value=existing["description"] if existing else "",
                             height=68, placeholder="Contexte, consignes générales…")
        if st.form_submit_button("💾  Enregistrer", type="primary", use_container_width=True):
            if not titre.strip() or not code.strip():
                st.error("Titre et code sont obligatoires.")
            else:
                if is_new:
                    try:
                        nid = create_quiz(titre.strip(), code.strip(), int(duree), desc.strip())
                        st.session_state.edit_quiz_id = nid
                        st.success("Quiz créé ! Ajoutez vos questions ci-dessous.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur — le code existe peut-être déjà : {e}")
                else:
                    update_quiz(quiz_id, titre.strip(), code.strip(), int(duree), desc.strip(), existing["actif"])
                    st.success("Quiz mis à jour.")
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    cur_id = st.session_state.edit_quiz_id
    if not cur_id:
        if st.button("← Retour", use_container_width=True):
            go("admin_dashboard")
        return

    # ── Questions existantes ──
    questions = get_questions(cur_id)
    section(f"Questions ({len(questions)})")

    if questions:
        for i, q in enumerate(questions):
            with st.expander(
                f"Q{i+1}  ·  {_TYPE_LABELS[q['type']]}  ·  {q['texte'][:52]}{'…' if len(q['texte'])>52 else ''}"
            ):
                if q["type"] in ("single", "multiple"):
                    for o in q["options"]:
                        icon = "✅" if o["is_correct"] else "◻️"
                        st.markdown(f"{icon} {o['texte']}")
                elif q["type"] == "numeric":
                    st.markdown(f"**Réponse attendue :** `{q['reponse_correcte_num']}`")
                elif q["type"] == "text":
                    st.markdown(f"**Réponses acceptées :** `{q['reponse_correcte_txt']}`")
                st.markdown(f"*{q['points']} point(s)*")
                if st.button("🗑  Supprimer cette question", key=f"dq_{q['id']}"):
                    delete_question(q["id"])
                    reorder_questions(cur_id)
                    st.rerun()
    else:
        st.info("Aucune question pour l'instant.")

    # ── Ajouter une question ──
    section("Ajouter une question")
    q_type = st.selectbox("Type", list(_TYPE_LABELS.keys()),
                           format_func=lambda x: _TYPE_LABELS[x],
                           key="adding_q_type", label_visibility="collapsed")

    with st.form("form_add_q", clear_on_submit=True):
        q_txt = st.text_area("Texte de la question *", height=88,
                              placeholder="Saisissez votre question ici…")
        q_pts = st.number_input("Points", min_value=0.5, max_value=20.0, value=1.0, step=0.5)
        opts_data = []

        if q_type in ("single", "multiple"):
            st.markdown("**Options** — cochez ✅ la/les bonne(s) réponse(s)")
            for j in range(6):
                c1, c2 = st.columns([5, 1])
                with c1:
                    ot = st.text_input(f"Option {j+1}", key=f"ot_{j}",
                                        label_visibility="collapsed",
                                        placeholder=f"Option {j+1}…")
                with c2:
                    oc = st.checkbox("✅", key=f"oc_{j}")
                if ot.strip():
                    opts_data.append({"texte": ot.strip(), "is_correct": oc})

        elif q_type == "numeric":
            c_num = st.number_input("Réponse numérique correcte", value=0.0, format="%.4f")

        elif q_type == "text":
            c_txt = st.text_input(
                "Réponse(s) correcte(s)",
                placeholder="réponse1 | réponse2  (séparées par |, laisser vide = question ouverte)",
            )

        if st.form_submit_button("➕  Ajouter la question", type="primary", use_container_width=True):
            err = None
            if not q_txt.strip():
                err = "Le texte est obligatoire."
            elif q_type in ("single", "multiple"):
                if not opts_data:
                    err = "Ajoutez au moins une option non vide."
                elif not any(o["is_correct"] for o in opts_data):
                    err = "Cochez au moins une bonne réponse."
                elif q_type == "single" and sum(o["is_correct"] for o in opts_data) > 1:
                    err = "Choix unique : une seule bonne réponse."
            if err:
                st.error(err)
            else:
                ordre = len(questions)
                if q_type in ("single", "multiple"):
                    add_question(cur_id, q_txt.strip(), q_type, ordre, q_pts, options=opts_data)
                elif q_type == "numeric":
                    add_question(cur_id, q_txt.strip(), q_type, ordre, q_pts, reponse_correcte_num=c_num)
                elif q_type == "text":
                    add_question(cur_id, q_txt.strip(), q_type, ordre, q_pts,
                                 reponse_correcte_txt=(c_txt.strip() if c_txt else ""))
                st.success("Question ajoutée ✓")
                st.rerun()

    st.markdown("---")
    if st.button("← Retour au dashboard", use_container_width=True):
        go("admin_dashboard")


# ═══════════════════════════════════════════════════════════════
#  ROUTEUR
# ═══════════════════════════════════════════════════════════════

_ROUTES = {
    "home":            render_home,
    "agent_search":    render_agent_search,
    "agent_quiz_code": render_agent_quiz_code,
    "agent_quiz":      render_agent_quiz,
    "agent_result":    render_agent_result,
    "admin_login":     render_admin_login,
    "admin_dashboard": render_admin_dashboard,
    "admin_quiz_edit": render_admin_quiz_edit,
}

_page = st.session_state.get("page", "home")
_fn = _ROUTES.get(_page)
if _fn:
    _fn()
else:
    go("home")
