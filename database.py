"""
database.py — QuizAgent CI
"""
import sqlite3, json, os, random
from datetime import datetime
import config


def _path():
    p = config.DB_PATH
    d = os.path.dirname(p)
    if d: os.makedirs(d, exist_ok=True)
    return p


def get_conn():
    c = sqlite3.connect(_path(), check_same_thread=False, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    c.execute("PRAGMA journal_mode = WAL")
    c.execute("PRAGMA busy_timeout = 10000")
    return c


def init_db():
    conn = get_conn(); c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS agents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL, prenom TEXT DEFAULT '',
        matricule TEXT DEFAULT '', published INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")

    c.execute("""CREATE TABLE IF NOT EXISTS quizzes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titre TEXT NOT NULL, code TEXT UNIQUE NOT NULL,
        duree_minutes INTEGER DEFAULT 30, description TEXT DEFAULT '',
        actif INTEGER DEFAULT 1, show_score INTEGER DEFAULT 1,
        randomize_questions INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")

    c.execute("""CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_id INTEGER NOT NULL, texte TEXT NOT NULL, type TEXT NOT NULL,
        ordre INTEGER DEFAULT 0, points REAL DEFAULT 1,
        reponse_correcte_num REAL, reponse_correcte_txt TEXT,
        FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE)""")

    c.execute("""CREATE TABLE IF NOT EXISTS options (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER NOT NULL, texte TEXT NOT NULL, is_correct INTEGER DEFAULT 0,
        FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE)""")

    # sessions : inclut start_time_epoch et answers_json pour persistance cross-refresh
    c.execute("""CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id INTEGER NOT NULL, quiz_id INTEGER NOT NULL,
        score REAL DEFAULT 0, max_score REAL DEFAULT 0,
        completed INTEGER DEFAULT 0,
        start_time_epoch REAL,
        answers_json TEXT DEFAULT '{}',
        started_at TEXT DEFAULT CURRENT_TIMESTAMP,
        completed_at TEXT,
        FOREIGN KEY (agent_id) REFERENCES agents(id),
        FOREIGN KEY (quiz_id) REFERENCES quizzes(id))""")

    c.execute("""CREATE TABLE IF NOT EXISTS answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL, question_id INTEGER NOT NULL,
        reponse TEXT DEFAULT '', is_correct INTEGER DEFAULT 0,
        FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
        FOREIGN KEY (question_id) REFERENCES questions(id))""")

    # Migrations colonnes manquantes
    for tbl, col, dflt in [
        ("quizzes",  "show_score",          "1"),
        ("quizzes",  "randomize_questions",  "0"),
        ("sessions", "start_time_epoch",     "NULL"),
        ("sessions", "answers_json",         "'{}'"),
    ]:
        try: c.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} DEFAULT {dflt}")
        except Exception: pass

    conn.commit(); conn.close()


# ── AGENTS ────────────────────────────────────────────────────

def search_agents(q):
    conn = get_conn(); c = conn.cursor()
    p = f"%{q.lower()}%"
    c.execute("SELECT * FROM agents WHERE published=1 AND (LOWER(nom) LIKE ? OR LOWER(prenom) LIKE ? OR LOWER(matricule) LIKE ?) ORDER BY nom,prenom", (p,p,p))
    r = [dict(x) for x in c.fetchall()]; conn.close(); return r

def get_all_agents():
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT * FROM agents ORDER BY nom,prenom")
    r = [dict(x) for x in c.fetchall()]; conn.close(); return r

def upsert_agents(df):
    conn = get_conn(); c = conn.cursor(); n = 0
    for _, row in df.iterrows():
        nom = str(row.get("nom","")).strip(); pre = str(row.get("prenom","")).strip(); mat = str(row.get("matricule","")).strip()
        if not nom or nom.lower()=="nan": continue
        if pre.lower()=="nan": pre=""
        if mat.lower()=="nan": mat=""
        c.execute("SELECT id FROM agents WHERE nom=? AND prenom=?",(nom,pre))
        if not c.fetchone(): c.execute("INSERT INTO agents (nom,prenom,matricule) VALUES (?,?,?)",(nom,pre,mat)); n+=1
    conn.commit(); conn.close(); return n

def set_agent_published(aid, pub):
    conn = get_conn(); conn.execute("UPDATE agents SET published=? WHERE id=?",(pub,aid)); conn.commit(); conn.close()

def publish_all_agents():
    conn = get_conn(); conn.execute("UPDATE agents SET published=1"); conn.commit(); conn.close()

def unpublish_all_agents():
    conn = get_conn(); conn.execute("UPDATE agents SET published=0"); conn.commit(); conn.close()

def delete_agent(aid):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT id FROM sessions WHERE agent_id=?",(aid,))
    for (sid,) in c.fetchall(): c.execute("DELETE FROM answers WHERE session_id=?",(sid,))
    c.execute("DELETE FROM sessions WHERE agent_id=?",(aid,))
    c.execute("DELETE FROM agents WHERE id=?",(aid,))
    conn.commit(); conn.close()

def add_agent_manual(nom, pre, mat):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT id FROM agents WHERE nom=? AND prenom=?",(nom,pre))
    if c.fetchone(): conn.close(); return False
    c.execute("INSERT INTO agents (nom,prenom,matricule) VALUES (?,?,?)",(nom,pre,mat))
    conn.commit(); conn.close(); return True


# ── QUIZZES ───────────────────────────────────────────────────

def get_quiz_by_code(code):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT * FROM quizzes WHERE UPPER(code)=? AND actif=1",(code.upper(),))
    r = c.fetchone(); conn.close(); return dict(r) if r else None

def get_all_quizzes():
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT * FROM quizzes ORDER BY created_at DESC")
    r = [dict(x) for x in c.fetchall()]; conn.close(); return r

def get_quiz(qid):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT * FROM quizzes WHERE id=?",(qid,))
    r = c.fetchone(); conn.close(); return dict(r) if r else None

def create_quiz(titre, code, duree, desc, show_score=1, randomize=0):
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT INTO quizzes (titre,code,duree_minutes,description,show_score,randomize_questions) VALUES (?,?,?,?,?,?)",
              (titre,code.upper(),duree,desc,show_score,randomize))
    qid = c.lastrowid; conn.commit(); conn.close(); return qid

def update_quiz(qid, titre, code, duree, desc, actif, show_score=1, randomize=0):
    conn = get_conn()
    conn.execute("UPDATE quizzes SET titre=?,code=?,duree_minutes=?,description=?,actif=?,show_score=?,randomize_questions=? WHERE id=?",
                 (titre,code.upper(),duree,desc,actif,show_score,randomize,qid))
    conn.commit(); conn.close()

def delete_quiz(qid):
    conn = get_conn(); conn.execute("DELETE FROM quizzes WHERE id=?",(qid,)); conn.commit(); conn.close()


# ── QUESTIONS ─────────────────────────────────────────────────

def get_questions(qid, shuffled=False):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT * FROM questions WHERE quiz_id=? ORDER BY ordre",(qid,))
    qs = [dict(x) for x in c.fetchall()]
    for q in qs:
        c.execute("SELECT * FROM options WHERE question_id=?",(q["id"],))
        q["options"] = [dict(o) for o in c.fetchall()]
    conn.close()
    if shuffled: random.shuffle(qs)
    return qs

def add_question(qid, texte, qtype, ordre, points, options=None, num=None, txt=None):
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT INTO questions (quiz_id,texte,type,ordre,points,reponse_correcte_num,reponse_correcte_txt) VALUES (?,?,?,?,?,?,?)",
              (qid,texte,qtype,ordre,points,num,txt))
    new_id = c.lastrowid
    if options and qtype in ("single","multiple"):
        for o in options: c.execute("INSERT INTO options (question_id,texte,is_correct) VALUES (?,?,?)",(new_id,o["texte"],int(o["is_correct"])))
    conn.commit(); conn.close(); return new_id

def delete_question(qid):
    conn = get_conn(); conn.execute("DELETE FROM questions WHERE id=?",(qid,)); conn.commit(); conn.close()

def reorder_questions(qid):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT id FROM questions WHERE quiz_id=? ORDER BY ordre",(qid,))
    for i,(sid,) in enumerate(c.fetchall()): c.execute("UPDATE questions SET ordre=? WHERE id=?",(i,sid))
    conn.commit(); conn.close()


# ── SESSIONS ──────────────────────────────────────────────────

def create_session(agent_id, quiz_id, max_score, start_time_epoch):
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT INTO sessions (agent_id,quiz_id,max_score,start_time_epoch,answers_json) VALUES (?,?,?,?,'{}')",
              (agent_id,quiz_id,max_score,start_time_epoch))
    sid = c.lastrowid; conn.commit(); conn.close(); return sid

def save_quiz_progress(session_id, answers_json_str, start_time_epoch):
    """Sauvegarde les réponses en cours — appelé à chaque rendu pour survie au refresh."""
    conn = get_conn()
    conn.execute("UPDATE sessions SET answers_json=?,start_time_epoch=? WHERE id=? AND completed=0",
                 (answers_json_str, start_time_epoch, session_id))
    conn.commit(); conn.close()

def get_incomplete_session(agent_id, quiz_id):
    """Retourne la session en cours non soumise pour cet agent+quiz, ou None."""
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT * FROM sessions WHERE agent_id=? AND quiz_id=? AND completed=0 ORDER BY started_at DESC LIMIT 1",
              (agent_id,quiz_id))
    r = c.fetchone(); conn.close(); return dict(r) if r else None

def submit_session(session_id, score, records):
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE sessions SET score=?,completed=1,completed_at=? WHERE id=?",
              (score,datetime.now().isoformat(),session_id))
    for a in records:
        c.execute("INSERT INTO answers (session_id,question_id,reponse,is_correct) VALUES (?,?,?,?)",
                  (session_id,a["question_id"],str(a["reponse"]),int(a["is_correct"])))
    conn.commit(); conn.close()

def get_results(quiz_id=None):
    conn = get_conn(); c = conn.cursor()
    base = """SELECT s.id,a.nom,a.prenom,a.matricule,q.titre AS quiz_titre,q.code AS quiz_code,
              s.score,s.max_score,s.started_at,s.completed_at
              FROM sessions s JOIN agents a ON s.agent_id=a.id JOIN quizzes q ON s.quiz_id=q.id
              WHERE s.completed=1"""
    if quiz_id: c.execute(base+" AND s.quiz_id=? ORDER BY s.completed_at DESC",(quiz_id,))
    else:        c.execute(base+" ORDER BY s.completed_at DESC")
    r = [dict(x) for x in c.fetchall()]; conn.close(); return r

def session_already_completed(agent_id, quiz_id):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT id FROM sessions WHERE agent_id=? AND quiz_id=? AND completed=1",(agent_id,quiz_id))
    r = c.fetchone() is not None; conn.close(); return r

def get_stats():
    """Stats agrégées pour le dashboard admin."""
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM agents")
    total_agents = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM agents WHERE published=1")
    pub_agents = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM quizzes WHERE actif=1")
    active_quizzes = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM sessions WHERE completed=1")
    total_submissions = c.fetchone()[0]
    c.execute("SELECT AVG(score*100.0/max_score) FROM sessions WHERE completed=1 AND max_score>0")
    avg_score = c.fetchone()[0] or 0
    # Scores par quiz
    c.execute("""SELECT q.titre, COUNT(s.id) as nb, AVG(s.score*100.0/s.max_score) as avg_pct
                 FROM sessions s JOIN quizzes q ON s.quiz_id=q.id
                 WHERE s.completed=1 AND s.max_score>0
                 GROUP BY q.id ORDER BY nb DESC""")
    per_quiz = [dict(x) for x in c.fetchall()]
    # 10 dernières soumissions
    c.execute("""SELECT a.nom,a.prenom,q.titre,s.score,s.max_score,s.completed_at
                 FROM sessions s JOIN agents a ON s.agent_id=a.id JOIN quizzes q ON s.quiz_id=q.id
                 WHERE s.completed=1 ORDER BY s.completed_at DESC LIMIT 10""")
    recent = [dict(x) for x in c.fetchall()]
    conn.close()
    return {
        "total_agents": total_agents, "pub_agents": pub_agents,
        "active_quizzes": active_quizzes, "total_submissions": total_submissions,
        "avg_score": avg_score, "per_quiz": per_quiz, "recent": recent,
    }
