"""
database.py — QuizAgent CI
Backend PostgreSQL (Supabase) avec fallback SQLite pour dev local.
"""
import os, json, random
from datetime import datetime

# ── Détection du backend ──────────────────────────────────────────────────────
# Si DATABASE_URL est défini → PostgreSQL (Supabase)
# Sinon → SQLite local (développement)

DATABASE_URL = os.environ.get("DATABASE_URL") or ""
try:
    from streamlit import secrets as _sec
    DATABASE_URL = DATABASE_URL or _sec.get("DATABASE_URL", "")
except Exception:
    pass

USE_PG = bool(DATABASE_URL)

if USE_PG:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    import psycopg2.pool
    _pool = None

    def _get_pool():
        global _pool
        if _pool is None:
            from urllib.parse import urlparse, quote, urlunparse
            p = urlparse(DATABASE_URL)
            if p.password:
                safe_pass = quote(p.password, safe="")
                safe_user = quote(p.username, safe="")
                host_part = p.hostname
                if p.port: host_part += f":{p.port}"
                safe_url = urlunparse(p._replace(netloc=f"{safe_user}:{safe_pass}@{host_part}"))
            else:
                safe_url = DATABASE_URL
            _pool = psycopg2.pool.SimpleConnectionPool(1, 5, safe_url)
        return _pool

    def get_conn():
        return _get_pool().getconn()

    def release(conn):
        _get_pool().putconn(conn)

    # Adaptateur : rend les résultats accessibles comme des dicts
    class _Cur:
        def __init__(self, conn):
            self._conn = conn
            self._cur  = conn.cursor(cursor_factory=RealDictCursor)
            self._lastrowid = None
        def execute(self, sql, params=None):
            sql = sql.replace("?", "%s")
            # Pour les INSERT, ajoute RETURNING id automatiquement
            sql_up = sql.strip().upper()
            if sql_up.startswith("INSERT") and "RETURNING" not in sql_up:
                sql = sql.rstrip().rstrip(";") + " RETURNING id"
                self._cur.execute(sql, params)
                row = self._cur.fetchone()
                self._lastrowid = row["id"] if row else None
            else:
                self._cur.execute(sql, params)
            return self
        def fetchone(self):  return self._cur.fetchone()
        def fetchall(self):  return self._cur.fetchall()
        @property
        def lastrowid(self): return self._lastrowid
        def __enter__(self): return self
        def __exit__(self, *a): self._conn.commit()

    def _cursor(conn): return _Cur(conn)

    def _run(sql, params=None):
        """Exécute une requête sans retour."""
        conn = get_conn()
        try:
            sql = sql.replace("?", "%s")
            with conn.cursor() as c:
                c.execute(sql, params)
            conn.commit()
        finally:
            release(conn)

    # Adaptation syntaxe PG : AUTOINCREMENT → SERIAL, TEXT DEFAULT '' → TEXT DEFAULT ''
    def _pg(sql):
        return (sql
            .replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
            .replace("REAL DEFAULT NULL", "DOUBLE PRECISION")
            .replace("REAL DEFAULT 0", "DOUBLE PRECISION DEFAULT 0")
            .replace("REAL", "DOUBLE PRECISION")
            .replace("CREATE TABLE IF NOT EXISTS", "CREATE TABLE IF NOT EXISTS")
        )

else:
    import sqlite3, config as _cfg

    def _db_path():
        p = _cfg.DB_PATH
        d = os.path.dirname(p)
        if d: os.makedirs(d, exist_ok=True)
        return p

    def get_conn():
        c = sqlite3.connect(_db_path(), check_same_thread=False, timeout=30)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys = ON")
        c.execute("PRAGMA journal_mode = WAL")
        c.execute("PRAGMA busy_timeout = 10000")
        return c

    def release(conn): pass

    class _Cur:
        def __init__(self, conn):
            self._conn = conn
            self._cur  = conn.cursor()
        def execute(self, sql, params=None):
            self._cur.execute(sql, params or ())
            return self
        def fetchone(self): return self._cur.fetchone()
        def fetchall(self): return self._cur.fetchall()
        @property
        def lastrowid(self): return self._cur.lastrowid
        def __enter__(self): return self
        def __exit__(self, *a): self._conn.commit()

    def _cursor(conn): return _Cur(conn)

    def _run(sql, params=None):
        conn = get_conn()
        conn.execute(sql, params or ())
        conn.commit()
        conn.close()

    def _pg(sql): return sql


