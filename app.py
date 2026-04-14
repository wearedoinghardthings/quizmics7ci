"""
app.py — QuizAgent CI
"""
import streamlit as st
import pandas as pd
import json, time, io, re, requests
from datetime import datetime, timedelta

import config, hashlib
from functools import lru_cache
from database import (
    init_db, search_agents, get_all_agents, upsert_agents,
    set_agent_published, publish_all_agents, unpublish_all_agents,
    get_agent_by_id, get_session_by_id, delete_agent, add_agent_manual,
    get_quiz_by_code, get_all_quizzes, get_quiz, create_quiz, update_quiz, delete_quiz,
    get_questions, add_question, delete_question, reorder_questions,
    create_session, save_quiz_progress, get_incomplete_session,
    submit_session, get_results, session_already_completed, get_stats,
)

st.set_page_config(page_title=config.APP_TITLE, page_icon="📝",
                   layout="centered", initial_sidebar_state="collapsed")

# ═══════════════════════════════════════════════════════════════
#  CSS + DESIGN SYSTEM
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box}
html,body,[class*="css"],input,textarea,button,select,.stMarkdown p,label,p,span,div{font-family:'Plus Jakarta Sans',sans-serif!important}
#MainMenu,footer,header,.stDeployButton{display:none!important}
.main,.main>div,section.main,.appview-container,.block-container{overflow:visible!important}
.block-container{padding:0 0 5rem!important;max-width:640px!important;margin:0 auto!important}
:root{
  --B:#2563EB;--Bd:#1E40AF;--Bx:#1E3A8A;--Bl:#EFF6FF;--Bm:#DBEAFE;
  --G:#10B981;--Gd:#059669;--Gl:#D1FAE5;
  --O:#F59E0B;--Od:#D97706;--Ol:#FEF3C7;
  --R:#EF4444;--Rd:#DC2626;--Rl:#FEE2E2;
  --P:#8B5CF6;--Pl:#EDE9FE;
  --bg:#F1F5FD;--sur:#FFFFFF;--bor:#E4EAF5;
  --txt:#0F1729;--mu:#64748B;--mu2:#94A3B8;
  --r:14px;--r2:10px;
  --sh:0 1px 3px rgba(15,23,42,.06),0 4px 16px rgba(15,23,42,.04);
  --shm:0 4px 20px rgba(15,23,42,.1),0 1px 6px rgba(15,23,42,.06);
  --shb:0 8px 32px rgba(37,99,235,.2),0 2px 8px rgba(37,99,235,.1)
}

