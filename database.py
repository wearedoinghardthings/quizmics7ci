"""
database.py — Couche de données SQLite pour QuizAgent CI
"""

import sqlite3
import json
import os
import random
from datetime import datetime

import config


def _db_path() -> str:
    path = config.DB_PATH
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    return path


def get_conn():
    conn = sqlite3.connect(_db_path(), check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS agents (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        nom         TEXT    NOT NULL,
        prenom      TEXT    DEFAULT \'\',
        matricule   TEXT    DEFAULT \'\',
        published   INTEGER DEFAULT 0,
        created_at  TEXT    DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS quizzes (
        id                   INTEGER PRIMARY KEY AUTOINCREMENT,
        titre                TEXT    NOT NULL,
        code                 TEXT    UNIQUE NOT NULL,
        duree_minutes        INTEGER DEFAULT 30,
        description          TEXT    DEFAULT \'\',
        actif                INTEGER DEFAULT 1,
        show_score           INTEGER DEFAULT 1,
        randomize_questions  INTEGER DEFAULT 0,
        created_at           TEXT    DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS questions (
        id                    INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_id               INTEGER NOT NULL,
        texte                 TEXT    NOT NULL,
        type                  TEXT    NOT NULL,
        ordre                 INTEGER DEFAULT 0,
        points                REAL    DEFAULT 1,
        reponse_correcte_num  REAL,
        reponse_correcte_txt  TEXT,
        FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS options (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER NOT NULL,
        texte       TEXT    NOT NULL,
        is_correct  INTEGER DEFAULT 0,
        FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS sessions (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id     INTEGER NOT NULL,
        quiz_id      INTEGER NOT NULL,
        score        REAL    DEFAULT 0,
        max_score    REAL    DEFAULT 0,
        completed    INTEGER DEFAULT 0,
        started_at   TEXT    DEFAULT CURRENT_TIMESTAMP,
        completed_at TEXT,
        FOREIGN KEY (agent_id) REFERENCES agents(id),
        FOREIGN KEY (quiz_id)  REFERENCES quizzes(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS answers (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id  INTEGER NOT NULL,
        question_id INTEGER NOT NULL,
        reponse     TEXT    DEFAULT \'\',
        is_correct  INTEGER DEFAULT 0,
        FOREIGN KEY (session_id)  REFERENCES sessions(id) ON DELETE CASCADE,
        FOREIGN KEY (question_id) REFERENCES questions(id)
    )""")

    # Migrations : ajout de colonnes si elles n\'existent pas encore
    for col, default in [("show_score", 1), ("randomize_questions", 0)]:
        try:
            c.execute(f"ALTER TABLE quizzes ADD COLUMN {col} INTEGER DEFAULT {default}")
        except Exception:
            pass

    conn.commit()
    conn.close()


# ── AGENTS ────────────────────────────────────────────────────────────────────

def search_agents(query: str):
    conn = get_conn()
    c = conn.cursor()
    q = f"%{query.lower()}%"
    c.execute("""
        SELECT * FROM agents
        WHERE published = 1
          AND (LOWER(nom) LIKE ? OR LOWER(prenom) LIKE ? OR LOWER(matricule) LIKE ?)
        ORDER BY nom, prenom
    """, (q, q, q))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_all_agents():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM agents ORDER BY nom, prenom")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def upsert_agents(df):
    conn = get_conn()
    c = conn.cursor()
    inserted = 0
    for _, row in df.iterrows():
        nom = str(row.get("nom", "")).strip()
        prenom = str(row.get("prenom", "")).strip()
        matricule = str(row.get("matricule", "")).strip()
        if not nom or nom.lower() == "nan":
            continue
        if prenom.lower() == "nan": prenom = ""
        if matricule.lower() == "nan": matricule = ""
        c.execute("SELECT id FROM agents WHERE nom=? AND prenom=?", (nom, prenom))
        if not c.fetchone():
            c.execute("INSERT INTO agents (nom, prenom, matricule) VALUES (?,?,?)",
                      (nom, prenom, matricule))
            inserted += 1
    conn.commit()
    conn.close()
    return inserted


def set_agent_published(agent_id: int, published: int):
    conn = get_conn()
    conn.execute("UPDATE agents SET published=? WHERE id=?", (published, agent_id))
    conn.commit()
    conn.close()


def publish_all_agents():
    conn = get_conn()
    conn.execute("UPDATE agents SET published=1")
    conn.commit()
    conn.close()


def unpublish_all_agents():
    conn = get_conn()
    conn.execute("UPDATE agents SET published=0")
    conn.commit()
    conn.close()


def delete_agent(agent_id: int):
    """Supprime un agent et toutes ses sessions/réponses associées."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM sessions WHERE agent_id=?", (agent_id,))
    session_ids = [r[0] for r in c.fetchall()]
    for sid in session_ids:
        c.execute("DELETE FROM answers WHERE session_id=?", (sid,))
    c.execute("DELETE FROM sessions WHERE agent_id=?", (agent_id,))
    c.execute("DELETE FROM agents WHERE id=?", (agent_id,))
    conn.commit()
    conn.close()


def add_agent_manual(nom: str, prenom: str, matricule: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM agents WHERE nom=? AND prenom=?", (nom, prenom))
    if c.fetchone():
        conn.close()
        return False
    c.execute("INSERT INTO agents (nom, prenom, matricule) VALUES (?,?,?)",
              (nom, prenom, matricule))
    conn.commit()
    conn.close()
    return True


# ── QUIZZES ───────────────────────────────────────────────────────────────────

def get_quiz_by_code(code: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM quizzes WHERE UPPER(code)=? AND actif=1", (code.upper(),))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_quizzes():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM quizzes ORDER BY created_at DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_quiz(quiz_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM quizzes WHERE id=?", (quiz_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def create_quiz(titre, code, duree_minutes, description, show_score=1, randomize=0) -> int:
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """INSERT INTO quizzes
           (titre, code, duree_minutes, description, show_score, randomize_questions)
           VALUES (?,?,?,?,?,?)""",
        (titre, code.upper(), duree_minutes, description, show_score, randomize),
    )
    qid = c.lastrowid
    conn.commit()
    conn.close()
    return qid


def update_quiz(quiz_id, titre, code, duree_minutes, description, actif,
                show_score=1, randomize=0):
    conn = get_conn()
    conn.execute(
        """UPDATE quizzes
           SET titre=?,code=?,duree_minutes=?,description=?,actif=?,
               show_score=?,randomize_questions=?
           WHERE id=?""",
        (titre, code.upper(), duree_minutes, description, actif,
         show_score, randomize, quiz_id),
    )
    conn.commit()
    conn.close()


def delete_quiz(quiz_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM quizzes WHERE id=?", (quiz_id,))
    conn.commit()
    conn.close()


# ── QUESTIONS ─────────────────────────────────────────────────────────────────

def get_questions(quiz_id: int, shuffled: bool = False):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM questions WHERE quiz_id=? ORDER BY ordre", (quiz_id,))
    questions = [dict(r) for r in c.fetchall()]
    for q in questions:
        c.execute("SELECT * FROM options WHERE question_id=?", (q["id"],))
        q["options"] = [dict(o) for o in c.fetchall()]
    conn.close()
    if shuffled:
        random.shuffle(questions)
    return questions


def add_question(quiz_id, texte, qtype, ordre, points,
                 options=None, reponse_correcte_num=None, reponse_correcte_txt=None) -> int:
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """INSERT INTO questions
           (quiz_id,texte,type,ordre,points,reponse_correcte_num,reponse_correcte_txt)
           VALUES (?,?,?,?,?,?,?)""",
        (quiz_id, texte, qtype, ordre, points, reponse_correcte_num, reponse_correcte_txt),
    )
    qid = c.lastrowid
    if options and qtype in ("single", "multiple"):
        for opt in options:
            c.execute("INSERT INTO options (question_id,texte,is_correct) VALUES (?,?,?)",
                      (qid, opt["texte"], int(opt["is_correct"])))
    conn.commit()
    conn.close()
    return qid


def delete_question(question_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM questions WHERE id=?", (question_id,))
    conn.commit()
    conn.close()


def reorder_questions(quiz_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM questions WHERE quiz_id=? ORDER BY ordre", (quiz_id,))
    ids = [r[0] for r in c.fetchall()]
    for i, qid in enumerate(ids):
        c.execute("UPDATE questions SET ordre=? WHERE id=?", (i, qid))
    conn.commit()
    conn.close()


# ── SESSIONS ──────────────────────────────────────────────────────────────────

def create_session(agent_id: int, quiz_id: int, max_score: float) -> int:
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO sessions (agent_id,quiz_id,max_score) VALUES (?,?,?)",
              (agent_id, quiz_id, max_score))
    sid = c.lastrowid
    conn.commit()
    conn.close()
    return sid


def submit_session(session_id: int, score: float, answer_records: list):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE sessions SET score=?,completed=1,completed_at=? WHERE id=?",
              (score, datetime.now().isoformat(), session_id))
    for ans in answer_records:
        c.execute(
            "INSERT INTO answers (session_id,question_id,reponse,is_correct) VALUES (?,?,?,?)",
            (session_id, ans["question_id"], str(ans["reponse"]), int(ans["is_correct"])),
        )
    conn.commit()
    conn.close()


def get_results(quiz_id=None):
    conn = get_conn()
    c = conn.cursor()
    base = """
        SELECT s.id, a.nom, a.prenom, a.matricule,
               q.titre AS quiz_titre, q.code AS quiz_code,
               s.score, s.max_score, s.started_at, s.completed_at
        FROM sessions s
        JOIN agents  a ON s.agent_id = a.id
        JOIN quizzes q ON s.quiz_id  = q.id
        WHERE s.completed = 1
    """
    if quiz_id:
        c.execute(base + " AND s.quiz_id=? ORDER BY s.completed_at DESC", (quiz_id,))
    else:
        c.execute(base + " ORDER BY s.completed_at DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def session_already_completed(agent_id: int, quiz_id: int) -> bool:
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM sessions WHERE agent_id=? AND quiz_id=? AND completed=1",
              (agent_id, quiz_id))
    exists = c.fetchone() is not None
    conn.close()
    return exists