def _row(r):
    """Convertit un résultat (Row SQLite ou dict PG) en dict Python."""
    if r is None: return None
    return dict(r)


# ── Initialisation des tables ─────────────────────────────────────────────────

def init_db():
    conn = get_conn()
    c = _cursor(conn)

    with c:
        c.execute(_pg("""CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL, prenom TEXT DEFAULT '',
            matricule TEXT DEFAULT '', published INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP)"""))

        c.execute(_pg("""CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titre TEXT NOT NULL, code TEXT UNIQUE NOT NULL,
            duree_minutes INTEGER DEFAULT 30, description TEXT DEFAULT '',
            actif INTEGER DEFAULT 1, show_score INTEGER DEFAULT 1,
            randomize_questions INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP)"""))

        c.execute(_pg("""CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER NOT NULL, texte TEXT NOT NULL, type TEXT NOT NULL,
            ordre INTEGER DEFAULT 0, points REAL DEFAULT 1,
            reponse_correcte_num REAL, reponse_correcte_txt TEXT)"""))

        c.execute(_pg("""CREATE TABLE IF NOT EXISTS options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL, texte TEXT NOT NULL,
            is_correct INTEGER DEFAULT 0)"""))

        c.execute(_pg("""CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id INTEGER NOT NULL, quiz_id INTEGER NOT NULL,
            score REAL DEFAULT 0, max_score REAL DEFAULT 0,
            completed INTEGER DEFAULT 0,
            start_time_epoch DOUBLE PRECISION,
            answers_json TEXT DEFAULT '{}',
            started_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT)"""))

        c.execute(_pg("""CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL, question_id INTEGER NOT NULL,
            reponse TEXT DEFAULT '', is_correct INTEGER DEFAULT 0)"""))

    # Migrations : ajouter les colonnes manquantes sans planter
    _safe_alter("quizzes",  "show_score",         "INTEGER DEFAULT 1")
    _safe_alter("quizzes",  "randomize_questions", "INTEGER DEFAULT 0")
    _safe_alter("sessions", "start_time_epoch",    "DOUBLE PRECISION")
    _safe_alter("sessions", "answers_json",        "TEXT DEFAULT '{}'")

    release(conn)


def _safe_alter(table, col, definition):
    try:
        if USE_PG:
            conn = get_conn()
            try:
                with conn.cursor() as c:
                    c.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {definition}")
                conn.commit()
            finally:
                release(conn)
        else:
            _run(f"ALTER TABLE {table} ADD COLUMN {col} {definition}")
    except Exception:
        pass


# ── Helpers internes ──────────────────────────────────────────────────────────

def _fetchall(sql, params=None):
    conn = get_conn()
    try:
        c = _cursor(conn)
        c.execute(sql, params or ())
        return [_row(r) for r in c.fetchall()]
    finally:
        release(conn)

def _fetchone(sql, params=None):
    conn = get_conn()
    try:
        c = _cursor(conn)
        c.execute(sql, params or ())
        return _row(c.fetchone())
    finally:
        release(conn)

def _execute(sql, params=None):
    """Exécute et retourne le lastrowid."""
    conn = get_conn()
    try:
        cur = _cursor(conn)
        with cur:
            cur.execute(sql, params or ())
        return cur.lastrowid
    finally:
        release(conn)


# ── AGENTS ────────────────────────────────────────────────────────────────────

def search_agents(q):
    p = f"%{q.lower()}%"
    return _fetchall(
        "SELECT * FROM agents WHERE published=1 AND (LOWER(nom) LIKE ? OR LOWER(prenom) LIKE ? OR LOWER(matricule) LIKE ?) ORDER BY nom,prenom",
        (p, p, p))