/* ══ TOPBAR ══ */
.topbar{
  background:linear-gradient(135deg,var(--Bx) 0%,var(--Bd) 100%);
  margin:0 -1rem 1.8rem -1rem;
  padding:16px 22px;
  display:flex;align-items:center;gap:12px;
  box-shadow:0 2px 20px rgba(30,58,138,.25);
}
.topbar-icon{font-size:1.3rem}
.topbar-title{color:#fff;font-size:1.05rem;font-weight:700;letter-spacing:-.01em}
.topbar-sub{color:rgba(255,255,255,.55);font-size:.82rem;margin-left:auto}

/* ══ HERO HOME ══ */
.hero{
  background:linear-gradient(145deg,var(--Bx) 0%,#1D4ED8 50%,#3B82F6 100%);
  border-radius:22px;padding:44px 28px 40px;text-align:center;
  margin:1rem 1rem 1.5rem;
  box-shadow:var(--shb);
  position:relative;overflow:hidden;
}
.hero::before{
  content:'';position:absolute;top:-60px;right:-60px;
  width:240px;height:240px;border-radius:50%;
  background:rgba(255,255,255,.06);
}
.hero::after{
  content:'';position:absolute;bottom:-80px;left:-40px;
  width:200px;height:200px;border-radius:50%;
  background:rgba(255,255,255,.04);
}
.hero-icon{font-size:3rem;margin-bottom:10px;position:relative;z-index:1}
.hero-title{color:#fff;font-size:2rem;font-weight:900;margin:0 0 6px;letter-spacing:-.04em;position:relative;z-index:1}
.hero-sub{color:rgba(255,255,255,.7);font-size:1rem;margin:0;font-weight:400;position:relative;z-index:1}
.hero-org{color:rgba(255,255,255,.5);font-size:.85rem;margin-top:4px;position:relative;z-index:1}

/* ══ BOUTONS ══ */
.stButton>button{
  font-family:'Plus Jakarta Sans',sans-serif!important;
  font-weight:700!important;font-size:15px!important;
  border-radius:var(--r2)!important;
  padding:13px 22px!important;width:100%!important;
  transition:all .18s cubic-bezier(.4,0,.2,1)!important;
  min-height:50px!important;letter-spacing:-.01em!important;
}
.stButton>button[kind="primary"]{
  background:linear-gradient(135deg,var(--B) 0%,var(--Bd) 100%)!important;
  border:none!important;color:#fff!important;
  box-shadow:0 4px 14px rgba(37,99,235,.35)!important;
}
.stButton>button[kind="primary"]:hover{
  background:linear-gradient(135deg,#1D4ED8 0%,var(--Bx) 100%)!important;
  box-shadow:0 6px 20px rgba(37,99,235,.45)!important;
  transform:translateY(-1px)!important;
}
.stButton>button[kind="primary"]:active{transform:translateY(0)!important}
.stButton>button:not([kind="primary"]){
  background:var(--sur)!important;
  border:2px solid var(--bor)!important;
  color:var(--txt)!important;
  box-shadow:var(--sh)!important;
}
.stButton>button:not([kind="primary"]):hover{
  border-color:var(--B)!important;color:var(--B)!important;
  background:var(--Bl)!important;
}

/* ══ INPUTS ══ */
.stTextInput>div>div>input,.stTextArea>div>div>textarea,.stNumberInput>div>div>input{
  font-family:'Plus Jakarta Sans',sans-serif!important;
  font-size:15px!important;border-radius:var(--r2)!important;
  border:2px solid var(--bor)!important;padding:12px 15px!important;
  background:var(--sur)!important;color:var(--txt)!important;
  transition:border-color .15s,box-shadow .15s!important;
}
.stTextInput>div>div>input:focus,.stTextArea>div>div>textarea:focus{
  border-color:var(--B)!important;
  box-shadow:0 0 0 4px rgba(37,99,235,.1)!important;outline:none!important;
}
.stTextInput label,.stTextArea label,.stSelectbox label,.stNumberInput label{
  font-size:11.5px!important;font-weight:700!important;color:var(--mu)!important;
  text-transform:uppercase!important;letter-spacing:.08em!important;margin-bottom:5px!important;
}
.stSelectbox>div>div{
  border-radius:var(--r2)!important;border:2px solid var(--bor)!important;
  font-size:15px!important;
}

/* ══ TIMER FIXE ══ */
#quiz-timer-bar{
  position:fixed!important;top:0!important;left:0!important;right:0!important;
  z-index:99999!important;
  padding:8px 1rem 6px!important;
  background:rgba(241,245,253,.96)!important;
  backdrop-filter:blur(16px)!important;
  -webkit-backdrop-filter:blur(16px)!important;
  border-bottom:1px solid var(--bor)!important;
  box-shadow:0 2px 16px rgba(15,23,42,.08)!important;
}
#quiz-timer-bar .inner{max-width:640px;margin:0 auto}
.tbox{border-radius:var(--r2);padding:12px 20px;display:flex;align-items:center;gap:14px}
.tn{background:linear-gradient(135deg,var(--Bx),var(--B));box-shadow:0 3px 14px rgba(37,99,235,.3)}
.tw{background:linear-gradient(135deg,#92400E,var(--O));box-shadow:0 3px 14px rgba(245,158,11,.3)}
.td{background:linear-gradient(135deg,#7F1D1D,var(--R));box-shadow:0 3px 14px rgba(239,68,68,.35);animation:pulse .65s infinite}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.85;transform:scale(1.01)}}
.ttime{color:#fff;font-size:2.1rem;font-weight:900;letter-spacing:4px;margin:0;line-height:1;font-variant-numeric:tabular-nums}
.tlbl{color:rgba(255,255,255,.75);font-size:.72rem;font-weight:700;margin:4px 0 0;text-transform:uppercase;letter-spacing:.1em}
.ticon{font-size:1.7rem}

/* ══ PROGRESSION ══ */
.prog{margin:8px 0 16px;padding:0 1rem}
.prog-row{display:flex;justify-content:space-between;font-size:.83rem;color:var(--mu);font-weight:600;margin-bottom:7px}
.prog-bg{background:var(--Bm);border-radius:99px;height:7px}
.prog-fill{background:linear-gradient(90deg,var(--B),#60A5FA);height:7px;border-radius:99px;transition:width .4s cubic-bezier(.4,0,.2,1)}

/* ══ QUESTION CARD ══ */
.qcard{
  background:var(--sur);
  border:1.5px solid var(--bor);
  border-left:4px solid var(--B);
  border-radius:0 var(--r) var(--r) 0;
  padding:16px 18px 8px;
  box-shadow:var(--sh);
  margin:14px 1rem 0;
  transition:border-color .15s;
}
.qcard:focus-within{border-color:var(--B);box-shadow:var(--shm)}
.qmeta{display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap}
.qnum{
  background:var(--B);color:#fff;
  font-size:.72rem;font-weight:800;padding:3px 10px;border-radius:99px;
}
.qtype{color:var(--mu);font-size:.76rem;font-weight:600}
.qpts{
  background:linear-gradient(135deg,#F1F5F9,#E8EDF8);
  color:var(--mu);font-size:.72rem;font-weight:700;
  padding:3px 10px;border-radius:99px;margin-left:auto;
}
.qtxt{font-size:15px;font-weight:700;color:var(--txt);margin:0 0 12px;line-height:1.5}

/* ══ RADIO / CHECKBOX ══ */
.stRadio>div{gap:6px!important}
.stRadio>div>label{
  background:var(--bg)!important;border:2px solid var(--bor)!important;
  border-radius:var(--r2)!important;padding:12px 15px!important;
  font-size:14.5px!important;font-weight:500!important;min-height:48px!important;
  cursor:pointer!important;transition:all .15s!important;
  display:flex!important;align-items:center!important;
}
.stRadio>div>label:hover{border-color:var(--B)!important;background:var(--Bl)!important;color:var(--Bd)!important}
div[data-testid="stCheckbox"] label{
  background:var(--bg);border:2px solid var(--bor);
  border-radius:var(--r2);padding:12px 15px;
  font-size:14.5px!important;font-weight:500!important;min-height:48px;
  margin-bottom:6px;display:flex;align-items:center;
  transition:all .15s;cursor:pointer;
}
div[data-testid="stCheckbox"] label:hover{border-color:var(--B);background:var(--Bl)}

/* ══ SCORE FINAL ══ */
.scard{
  background:linear-gradient(145deg,var(--Bx) 0%,#1D4ED8 50%,#3B82F6 100%);
  border-radius:22px;padding:36px 28px;text-align:center;
  box-shadow:var(--shb);margin:1rem 1rem 1.5rem;
  position:relative;overflow:hidden;
}
.scard::before{content:'';position:absolute;top:-50px;right:-50px;width:200px;height:200px;border-radius:50%;background:rgba(255,255,255,.06)}
.se{font-size:3.2rem;margin-bottom:6px;position:relative;z-index:1}
.sn{color:rgba(255,255,255,.75);font-size:.95rem;font-weight:500;margin:0 0 6px;position:relative;z-index:1}
.sv{color:#fff;font-size:3rem;font-weight:900;margin:0;letter-spacing:-2px;position:relative;z-index:1}
.sp{color:rgba(255,255,255,.85);font-size:1.6rem;font-weight:700;margin:2px 0 8px;position:relative;z-index:1}
.sq{color:rgba(255,255,255,.55);font-size:.88rem;margin:0;position:relative;z-index:1}
.subcard{
  background:linear-gradient(135deg,var(--Bl),#fff);
  border:2px solid var(--Bm);border-radius:18px;
  padding:32px 24px;text-align:center;
  margin:1rem 1rem 1.5rem;box-shadow:var(--sh);
}

/* ══ CARDS GÉNÉRIQUES ══ */
.card{
  background:var(--sur);border:1.5px solid var(--bor);
  border-radius:var(--r);padding:18px 20px;margin:10px 1rem;
  box-shadow:var(--sh);
}
.slbl{
  font-size:.7rem;font-weight:800;color:var(--mu2);
  text-transform:uppercase;letter-spacing:.12em;
  margin:22px 1rem 9px;display:block;
}

/* ══ KPI DASHBOARD ══ */
.kpi-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin:0 1rem 20px}
.kpi{
  border-radius:var(--r);padding:20px 18px;
  box-shadow:var(--sh);position:relative;overflow:hidden;
  transition:transform .2s,box-shadow .2s;
}
.kpi:hover{transform:translateY(-2px);box-shadow:var(--shm)}
.kpi::after{
  content:'';position:absolute;bottom:-25px;right:-25px;
  width:90px;height:90px;border-radius:50%;opacity:.1;
}
.kpi-b{background:linear-gradient(135deg,#EFF6FF,#DBEAFE);border:1.5px solid #BFDBFE}
.kpi-b::after{background:var(--B)}
.kpi-g{background:linear-gradient(135deg,#ECFDF5,#D1FAE5);border:1.5px solid #A7F3D0}
.kpi-g::after{background:var(--G)}
.kpi-o{background:linear-gradient(135deg,#FFFBEB,#FEF3C7);border:1.5px solid #FDE68A}
.kpi-o::after{background:var(--O)}
.kpi-p{background:linear-gradient(135deg,#F5F3FF,#EDE9FE);border:1.5px solid #DDD6FE}
.kpi-p::after{background:var(--P)}
.kpi-icon{font-size:1.7rem;margin-bottom:10px;display:block}
.kpi-val{font-size:2.1rem;font-weight:900;margin:0;letter-spacing:-1px;line-height:1}
.kpi-b .kpi-val{color:var(--B)}.kpi-g .kpi-val{color:var(--Gd)}
.kpi-o .kpi-val{color:var(--Od)}.kpi-p .kpi-val{color:#7C3AED}
.kpi-lbl{font-size:.72rem;font-weight:700;color:var(--mu);margin:5px 0 0;text-transform:uppercase;letter-spacing:.08em}

/* ══ ACTIVITÉ ══ */
.act-item{display:flex;align-items:center;gap:12px;padding:11px 0;border-bottom:1px solid var(--bor)}
.act-item:last-child{border-bottom:none}
.act-av{
  width:38px;height:38px;border-radius:50%;flex-shrink:0;
  display:flex;align-items:center;justify-content:center;
  font-weight:800;font-size:13px;
  background:linear-gradient(135deg,var(--Bm),var(--Bl));color:var(--B);
}
.act-name{font-weight:700;font-size:14px;color:var(--txt)}
.act-quiz{font-size:.78rem;color:var(--mu);margin-top:1px}
.act-score{margin-left:auto;text-align:right;flex-shrink:0}
.act-pct{font-size:1.05rem;font-weight:800}
.act-time{font-size:.72rem;color:var(--mu2)}

/* ══ AGENT CARD ADMIN ══ */
.agcard{
  background:var(--sur);border:1.5px solid var(--bor);
  border-radius:var(--r);padding:14px 16px;margin:6px 0;
  box-shadow:var(--sh);transition:border-color .15s;
}
.agcard:hover{border-color:var(--Bm)}
.agtop{display:flex;align-items:center;gap:12px;margin-bottom:10px}
.av{
  width:38px;height:38px;border-radius:50%;flex-shrink:0;
  background:linear-gradient(135deg,var(--Bm),var(--Bl));color:var(--B);
  display:flex;align-items:center;justify-content:center;
  font-weight:800;font-size:13px;
}

/* ══ BADGES ══ */
.badge{display:inline-block;padding:3px 10px;border-radius:99px;font-size:.72rem;font-weight:700}
.bg{background:var(--Gl);color:var(--Gd)}.bo{background:var(--Ol);color:var(--Od)}
.bb{background:var(--Bm);color:var(--Bd)}.bgr{background:#F1F5F9;color:#475569}
.br{background:var(--Rl);color:var(--Rd)}

/* ══ BARRE SCORES ══ */
.qzbar{margin:6px 0}
.qzbar-row{display:flex;align-items:center;gap:10px;margin:6px 0}
.qzbar-lbl{font-size:.82rem;font-weight:600;color:var(--txt);min-width:100px;max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.qzbar-bg{flex:1;background:var(--Bm);border-radius:99px;height:10px;overflow:hidden}
.qzbar-fill{height:10px;border-radius:99px}
.qzbar-val{font-size:.82rem;font-weight:800;min-width:38px;text-align:right}

/* ══ TABS ══ */
.stTabs [data-baseweb="tab-list"]{gap:4px!important;border-bottom:2px solid var(--bor)!important;padding:0 1rem!important}
.stTabs [data-baseweb="tab"]{
  font-family:'Plus Jakarta Sans',sans-serif!important;
  font-size:13px!important;font-weight:700!important;
  padding:10px 14px!important;border-radius:8px 8px 0 0!important;
  letter-spacing:-.01em!important;
}

/* ══ EXPANDER ══ */
div[data-testid="stExpander"]{
  border:2px solid var(--bor)!important;border-radius:var(--r)!important;
  margin:6px 0!important;overflow:hidden!important;box-shadow:var(--sh)!important;
  transition:border-color .15s!important;
}
div[data-testid="stExpander"]:hover{border-color:var(--Bm)!important}
div[data-testid="stExpander"] summary{
  font-family:'Plus Jakarta Sans',sans-serif!important;
  font-weight:700!important;font-size:14px!important;padding:14px 18px!important;
}

/* ══ FORM ══ */
div[data-testid="stForm"]{border:none!important;padding:0!important}
hr{border:none!important;border-top:2px solid var(--bor)!important;margin:20px 1rem!important}
.stAlert{border-radius:var(--r)!important;font-family:'Plus Jakarta Sans',sans-serif!important;margin:0 1rem!important}

/* ══ SCROLLBAR ══ */
::-webkit-scrollbar{width:5px}
::-webkit-scrollbar-track{background:var(--bg)}
::-webkit-scrollbar-thumb{background:var(--Bm);border-radius:99px}
::-webkit-scrollbar-thumb:hover{background:var(--B)}
</style>""", unsafe_allow_html=True)

init_db()

try:
    from streamlit_autorefresh import st_autorefresh
    _AR = True
except ImportError:
    _AR = False

_D = {
    "page":"home","current_agent":None,"current_quiz":None,
    "quiz_questions":None,"quiz_start_time":None,"quiz_answers":{},
    "session_id":None,"admin_logged":False,"quiz_submitted":False,
    "final_score":None,"edit_quiz_id":None,"adding_q_type":"single",
}
for k,v in _D.items():
    if k not in st.session_state: st.session_state[k]=v


def go(p): st.session_state.page=p; st.rerun()


# ── Persistance de session (survit au refresh) ───────────────────────────────

def _admin_token():
    day = datetime.now().strftime("%Y%m%d")
    return hashlib.md5(f"{config.ADMIN_PASSWORD}{day}".encode()).hexdigest()[:16]


def _save_state():
    """Encode l'état dans l'URL — ne déclenche PAS de rerun."""
    try:
        qp = dict(st.query_params)
        changed = False
        def _set(k, v):
            nonlocal changed
            if qp.get(k) != v: qp[k] = v; changed = True
        def _del(k):
            nonlocal changed
            if k in qp: del qp[k]; changed = True

        if st.session_state.current_agent:
            _set("a", str(st.session_state.current_agent["id"]))
        else:
            _del("a"); _del("s"); _del("p")

        if st.session_state.admin_logged:
            _set("t", _admin_token())
        else:
            _del("t")

        if st.session_state.session_id and not st.session_state.quiz_submitted:
            _set("s", str(st.session_state.session_id))
        else:
            _del("s")

        if st.session_state.page not in ("home",):
            _set("p", st.session_state.page)
        else:
            _del("p")

        if changed:
            for k,v in list(qp.items()):
                st.query_params[k] = v
            for k in list(st.query_params.keys()):
                if k not in qp:
                    del st.query_params[k]
    except Exception:
        pass


def _restore_state():
    """Lit l'URL et restaure l'état — appelé UNE SEULE FOIS au démarrage."""
    if st.session_state.get("_restored"):
        return
    st.session_state["_restored"] = True
    try:
        qp = st.query_params

        # 1. Restaurer l'agent
        if "a" in qp and not st.session_state.current_agent:
            try:
                agent = get_agent_by_id(int(qp["a"]))
                if agent:
                    st.session_state.current_agent = agent
            except Exception:
                pass

        # 2. Restaurer le login admin
        if "t" in qp and not st.session_state.admin_logged:
            try:
                if qp["t"] == _admin_token():
                    st.session_state.admin_logged = True
            except Exception:
                pass

        # 3. Restaurer le quiz en cours
        if "s" in qp and st.session_state.current_agent and not st.session_state.session_id:
            try:
                sid = int(qp["s"])
                sess = get_session_by_id(sid)
                if sess and not sess.get("completed"):
                    quiz = get_quiz(sess["quiz_id"])
                    if quiz:
                        epoch = float(sess.get("start_time_epoch") or time.time())
                        remaining = quiz["duree_minutes"] * 60 - (time.time() - epoch)
                        if remaining > 15:
                            questions = get_questions(quiz["id"])
                            try:
                                answers = json.loads(sess.get("answers_json") or "{}")
                                answers = {int(k) if str(k).isdigit() else k: v for k,v in answers.items()}
                            except Exception:
                                answers = {}
                            st.session_state.current_quiz      = quiz
                            st.session_state.quiz_questions    = questions
                            st.session_state.quiz_start_time   = epoch
                            st.session_state.quiz_answers      = answers
                            st.session_state.session_id        = sid
                            st.session_state.quiz_submitted    = False
                            st.session_state.page              = "agent_quiz"
                        else:
                            # Temps écoulé — soumettre automatiquement
                            try:
                                questions = get_questions(quiz["id"])
                                answers = json.loads(sess.get("answers_json") or "{}")
                                answers = {int(k) if str(k).isdigit() else k: v for k,v in answers.items()}
                                score, records = _calc(questions, answers)
                                submit_session(sid, score, records)
                            except Exception:
                                pass
            except Exception:
                pass

        # 4. Restaurer la page (après avoir restauré l'état)
        if "p" in qp and st.session_state.page == "home":
            page = qp["p"]
            # Vérifier que l'état requis est présent
            if page in ("agent_quiz_code", "agent_quiz", "agent_result") and st.session_state.current_agent:
                st.session_state.page = page
            elif page in ("admin_dashboard", "admin_quiz_edit") and st.session_state.admin_logged:
                st.session_state.page = page
    except Exception:
        pass


# ── Appel unique au démarrage ─────────────────────────────────────────────────
_restore_state()


def _generate_quiz_pdf(quiz, questions):
    """Génère un vrai fichier PDF du corrigé via fpdf2."""
    from fpdf import FPDF
    import io

    TYPES = {"single":"Choix unique","multiple":"Choix multiple",
             "numeric":"Valeur numérique","text":"Texte libre"}

    class PDF(FPDF):
        def header(self):
            # Bande bleue en haut
            self.set_fill_color(30, 58, 138)
            self.rect(0, 0, 210, 38, "F")
            self.set_text_color(255, 255, 255)
            self.set_font("Helvetica", "B", 17)
            self.set_xy(12, 7)
            titre = quiz["titre"][:58]
            self.cell(186, 9, titre, ln=True)
            self.set_font("Helvetica", "", 10)
            self.set_xy(12, 18)
            total_pts = sum(q["points"] for q in questions)
            info = f"Code: {quiz['code']}   |   Duree: {quiz['duree_minutes']} min   |   {len(questions)} question(s)   |   {total_pts:.0f} pt(s)"
            self.cell(186, 6, info, ln=True)
            if quiz.get("description"):
                self.set_xy(12, 26)
                self.set_font("Helvetica", "I", 9)
                self.set_text_color(200, 220, 255)
                self.cell(186, 6, quiz["description"][:80], ln=True)
            self.set_text_color(0, 0, 0)
            self.ln(16)

        def footer(self):
            self.set_y(-14)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(150, 150, 150)
            now = datetime.now().strftime("%d/%m/%Y %H:%M")
            self.cell(0, 8, f"QuizAgent CI  —  Genere le {now}  —  Page {self.page_no()}", align="C")

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    for i, q in enumerate(questions):
        pts = f"{q['points']:.0f} pt" + ("s" if q["points"] != 1 else "")
        type_lbl = TYPES.get(q["type"], q["type"])

        # Numéro + type
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(239, 246, 255)
        pdf.set_text_color(29, 78, 216)
        pdf.cell(20, 6, f"  Q{i+1}", fill=True, border=0)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(60, 6, type_lbl, border=0)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 6, pts, align="R", ln=True, border=0)

        # Texte de la question — bande bleu gauche
        pdf.set_fill_color(29, 78, 216)
        pdf.rect(pdf.get_x(), pdf.get_y(), 3, 8, "F")
        pdf.set_x(pdf.get_x() + 5)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(15, 23, 42)
        # multi_cell pour les longs textes
        x_before = pdf.get_x()
        pdf.multi_cell(175, 6, q["texte"], border=0)
        pdf.ln(3)

        # Options / réponses
        if q["type"] in ("single", "multiple"):
            for o in q["options"]:
                if o["is_correct"]:
                    pdf.set_fill_color(209, 250, 229)
                    pdf.set_draw_color(5, 150, 105)
                    pdf.set_text_color(6, 95, 70)
                    icon = "OK "
                    font_style = "B"
                else:
                    pdf.set_fill_color(248, 250, 255)
                    pdf.set_draw_color(226, 232, 244)
                    pdf.set_text_color(15, 23, 42)
                    icon = "   "
                    font_style = ""
                pdf.set_x(16)
                pdf.set_font("Helvetica", font_style, 10)
                pdf.multi_cell(174, 6, f"{icon}{o['texte']}", border=1, fill=True)
                pdf.ln(1)

        elif q["type"] == "numeric":
            rep = q.get("reponse_correcte_num")
            pdf.set_x(16)
            pdf.set_fill_color(209, 250, 229)
            pdf.set_text_color(6, 95, 70)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(174, 7, f"  Reponse correcte : {rep}", fill=True, border=1, ln=True)

        elif q["type"] == "text":
            raw = (q.get("reponse_correcte_txt") or "").strip()
            pdf.set_x(16)
            pdf.set_fill_color(209, 250, 229)
            pdf.set_text_color(6, 95, 70)
            pdf.set_font("Helvetica", "B", 10)
            if raw:
                pdf.multi_cell(174, 7, f"  Reponse(s) : {raw}", fill=True, border=1)
            else:
                pdf.set_fill_color(241, 245, 249)
                pdf.set_text_color(100, 116, 139)
                pdf.cell(174, 7, "  Question ouverte (pas de correction automatique)", fill=True, border=1, ln=True)

        pdf.ln(6)

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


def topbar(t,i="📝"): st.markdown(f'<div class="topbar"><span style="font-size:1.2rem">{i}</span><span class="tt">{t}</span></div>',unsafe_allow_html=True)
def slbl(t): st.markdown(f'<p class="slbl">{t}</p>',unsafe_allow_html=True)
def badge(t,c="b"): return f'<span class="badge b{c}">{t}</span>'

def kpi_grid(items):
    """items = [(icon, value, label, color_class), ...]"""
    cols = "".join(
        f'<div class="kpi kpi-{c}"><div class="kpi-icon">{i}</div>'
        f'<p class="kpi-val">{v}</p><p class="kpi-lbl">{l}</p></div>'
        for i,v,l,c in items
    )
    st.markdown(f'<div class="kpi-grid">{cols}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  HOME
# ══════════════════════════════════════════════════════════════

def render_home():
    org = f"<br><small style='opacity:.7'>{config.ORG_NAME}</small>" if config.ORG_NAME else ""
    st.markdown(
        f'<div class="hero"><div class="hi">📝</div>'
        f'<h1 class="ht">{config.APP_TITLE}</h1>'
        f'<p class="hs">{config.APP_SUBTITLE}{org}</p></div>',
        unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1:
        if st.button("👤  Je suis Agent",key="home_agent",use_container_width=True,type="primary"): go("agent_search")
    with c2:
        if st.button("⚙️  Administration",key="home_admin",use_container_width=True): go("admin_login")


# ══════════════════════════════════════════════════════════════
#  AGENT — Recherche
# ══════════════════════════════════════════════════════════════

def render_agent_search():
    topbar("Identification","👤")
    slbl("Tapez votre nom ou matricule")
    q = st.text_input(" ", placeholder="Ex : Konan, Diallo, AGT001…",
                       label_visibility="collapsed", key="sq")
    if st.button("← Retour",key="as_back",use_container_width=True): go("home")
    q = (q or "").strip()
    if len(q)<2:
        if len(q)==1: st.caption("Continuez à taper…")
        return
    agents = search_agents(q)
    if not agents:
        st.warning("Aucun agent trouvé. Vérifiez l'orthographe ou contactez votre superviseur.")
        return
    slbl(f"{len(agents)} résultat(s) — appuyez sur votre nom")
    for a in agents:
        lbl = f"👤  {a['nom']} {a['prenom']}".strip()
        if a["matricule"]: lbl += f"  ·  {a['matricule']}"
        if st.button(lbl,key=f"sel_{a['id']}",use_container_width=True,type="primary"):
            st.session_state.current_agent=a; _save_state(); go("agent_quiz_code")


# ══════════════════════════════════════════════════════════════
#  AGENT — Code quiz
# ══════════════════════════════════════════════════════════════

def render_agent_quiz_code():
    agent=st.session_state.current_agent
    if not agent: go("agent_search"); return
    topbar("Accès au Quiz","📋")
    init=(agent["nom"][0]+(agent["prenom"][0] if agent["prenom"] else "")).upper()
    st.markdown(
        f'<div class="card" style="display:flex;align-items:center;gap:12px;margin-bottom:18px">'
        f'<div class="av" style="width:44px;height:44px;font-size:15px">{init}</div>'
        f'<div><div style="font-size:1.05rem;font-weight:700">{agent["nom"]} {agent["prenom"]}</div>'
        f'<div style="color:var(--mu);font-size:.83rem">{agent["matricule"] or "Agent"}</div></div></div>',
        unsafe_allow_html=True)
    slbl("Code du quiz communiqué par votre superviseur")
    code=st.text_input(" ",placeholder="Ex : QZ001",max_chars=20,label_visibility="collapsed")
    c1,c2=st.columns([1,2])
    with c1:
        if st.button("← Retour",key="aqc_back",use_container_width=True): go("agent_search")
    with c2:
        if st.button("▶  Commencer",key="aqc_start",type="primary",use_container_width=True):
            _start_quiz(agent,code)


def _start_quiz(agent, code):
    if not (code or "").strip(): st.warning("Saisissez un code."); return
    quiz=get_quiz_by_code(code.strip())
    if not quiz: st.error("Code incorrect ou quiz désactivé."); return

    # ── Vérifier session en cours (pour restore après refresh) ──
    incomplete=get_incomplete_session(agent["id"],quiz["id"])
    if incomplete and incomplete.get("start_time_epoch"):
        epoch=incomplete["start_time_epoch"]
        remaining=quiz["duree_minutes"]*60-(time.time()-epoch)
        if remaining>15:  # encore du temps
            try:
                raw=incomplete.get("answers_json") or "{}"
                answers=json.loads(raw)
                answers={int(k) if str(k).isdigit() else k: v for k,v in answers.items()}
            except Exception:
                answers={}
            questions=get_questions(quiz["id"])  # ordre non aléatoire à la restauration
            st.session_state.current_quiz=quiz
            st.session_state.quiz_questions=questions
            st.session_state.quiz_start_time=epoch
            st.session_state.quiz_answers=answers
            st.session_state.quiz_submitted=False
            st.session_state.session_id=incomplete["id"]
            st.toast("🔄 Quiz en cours restauré — continuez !", icon="✅")
            go("agent_quiz"); return
        else:
            # temps écoulé sur session incomplète → auto-soumettre
            try:
                raw=incomplete.get("answers_json") or "{}"
                answers=json.loads(raw)
                answers={int(k) if str(k).isdigit() else k: v for k,v in answers.items()}
                questions=get_questions(quiz["id"])
                score,records=_calc(questions,answers)
                submit_session(incomplete["id"],score,records)
            except Exception: pass
            st.warning("Votre temps était écoulé. Votre session a été automatiquement soumise.")
            return

    if session_already_completed(agent["id"],quiz["id"]):
        st.warning("Vous avez déjà soumis ce quiz. Contactez votre superviseur."); return

    shuffled=bool(quiz.get("randomize_questions",0))
    questions=get_questions(quiz["id"],shuffled=shuffled)
    if not questions: st.error("Ce quiz ne contient pas encore de questions."); return

    max_score=sum(q["points"] for q in questions)
    epoch=time.time()
    sid=create_session(agent["id"],quiz["id"],max_score,epoch)
    st.session_state.current_quiz=quiz
    st.session_state.quiz_questions=questions
    st.session_state.quiz_start_time=epoch
    st.session_state.quiz_answers={}
    st.session_state.quiz_submitted=False
    st.session_state.session_id=sid
    go("agent_quiz")


# ══════════════════════════════════════════════════════════════
#  AGENT — Quiz (timer fixe)
# ══════════════════════════════════════════════════════════════

def _calc(questions, answers):
    score,records=0.0,[]
    for q in questions:
        qid=q["id"]; resp=answers.get(qid,""); ok=0
        if q["type"]=="single":
            ok=1 if resp in [o["id"] for o in q["options"] if o["is_correct"]] else 0
        elif q["type"]=="multiple":
            cor=set(o["id"] for o in q["options"] if o["is_correct"])
            giv=set(resp) if isinstance(resp,list) else set()
            ok=1 if giv==cor and cor else 0
        elif q["type"]=="numeric":
            try:
                exp=float(q["reponse_correcte_num"]) if q["reponse_correcte_num"] is not None else None
                giv=float(str(resp).replace(",",".")) if str(resp).strip() else None
                ok=1 if exp is not None and giv is not None and abs(giv-exp)<0.01 else 0
            except: ok=0
        elif q["type"]=="text":
            raw=(q.get("reponse_correcte_txt") or "").strip()
            if raw: ok=1 if str(resp).lower().strip() in [a.lower().strip() for a in raw.split("|") if a.strip()] else 0
            else:   ok=1
        if ok: score+=q["points"]
        records.append({"question_id":qid,
                         "reponse":json.dumps(resp,ensure_ascii=False) if isinstance(resp,list) else str(resp),
                         "is_correct":ok})
    return score,records


def _submit():
    if st.session_state.quiz_submitted: return
    ql=st.session_state.quiz_questions
    score,records=_calc(ql,st.session_state.quiz_answers)
    submit_session(st.session_state.session_id,score,records)
    st.session_state.final_score={"score":score,"max_score":sum(q["points"] for q in ql)}
    st.session_state.quiz_submitted=True


def render_agent_quiz():
    if st.session_state.quiz_submitted: go("agent_result"); return

    quiz=st.session_state.current_quiz
    questions=st.session_state.quiz_questions
    agent=st.session_state.current_agent

    if _AR: st_autorefresh(interval=2000,key="qr")

    remaining=max(0,quiz["duree_minutes"]*60-(time.time()-st.session_state.quiz_start_time))

    if remaining<=0:
        _submit(); st.session_state.page="agent_result"; st.rerun(); return

    mins,secs=int(remaining//60),int(remaining%60)
    if remaining>300:  tcls,tlbl,tico="tn","Temps restant","⏱"
    elif remaining>60: tcls,tlbl,tico="tw","Moins de 5 min !","⚠️"
    else:              tcls,tlbl,tico="td","Dépêchez-vous !","🚨"

    # ── TIMER FIXE — position:fixed via JS pour garantir le fonctionnement ──
    st.markdown(f"""
    <div id="quiz-timer-bar">
      <div class="inner">
        <div class="tbox {tcls}">
          <span class="ticon">{tico}</span>
          <div><p class="ttime">{mins:02d}:{secs:02d}</p><p class="tlbl">{tlbl}</p></div>
        </div>
      </div>
    </div>
    <div style="height:90px"></div>
    <script>
    (function(){{
      var el=document.getElementById('quiz-timer-bar');
      if(el && el.parentNode!==document.body){{
        document.body.insertBefore(el,document.body.firstChild);
      }}
    }})();
    </script>
    """, unsafe_allow_html=True)

    answered=sum(1 for v in st.session_state.quiz_answers.values() if v not in("","[],",None,[]))
    pct=answered/len(questions) if questions else 0
    st.markdown(
        f'<div class="prog">'
        f'<div class="prog-row"><span><b>{quiz["titre"]}</b></span><span>{answered}/{len(questions)} répondue(s)</span></div>'
        f'<div class="prog-bg"><div class="prog-fill" style="width:{pct*100:.0f}%"></div></div>'
        f'</div>', unsafe_allow_html=True)

    ICONS={"single":"⭕","multiple":"☑️","numeric":"🔢","text":"📝"}
    HINTS={"single":"Une seule réponse","multiple":"Plusieurs réponses","numeric":"Entrez un nombre","text":"Réponse libre"}

    for i,q in enumerate(questions):
        qid=q["id"]
        pts=f"{q['points']:.0f} pt"+("s" if q["points"]!=1 else "")
        st.markdown(
            f'<div class="qcard">'
            f'<div class="qmeta"><span class="qnum">Q{i+1}</span>'
            f'<span class="qtype">{ICONS[q["type"]]} {HINTS[q["type"]]}</span>'
            f'<span class="qpts">{pts}</span></div>'
            f'<p class="qtxt">{q["texte"]}</p></div>', unsafe_allow_html=True)

        if q["type"]=="single":
            opts=q["options"]; cur=st.session_state.quiz_answers.get(qid)
            idx=next((j for j,o in enumerate(opts) if o["id"]==cur),None)
            sel=st.radio(" ",range(len(opts)),format_func=lambda x,_o=opts:_o[x]["texte"],
                         index=idx,key=f"q_{qid}",label_visibility="collapsed")
            if sel is not None: st.session_state.quiz_answers[qid]=opts[sel]["id"]

        elif q["type"]=="multiple":
            cur=st.session_state.quiz_answers.get(qid,[])
            sel=[]
            for o in q["options"]:
                if st.checkbox(o["texte"],value=(o["id"] in cur),key=f"q_{qid}_{o['id']}"): sel.append(o["id"])
            st.session_state.quiz_answers[qid]=sel

        elif q["type"]=="numeric":
            val=st.session_state.quiz_answers.get(qid,"")
            v=st.text_input(" ",value=str(val) if val!="" else "",key=f"q_{qid}",
                             placeholder="Entrez un nombre…",label_visibility="collapsed")
            st.session_state.quiz_answers[qid]=v

        elif q["type"]=="text":
            val=st.session_state.quiz_answers.get(qid,"")
            v=st.text_area(" ",value=val,key=f"q_{qid}",height=80,
                            placeholder="Votre réponse…",label_visibility="collapsed")
            st.session_state.quiz_answers[qid]=v

        st.markdown("")

    st.markdown("---")
    if st.button("✅  Soumettre mes réponses",key="quiz_submit",type="primary",use_container_width=True):
        _submit()
        go("agent_result")
        return

    # ── Sauvegarde auto des réponses (uniquement si pas en train de soumettre) ──
    if st.session_state.session_id and not st.session_state.quiz_submitted:
        try:
            save_quiz_progress(
                st.session_state.session_id,
                json.dumps(st.session_state.quiz_answers),
                st.session_state.quiz_start_time
            )
        except Exception: pass


# ══════════════════════════════════════════════════════════════
#  AGENT — Résultat
# ══════════════════════════════════════════════════════════════

def render_agent_result():
    res=st.session_state.final_score; quiz=st.session_state.current_quiz; agent=st.session_state.current_agent
    if not res or not agent or not quiz: go("home"); return
    show_score=bool(quiz.get("show_score",1))
    score,max_sc=res["score"],res["max_score"]
    pct=(score/max_sc*100) if max_sc>0 else 0
    if show_score:
        emoji="🏆" if pct>=80 else("👍" if pct>=60 else "📚")
        st.markdown(
            f'<div class="scard"><div class="se">{emoji}</div>'
            f'<p class="sn">{agent["nom"]} {agent["prenom"]}</p>'
            f'<p class="sv">{score:.1f} / {max_sc:.1f}</p>'
            f'<p class="sp">{pct:.0f} %</p><p class="sq">{quiz["titre"]}</p></div>',
            unsafe_allow_html=True)
        if pct>=80: st.success("Excellent résultat ! Félicitations ! 🎉")
        elif pct>=60: st.info("Bon résultat. Continuez vos efforts !")
        else: st.warning("Il faut encore travailler ce sujet. Courage !")
    else:
        st.markdown(
            f'<div class="subcard"><div style="font-size:2.5rem;margin-bottom:8px">✅</div>'
            f'<div style="font-size:1.1rem;font-weight:700;color:var(--Bd)">Réponses enregistrées</div>'
            f'<div style="color:var(--mu);font-size:.9rem;margin-top:6px">{agent["nom"]} {agent["prenom"]} · {quiz["titre"]}</div></div>',
            unsafe_allow_html=True)
    st.markdown(f'<p style="text-align:center;color:var(--mu);font-size:.82rem;margin:6px 0 14px">Soumis le {datetime.now().strftime("%d/%m/%Y à %H:%M")}</p>',unsafe_allow_html=True)
    if st.button("🏠  Retour à l'accueil",key="result_home",use_container_width=True):
        for k in("current_quiz","quiz_questions","quiz_start_time","quiz_answers","session_id","quiz_submitted","final_score"): st.session_state[k]=_D[k]
        st.session_state.current_agent=None; _save_state(); go("home")


# ══════════════════════════════════════════════════════════════
#  ADMIN — Connexion
# ══════════════════════════════════════════════════════════════

def render_admin_login():
    if st.session_state.admin_logged: go("admin_dashboard"); return
    topbar("Administration","⚙️")
    st.markdown('<div class="card">',unsafe_allow_html=True)
    st.markdown("#### 🔐 Connexion administrateur")
    pwd=st.text_input(" ",type="password",placeholder="Mot de passe…",label_visibility="collapsed")
    c1,c2=st.columns([1,2])
    with c1:
        if st.button("← Retour",key="al_back",use_container_width=True): go("home")
    with c2:
        if st.button("Se connecter",key="al_login",type="primary",use_container_width=True):
            if pwd==config.ADMIN_PASSWORD: st.session_state.admin_logged=True; _save_state(); go("admin_dashboard")
            else: st.error("Mot de passe incorrect.")
    st.markdown('</div>',unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  ADMIN — Dashboard
# ══════════════════════════════════════════════════════════════

def render_admin_dashboard():
    if not st.session_state.admin_logged: go("admin_login"); return
    topbar(config.APP_TITLE+"  ·  Tableau de bord","⚙️")

    t0,t1,t2,t3=st.tabs(["📊 Vue d'ensemble","👥 Agents","📝 Quiz","📋 Résultats"])
    with t0: _tab_overview()
    with t1: _tab_agents()
    with t2: _tab_quizzes()
    with t3: _tab_results()

    st.markdown("---")
    if st.button("🚪  Déconnexion",key="admin_logout",use_container_width=True): st.session_state.admin_logged=False; _save_state(); go("home")


# ── Vue d'ensemble ────────────────────────────────────────────

def _tab_overview():
    stats=get_stats()

    kpi_grid([
        ("👥", stats["total_agents"],   "Agents total",  "b"),
        ("✅", stats["pub_agents"],      "Publiés",       "g"),
        ("📝", stats["active_quizzes"],  "Quiz actifs",   "p"),
        ("📊", stats["total_submissions"],"Soumissions",  "o"),
    ])

    # Score moyen global
    avg=stats["avg_score"]
    c1,c2=st.columns(2)
    with c1:
        st.markdown(
            f'<div class="card" style="text-align:center">'
            f'<div style="font-size:.72rem;font-weight:700;color:var(--mu);text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px">Score moyen global</div>'
            f'<div style="font-size:2.4rem;font-weight:900;color:{"var(--G)" if avg>=70 else "var(--O)" if avg>=50 else "var(--R)"}">{avg:.1f}%</div>'
            f'</div>',unsafe_allow_html=True)
    with c2:
        # Taux de complétion : sessions complétées / agents publiés
        rate=min(100,round(stats["total_submissions"]/max(1,stats["pub_agents"])*100))
        st.markdown(
            f'<div class="card" style="text-align:center">'
            f'<div style="font-size:.72rem;font-weight:700;color:var(--mu);text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px">Agents ayant composé</div>'
            f'<div style="font-size:2.4rem;font-weight:900;color:var(--B)">{rate}%</div>'
            f'</div>',unsafe_allow_html=True)

    # Scores par quiz
    if stats["per_quiz"]:
        st.markdown('<p class="slbl">Scores moyens par quiz</p>',unsafe_allow_html=True)
        bars=""
        for q in stats["per_quiz"]:
            pct=min(100,q["avg_pct"] or 0)
            col="var(--G)" if pct>=70 else("var(--O)" if pct>=50 else "var(--R)")
            bars+=f'<div class="qz-bar-row"><span class="qz-bar-lbl" title="{q["titre"]}">{q["titre"][:20]}</span><div class="qz-bar-bg"><div class="qz-bar-fill" style="width:{pct:.0f}%;background:linear-gradient(90deg,{col},{col}88)"></div></div><span class="qz-bar-val">{pct:.0f}%</span></div>'
        st.markdown(f'<div class="qz-bar-wrap">{bars}</div>',unsafe_allow_html=True)

    # Activité récente
    if stats["recent"]:
        st.markdown('<p class="slbl">10 dernières soumissions</p>',unsafe_allow_html=True)
        items=""
        for r in stats["recent"]:
            pct_r=(r["score"]/r["max_score"]*100) if r["max_score"]>0 else 0
            col_r="var(--G)" if pct_r>=70 else("var(--O)" if pct_r>=50 else "var(--R)")
            init_r=(r["nom"][0]+(r["prenom"][0] if r["prenom"] else "")).upper()
            # Format time
            try:
                dt=datetime.fromisoformat(r["completed_at"])
                diff=datetime.now()-dt
                if diff.seconds<3600:    tstr=f"Il y a {diff.seconds//60} min"
                elif diff.days==0:       tstr=f"Il y a {diff.seconds//3600}h"
                else:                    tstr=dt.strftime("%d/%m %H:%M")
            except: tstr=r["completed_at"][:16] if r["completed_at"] else "—"
            items+=(f'<div class="activity-item">'
                    f'<div class="act-av">{init_r}</div>'
                    f'<div><div class="act-name">{r["nom"]} {r["prenom"]}</div>'
                    f'<div class="act-quiz">{r["titre"]}</div></div>'
                    f'<div class="act-score">'
                    f'<div class="act-pct" style="color:{col_r}">{pct_r:.0f}%</div>'
                    f'<div class="act-time">{tstr}</div></div></div>')
        st.markdown(f'<div class="card">{items}</div>',unsafe_allow_html=True)
    else:
        st.info("Aucune soumission pour l'instant.")

    # Actions rapides
    st.markdown('<p class="slbl">Actions rapides</p>',unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1:
        if st.button("➕  Créer un quiz",key="ovw_create_quiz",use_container_width=True,type="primary"):
            st.session_state.edit_quiz_id=None; go("admin_quiz_edit")
    with c2:
        if st.button("✅  Publier tous les agents",key="ovw_pub_all",use_container_width=True):
            publish_all_agents(); st.rerun()


# ── Agents ────────────────────────────────────────────────────

def _ndf(df):
    df.columns=[str(c).lower().strip() for c in df.columns]
    nom=next((c for c in ["nom","name","lastname","noms"] if c in df.columns),None)
    if not nom: return None
    pre=next((c for c in ["prenom","prénom","firstname","prenoms"] if c in df.columns),None)
    mat=next((c for c in ["matricule","id","code","identifiant"] if c in df.columns),None)
    out=pd.DataFrame()
    out["nom"]=df[nom]; out["prenom"]=df[pre] if pre else ""; out["matricule"]=df[mat] if mat else ""
    return out


def _tab_agents():
    s1,s2,s3=st.tabs(["✏️ Ajouter","📥 Importer","📋 Liste"])
    with s1:
        with st.form("fag",clear_on_submit=True):
            c1,c2,c3=st.columns(3)
            with c1: nom=st.text_input("Nom *")
            with c2: pre=st.text_input("Prénom")
            with c3: mat=st.text_input("Matricule")
            if st.form_submit_button("Ajouter",type="primary",use_container_width=True):
                if not nom.strip(): st.error("Nom obligatoire.")
                elif add_agent_manual(nom.strip(),pre.strip(),mat.strip()): st.success(f"{nom} ajouté."); st.rerun()
                else: st.warning("Cet agent existe déjà.")
    with s2:
        st.markdown("**Fichier CSV ou Excel**"); st.caption("Colonnes : `nom`, `prenom`, `matricule`")
        up=st.file_uploader("Fichier",type=["csv","xlsx","xls"],label_visibility="collapsed")
        if up:
            try:
                df_r=pd.read_csv(up) if up.name.lower().endswith(".csv") else pd.read_excel(up)
                df=_ndf(df_r)
                if df is None: st.error("Colonne 'nom' introuvable.")
                else:
                    st.dataframe(df.head(5),use_container_width=True)
                    st.caption(f"{len(df)} agent(s)")
                    if st.button("✅  Importer",key="ag_import_file",type="primary",use_container_width=True):
                        n=upsert_agents(df); st.success(f"{n} importé(s)."); st.rerun()
            except Exception as e: st.error(f"Erreur : {e}")
        st.markdown("---"); st.markdown("**Google Sheets (lien public)**")
        gs=st.text_input("URL",placeholder="https://docs.google.com/spreadsheets/d/…",label_visibility="collapsed")
        if st.button("Importer depuis Google Sheets",key="ag_import_gs",use_container_width=True): _gs(gs)
    with s3:
        ags=get_all_agents()
        if not ags: st.info("Aucun agent."); return
        nb=sum(1 for a in ags if a["published"])
        st.markdown(f'<p style="color:var(--mu);font-size:.85rem;margin-bottom:10px"><b>{len(ags)}</b> agent(s) &nbsp;·&nbsp;{badge(f"{nb} publié(s)","g")} &nbsp;{badge(f"{len(ags)-nb} brouillon(s)","o")}</p>',unsafe_allow_html=True)
        c1,c2=st.columns(2)
        with c1:
            if st.button("✅ Publier tous",key="ag_pub_all",use_container_width=True,type="primary"): publish_all_agents(); st.rerun()
        with c2:
            if st.button("⛔ Dépublier tous",key="ag_unpub_all",use_container_width=True): unpublish_all_agents(); st.rerun()
        st.markdown("---")
        filtre=st.text_input("🔍 Filtrer",placeholder="Nom, matricule…",key="af",label_visibility="collapsed")
        shown=[a for a in ags if not filtre or filtre.lower() in f"{a['nom']} {a['prenom']} {a['matricule']}".lower()]
        for a in shown:
            init=(a["nom"][0]+(a["prenom"][0] if a["prenom"] else "")).upper()
            pub_b=badge("✓ Publié","g") if a["published"] else badge("Brouillon","o")
            mat_s=f'  ·  <span style="color:var(--mu)">{a["matricule"]}</span>' if a["matricule"] else ""
            st.markdown(f'<div class="agcard"><div class="agtop"><div class="av">{init}</div><div><b>{a["nom"]} {a["prenom"]}</b>{mat_s}<br>{pub_b}</div></div>',unsafe_allow_html=True)
            c1,c2=st.columns([3,1])
            with c1:
                lbl="🔓 Dépublier" if a["published"] else "✅ Publier"
                if st.button(lbl,key=f"p_{a['id']}",use_container_width=True): set_agent_published(a["id"],0 if a["published"] else 1); st.rerun()
            with c2:
                if st.button("🗑️",key=f"d_{a['id']}",use_container_width=True): delete_agent(a["id"]); st.rerun()
            st.markdown('</div>',unsafe_allow_html=True)


def _gs(url):
    if not (url or "").strip(): st.warning("Collez une URL."); return
    try:
        m=re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)",url)
        if not m: st.error("URL invalide."); return
        sid=m.group(1); gm=re.search(r"gid=(\d+)",url); gid=gm.group(1) if gm else "0"
        r=requests.get(f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid={gid}",timeout=15); r.raise_for_status()
        df=_ndf(pd.read_csv(io.StringIO(r.text)))
        if df is None: st.error("Colonne 'nom' introuvable."); return
        n=upsert_agents(df); st.success(f"{n} agent(s) importé(s)."); st.rerun()
    except Exception as e: st.error(f"Erreur : {e}")


# ── Quiz ──────────────────────────────────────────────────────

def _tab_quizzes():
    if st.button("➕  Créer un quiz",key="qz_create_quiz",type="primary",use_container_width=True):
        st.session_state.edit_quiz_id=None; go("admin_quiz_edit")
    st.markdown("---")
    quizzes=get_all_quizzes()
    if not quizzes: st.info("Aucun quiz."); return
    for quiz in quizzes:
        nb=len(get_questions(quiz["id"]))
        s=badge("Actif","g") if quiz["actif"] else badge("Inactif","gr")
        sc=badge("Score visible","b") if quiz.get("show_score",1) else badge("Score masqué","o")
        rn=badge("Aléatoire","b") if quiz.get("randomize_questions",0) else ""
        with st.expander(f"{'🟢' if quiz['actif'] else '⚫'} {quiz['titre']}  ·  `{quiz['code']}`"):
            st.markdown(f"{s} &nbsp;{sc} &nbsp;{rn} &nbsp;{badge(str(quiz['duree_minutes'])+' min','gr')} &nbsp;{badge(str(nb)+' question(s)','gr')}",unsafe_allow_html=True)
            if quiz["description"]: st.caption(quiz["description"])
            c1,c2,c3=st.columns(3)
            with c1:
                if st.button("✏️ Modifier",key=f"eq_{quiz['id']}",use_container_width=True): st.session_state.edit_quiz_id=quiz["id"]; go("admin_quiz_edit")
            with c2:
                if st.button("🟢 Activer" if not quiz["actif"] else "🔴 Désactiver",key=f"tq_{quiz['id']}",use_container_width=True):
                    update_quiz(quiz["id"],quiz["titre"],quiz["code"],quiz["duree_minutes"],quiz["description"],0 if quiz["actif"] else 1,quiz.get("show_score",1),quiz.get("randomize_questions",0)); st.rerun()
            with c3:
                if st.button("🗑 Suppr.",key=f"dq_{quiz['id']}",use_container_width=True): delete_quiz(quiz["id"]); st.rerun()
            # Export PDF corrigé
            if nb > 0:
                qz_questions = get_questions(quiz["id"])
                pdf_bytes = _generate_quiz_pdf(quiz, qz_questions)
                st.download_button(
                    "📄  Télécharger le corrigé PDF",
                    data=pdf_bytes,
                    file_name=f"corrige_{quiz['code']}.pdf",
                    mime="application/pdf",
                    key=f"pdf_{quiz['id']}",
                    use_container_width=True,
                )


# ── Résultats ─────────────────────────────────────────────────

def _tab_results():
    quizzes=get_all_quizzes()
    opts={0:"— Tous les quiz —"}; opts.update({q["id"]:f"{q['titre']} ({q['code']})" for q in quizzes})
    sel=st.selectbox("Quiz",list(opts.keys()),format_func=lambda x:opts[x],label_visibility="collapsed")
    results=get_results(sel if sel else None)
    if not results: st.info("Aucun résultat disponible."); return
    df=pd.DataFrame(results)
    df["pct"]=(df["score"]/df["max_score"]*100).round(1); df["agent"]=df["nom"]+" "+df["prenom"]
    disp=df[["agent","matricule","quiz_titre","score","max_score","pct","completed_at"]].copy()
    disp.columns=["Agent","Matricule","Quiz","Score","Sur","%","Date"]
    st.dataframe(disp,use_container_width=True)
    buf=io.BytesIO()
    with pd.ExcelWriter(buf,engine="openpyxl") as w:
        disp.to_excel(w,index=False,sheet_name="Résultats")
        ws=w.sheets["Résultats"]
        for col in ws.columns:
            ml=max((len(str(c.value)) for c in col if c.value),default=10)
            ws.column_dimensions[col[0].column_letter].width=min(ml+4,40)
    buf.seek(0)
    st.download_button("📥  Télécharger Excel",data=buf.getvalue(),
                        file_name=f"resultats_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True)


# ══════════════════════════════════════════════════════════════
#  ADMIN — Éditeur Quiz
# ══════════════════════════════════════════════════════════════

_TYPES={"single":"⭕  Choix unique","multiple":"☑️  Choix multiple","numeric":"🔢  Valeur numérique","text":"📝  Texte libre"}


def render_admin_quiz_edit():
    if not st.session_state.admin_logged: go("admin_login"); return
    quiz_id=st.session_state.edit_quiz_id; is_new=quiz_id is None; existing=get_quiz(quiz_id) if not is_new else None
    topbar("Nouveau Quiz" if is_new else "Modifier le Quiz","📝")
    st.markdown('<div class="card">',unsafe_allow_html=True)
    with st.form("fqi"):
        titre=st.text_input("Titre *",value=existing["titre"] if existing else "",placeholder="Ex : Évaluation module Femme")
        c1,c2=st.columns(2)
        with c1: code=st.text_input("Code *",value=existing["code"] if existing else "",placeholder="QZ001",max_chars=20)
        with c2: duree=st.number_input("Durée (min)",min_value=1,max_value=600,value=existing["duree_minutes"] if existing else 30)
        desc=st.text_area("Description",value=existing["description"] if existing else "",height=68)
        c1,c2=st.columns(2)
        with c1: show_sc=st.checkbox("Afficher le score aux agents",value=bool(existing.get("show_score",1)) if existing else True,help="Décoché = l'agent voit seulement 'Réponses enregistrées'")
        with c2: rnd=st.checkbox("Questions aléatoires",value=bool(existing.get("randomize_questions",0)) if existing else False,help="Ordre différent pour chaque agent")
        if st.form_submit_button("💾  Enregistrer",type="primary",use_container_width=True):
            if not titre.strip() or not code.strip(): st.error("Titre et code obligatoires.")
            else:
                if is_new:
                    try:
                        nid=create_quiz(titre.strip(),code.strip(),int(duree),desc.strip(),int(show_sc),int(rnd))
                        st.session_state.edit_quiz_id=nid; st.success("Quiz créé !"); st.rerun()
                    except Exception as e: st.error(f"Erreur (code déjà existant ?) : {e}")
                else:
                    update_quiz(quiz_id,titre.strip(),code.strip(),int(duree),desc.strip(),existing["actif"],int(show_sc),int(rnd)); st.success("Quiz mis à jour."); st.rerun()
    st.markdown('</div>',unsafe_allow_html=True)

    cur_id=st.session_state.edit_quiz_id
    if not cur_id:
        if st.button("← Retour",key="qe_back_top",use_container_width=True): go("admin_dashboard")
        return

    questions=get_questions(cur_id)
    slbl(f"Questions ({len(questions)})")
    if questions:
        for i,q in enumerate(questions):
            with st.expander(f"Q{i+1}  ·  {_TYPES[q['type']]}  ·  {q['texte'][:50]}{'…' if len(q['texte'])>50 else ''}"):
                if q["type"] in("single","multiple"):
                    for o in q["options"]: st.markdown(f"{'✅' if o['is_correct'] else '◻️'} {o['texte']}")
                elif q["type"]=="numeric": st.markdown(f"**Réponse :** `{q['reponse_correcte_num']}`")
                elif q["type"]=="text":    st.markdown(f"**Réponses :** `{q['reponse_correcte_txt']}`")
                st.caption(f"{q['points']} point(s)")
                if st.button("🗑️ Supprimer",key=f"dq_{q['id']}"): delete_question(q["id"]); reorder_questions(cur_id); st.rerun()
    else: st.info("Aucune question. Ajoutez-en ci-dessous.")

    slbl("Ajouter une question")
    q_type=st.selectbox("Type",list(_TYPES.keys()),format_func=lambda x:_TYPES[x],key="aqt",label_visibility="collapsed")
    with st.form("faq",clear_on_submit=True):
        q_txt=st.text_area("Question *",height=88,placeholder="Saisissez votre question…")
        q_pts=st.number_input("Points",min_value=0.5,max_value=20.0,value=1.0,step=0.5)
        opts_d=[]
        if q_type in("single","multiple"):
            st.markdown("**Options** — cochez la/les bonne(s) réponse(s) ✅")
            for j in range(6):
                c1,c2=st.columns([5,1])
                with c1: ot=st.text_input(f"Option {j+1}",key=f"ot_{j}",label_visibility="collapsed",placeholder=f"Option {j+1}…")
                with c2: oc=st.checkbox("✅",key=f"oc_{j}")
                if ot.strip(): opts_d.append({"texte":ot.strip(),"is_correct":oc})
        elif q_type=="numeric": c_num=st.number_input("Réponse correcte",value=0.0,format="%.4f")
        elif q_type=="text":    c_txt=st.text_input("Réponse(s)",placeholder="rep1 | rep2  (laisser vide = question ouverte)")
        if st.form_submit_button("➕  Ajouter la question",type="primary",use_container_width=True):
            err=None
            if not q_txt.strip(): err="Texte obligatoire."
            elif q_type in("single","multiple"):
                if not opts_d: err="Ajoutez au moins une option."
                elif not any(o["is_correct"] for o in opts_d): err="Cochez au moins une bonne réponse."
                elif q_type=="single" and sum(o["is_correct"] for o in opts_d)>1: err="Choix unique : une seule bonne réponse."
            if err: st.error(err)
            else:
                ordre=len(questions)
                if q_type in("single","multiple"): add_question(cur_id,q_txt.strip(),q_type,ordre,q_pts,options=opts_d)
                elif q_type=="numeric":             add_question(cur_id,q_txt.strip(),q_type,ordre,q_pts,num=c_num)
                elif q_type=="text":                add_question(cur_id,q_txt.strip(),q_type,ordre,q_pts,txt=(c_txt.strip() if c_txt else ""))
                st.success("Question ajoutée ✓"); st.rerun()

    st.markdown("---")
    if st.button("← Retour au dashboard",key="qe_back_bot",use_container_width=True): go("admin_dashboard")


# ══════════════════════════════════════════════════════════════
#  ROUTEUR
# ══════════════════════════════════════════════════════════════

_R={"home":render_home,"agent_search":render_agent_search,"agent_quiz_code":render_agent_quiz_code,
    "agent_quiz":render_agent_quiz,"agent_result":render_agent_result,
    "admin_login":render_admin_login,"admin_dashboard":render_admin_dashboard,
    "admin_quiz_edit":render_admin_quiz_edit}

fn=_R.get(st.session_state.get("page","home"))
if fn: fn()
else: go("home")