def get_all_agents():
    return _fetchall("SELECT * FROM agents ORDER BY nom,prenom")

def upsert_agents(df):
    n = 0
    for _, row in df.iterrows():
        nom = str(row.get("nom","")).strip()
        pre = str(row.get("prenom","")).strip()
        mat = str(row.get("matricule","")).strip()
        if not nom or nom.lower()=="nan": continue
        if pre.lower()=="nan": pre=""
        if mat.lower()=="nan": mat=""
        exists = _fetchone("SELECT id FROM agents WHERE nom=? AND prenom=?", (nom, pre))
        if not exists:
            _execute("INSERT INTO agents (nom,prenom,matricule) VALUES (?,?,?)", (nom, pre, mat))
            n += 1
    return n

def set_agent_published(aid, pub):
    _run("UPDATE agents SET published=? WHERE id=?", (pub, aid))

def publish_all_agents():
    _run("UPDATE agents SET published=1")

def unpublish_all_agents():
    _run("UPDATE agents SET published=0")

def delete_agent(aid):
    conn = get_conn()
    try:
        cur = _cursor(conn)
        with cur:
            cur.execute("SELECT id FROM sessions WHERE agent_id=?", (aid,))
            for r in cur.fetchall():
                cur.execute("DELETE FROM answers WHERE session_id=?", (_row(r)["id"],))
            cur.execute("DELETE FROM sessions WHERE agent_id=?", (aid,))
            cur.execute("DELETE FROM agents WHERE id=?", (aid,))
    finally:
        release(conn)

def add_agent_manual(nom, pre, mat):
    if _fetchone("SELECT id FROM agents WHERE nom=? AND prenom=?", (nom, pre)):
        return False
    _execute("INSERT INTO agents (nom,prenom,matricule) VALUES (?,?,?)", (nom, pre, mat))
    return True


# ── QUIZZES ───────────────────────────────────────────────────────────────────

def get_quiz_by_code(code):
    return _fetchone("SELECT * FROM quizzes WHERE UPPER(code)=? AND actif=1", (code.upper(),))

def get_all_quizzes():
    return _fetchall("SELECT * FROM quizzes ORDER BY created_at DESC")

def get_quiz(qid):
    return _fetchone("SELECT * FROM quizzes WHERE id=?", (qid,))

def create_quiz(titre, code, duree, desc, show_score=1, randomize=0):
    return _execute(
        "INSERT INTO quizzes (titre,code,duree_minutes,description,show_score,randomize_questions) VALUES (?,?,?,?,?,?)",
        (titre, code.upper(), duree, desc, show_score, randomize))

def update_quiz(qid, titre, code, duree, desc, actif, show_score=1, randomize=0):
    _run("UPDATE quizzes SET titre=?,code=?,duree_minutes=?,description=?,actif=?,show_score=?,randomize_questions=? WHERE id=?",
         (titre, code.upper(), duree, desc, actif, show_score, randomize, qid))

def delete_quiz(qid):
    _run("DELETE FROM quizzes WHERE id=?", (qid,))


# ── QUESTIONS ─────────────────────────────────────────────────────────────────

def get_questions(qid, shuffled=False):
    qs = _fetchall("SELECT * FROM questions WHERE quiz_id=? ORDER BY ordre", (qid,))
    for q in qs:
        q["options"] = _fetchall("SELECT * FROM options WHERE question_id=?", (q["id"],))
    if shuffled: random.shuffle(qs)
    return qs

def add_question(qid, texte, qtype, ordre, points, options=None, num=None, txt=None):
    new_id = _execute(
        "INSERT INTO questions (quiz_id,texte,type,ordre,points,reponse_correcte_num,reponse_correcte_txt) VALUES (?,?,?,?,?,?,?)",
        (qid, texte, qtype, ordre, points, num, txt))
    if options and qtype in ("single","multiple"):
        for o in options:
            _execute("INSERT INTO options (question_id,texte,is_correct) VALUES (?,?,?)",
                     (new_id, o["texte"], int(o["is_correct"])))
    return new_id

def delete_question(qid):
    _run("DELETE FROM questions WHERE id=?", (qid,))

def reorder_questions(qid):
    qs = _fetchall("SELECT id FROM questions WHERE quiz_id=? ORDER BY ordre", (qid,))
    for i, q in enumerate(qs):
        _run("UPDATE questions SET ordre=? WHERE id=?", (i, q["id"]))


# ── SESSIONS ──────────────────────────────────────────────────────────────────

def create_session(agent_id, quiz_id, max_score, start_time_epoch):
    return _execute(
        "INSERT INTO sessions (agent_id,quiz_id,max_score,start_time_epoch,answers_json) VALUES (?,?,?,?,'{}')",
        (agent_id, quiz_id, max_score, start_time_epoch))

def save_quiz_progress(session_id, answers_json_str, start_time_epoch):
    _run("UPDATE sessions SET answers_json=?,start_time_epoch=? WHERE id=? AND completed=0",
         (answers_json_str, start_time_epoch, session_id))

def get_incomplete_session(agent_id, quiz_id):
    return _fetchone(
        "SELECT * FROM sessions WHERE agent_id=? AND quiz_id=? AND completed=0 ORDER BY started_at DESC LIMIT 1",
        (agent_id, quiz_id))

def submit_session(session_id, score, records):
    _run("UPDATE sessions SET score=?,completed=1,completed_at=? WHERE id=?",
         (score, datetime.now().isoformat(), session_id))
    for a in records:
        _execute("INSERT INTO answers (session_id,question_id,reponse,is_correct) VALUES (?,?,?,?)",
                 (session_id, a["question_id"], str(a["reponse"]), int(a["is_correct"])))

def get_results(quiz_id=None):
    base = """SELECT s.id,a.nom,a.prenom,a.matricule,q.titre AS quiz_titre,q.code AS quiz_code,
              s.score,s.max_score,s.started_at,s.completed_at
              FROM sessions s JOIN agents a ON s.agent_id=a.id JOIN quizzes q ON s.quiz_id=q.id
              WHERE s.completed=1"""
    if quiz_id:
        return _fetchall(base+" AND s.quiz_id=? ORDER BY s.completed_at DESC", (quiz_id,))
    return _fetchall(base+" ORDER BY s.completed_at DESC")

def session_already_completed(agent_id, quiz_id):
    return _fetchone(
        "SELECT id FROM sessions WHERE agent_id=? AND quiz_id=? AND completed=1",
        (agent_id, quiz_id)) is not None

def get_stats():
    def _n(sql, p=None): r=_fetchone(sql,p); return list(_row(r).values())[0] if r else 0
    total_agents     = _n("SELECT COUNT(*) FROM agents")
    pub_agents       = _n("SELECT COUNT(*) FROM agents WHERE published=1")
    active_quizzes   = _n("SELECT COUNT(*) FROM quizzes WHERE actif=1")
    total_submissions= _n("SELECT COUNT(*) FROM sessions WHERE completed=1")
    avg_r = _fetchone("SELECT AVG(score*100.0/max_score) as v FROM sessions WHERE completed=1 AND max_score>0")
    avg_score = float(list(avg_r.values())[0]) if avg_r and list(avg_r.values())[0] else 0
    per_quiz = _fetchall("""SELECT q.titre, COUNT(s.id) as nb, AVG(s.score*100.0/s.max_score) as avg_pct
                 FROM sessions s JOIN quizzes q ON s.quiz_id=q.id
                 WHERE s.completed=1 AND s.max_score>0
                 GROUP BY q.titre ORDER BY nb DESC""")
    recent = _fetchall("""SELECT a.nom,a.prenom,q.titre,s.score,s.max_score,s.completed_at
                 FROM sessions s JOIN agents a ON s.agent_id=a.id JOIN quizzes q ON s.quiz_id=q.id
                 WHERE s.completed=1 ORDER BY s.completed_at DESC LIMIT 10""")
    return {"total_agents":total_agents,"pub_agents":pub_agents,
            "active_quizzes":active_quizzes,"total_submissions":total_submissions,
            "avg_score":avg_score,"per_quiz":per_quiz,"recent":recent}
