"""
=====================================================================
 Planificador de Estudios — Álgebra Vectorial y Matrices
 Universidad Don Bosco · Ciclo II-2026
=====================================================================
Stack  : Streamlit · PostgreSQL (Supabase) · Plotly
DB     : Supabase — configurar en .streamlit/secrets.toml
         o en Streamlit Cloud > App settings > Secrets
"""

import streamlit as st
import psycopg2
import psycopg2.extras
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import date
from urllib.parse import urlparse

# ─────────────────────────────────────────────
#  CONFIGURACIÓN DE PÁGINA  (debe ir PRIMERO)
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Álgebra Vectorial — Planificador",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  CONSTANTES
# ─────────────────────────────────────────────
UNIT_COLORS = {
    "Unidad I":   "#5b8ef0",
    "Unidad II":  "#4caf82",
    "Unidad III": "#e8a44a",
    "Unidad IV":  "#9b7de8",
    "Cierre":     "#8b8d9e",
}
STATUS_ICONS = {"Pendiente": "⬜", "Estudiado": "🟡", "Dominado": "✅"}

# ─────────────────────────────────────────────
#  DATOS DEL CURSO (extraídos del PDF oficial)
# ─────────────────────────────────────────────
COURSE_DATA = [
    # ── UNIDAD I ─────────────────────────────────────────────────────
    {
        "semana": 1, "label": "Sem 1", "dates": "22–27 jun",
        "unit": "Unidad I", "unit_full": "Números Complejos",
        "title": "Fundamentos de números complejos",
        "is_exam": False, "is_eval": False, "eval_pct": 0, "eval_label": "",
        "topics": [
            {"session": "Sesión 1", "content": "Concepto de números complejos y raíces de negativos"},
            {"session": "Sesión 1", "content": "Suma y resta de números imaginarios"},
            {"session": "Sesión 1", "content": "Potencias de la unidad imaginaria i"},
            {"session": "Sesión 1", "content": "Multiplicación de números complejos"},
            {"session": "Sesión 2", "content": "Igualdad de números complejos"},
            {"session": "Sesión 2", "content": "Números imaginarios puros y reales puros"},
            {"session": "Sesión 2", "content": "Plano complejo o plano de Argand"},
            {"session": "Sesión 2", "content": "Módulo de un número complejo"},
            {"session": "Sesión 2", "content": "Conjugado y opuesto de un número complejo"},
            {"session": "Sesión 2", "content": "Cociente de números complejos e inverso multiplicativo"},
        ],
    },
    {
        "semana": 2, "label": "Sem 2", "dates": "29 jun–4 jul",
        "unit": "Unidad I", "unit_full": "Números Complejos",
        "title": "Soluciones complejas + Discusión 1",
        "is_exam": False, "is_eval": True, "eval_pct": 10, "eval_label": "Discusión 1 (10%)",
        "topics": [
            {"session": "Sesión 1",    "content": "Soluciones complejas de ecuaciones polinomiales"},
            {"session": "Sesión 1",    "content": "Teoremas de soluciones complejas"},
            {"session": "Sesión 1",    "content": "División sintética para encontrar raíces"},
            {"session": "Discusión 1", "content": "⚡ EVALUACIÓN: Discusión 1 (10%) — complejos hasta soluciones complejas"},
        ],
    },
    {
        "semana": 3, "label": "Sem 3", "dates": "6–11 jul",
        "unit": "Unidad I", "unit_full": "Números Complejos",
        "title": "Forma trigonométrica, polar y De Moivre",
        "is_exam": False, "is_eval": False, "eval_pct": 0, "eval_label": "",
        "topics": [
            {"session": "Sesión 1", "content": "Números complejos en forma trigonométrica"},
            {"session": "Sesión 1", "content": "Números complejos en forma polar"},
            {"session": "Sesión 1", "content": "Producto y cociente en forma trigonométrica"},
            {"session": "Sesión 1", "content": "Producto y cociente en forma polar"},
            {"session": "Sesión 2", "content": "Teorema de De Moivre"},
            {"session": "Sesión 2", "content": "Potencia de un número complejo (forma trig. y polar)"},
            {"session": "Sesión 2", "content": "Raíz n-ésima de un número complejo"},
        ],
    },
    {
        "semana": 4, "label": "Sem 4", "dates": "13–18 jul",
        "unit": "Unidad I", "unit_full": "Números Complejos",
        "title": "Trabajo Autónomo 1 + Examen Parcial 1",
        "is_exam": True, "is_eval": True, "eval_pct": 17.5, "eval_label": "Autónomo 1 (2.5%) + Parcial 1 (15%)",
        "topics": [
            {"session": "Autónomo 1", "content": "⚡ EVALUACIÓN: Trabajo Autónomo 1 (2.5%) — forma trig. a raíces n-ésimas"},
            {"session": "Parcial 1",  "content": "🎯 EXAMEN PARCIAL 1 (15%) — forma trig., polar, De Moivre, raíces n-ésimas"},
        ],
    },
    # ── UNIDAD II ────────────────────────────────────────────────────
    {
        "semana": 5, "label": "Sem 5", "dates": "20–25 jul",
        "unit": "Unidad II", "unit_full": "Matrices y Determinantes",
        "title": "Matrices — tipos, operaciones, determinantes",
        "is_exam": False, "is_eval": False, "eval_pct": 0, "eval_label": "",
        "topics": [
            {"session": "Sesión 1", "content": "Tipos de matrices (cuadrada, nula, identidad, triangular…)"},
            {"session": "Sesión 1", "content": "Igualdad de matrices"},
            {"session": "Sesión 1", "content": "Suma y resta de matrices"},
            {"session": "Sesión 1", "content": "Producto de matrices y potencia de matriz cuadrada"},
            {"session": "Sesión 2", "content": "Determinante de una matriz"},
            {"session": "Sesión 2", "content": "Cálculo de determinantes (Sarrus, cofactores)"},
            {"session": "Sesión 2", "content": "Propiedades de los determinantes"},
        ],
    },
    {
        "semana": 6, "label": "Sem 6", "dates": "27–31 jul",
        "unit": "Unidad II", "unit_full": "Matrices y Determinantes",
        "title": "Matriz inversa, rango y ecuaciones matriciales",
        "is_exam": False, "is_eval": False, "eval_pct": 0, "eval_label": "",
        "topics": [
            {"session": "Sesión 1", "content": "Matriz inversa por la adjunta (clásica)"},
            {"session": "Sesión 1", "content": "Matriz inversa por operaciones elementales de fila"},
            {"session": "Sesión 1", "content": "Propiedades de la matriz inversa"},
            {"session": "Sesión 2", "content": "Ecuaciones matriciales"},
            {"session": "Sesión 2", "content": "Matrices escalonadas"},
            {"session": "Sesión 2", "content": "Rango por filas linealmente independientes"},
            {"session": "Sesión 2", "content": "Rango de una matriz por determinantes"},
        ],
    },
    {
        "semana": 7, "label": "Sem 7", "dates": "10–15 ago",
        "unit": "Unidad II", "unit_full": "Matrices y Determinantes",
        "title": "Rouché-Frobenius y sistemas de ecuaciones lineales",
        "is_exam": False, "is_eval": False, "eval_pct": 0, "eval_label": "",
        "topics": [
            {"session": "Sesión 1", "content": "Teorema de Rouché-Frobenius"},
            {"session": "Sesión 1", "content": "Sistemas compatibles determinados e indeterminados"},
            {"session": "Sesión 1", "content": "Sistemas de ecuaciones lineales incompatibles"},
            {"session": "Sesión 2", "content": "Resolución de SEL por la regla de Cramer"},
            {"session": "Sesión 2", "content": "Resolución de SEL por Gauss-Jordan"},
            {"session": "Sesión 2", "content": "Resolución de SEL por matriz inversa"},
            {"session": "Sesión 2", "content": "Problemas de aplicación de ingeniería"},
        ],
    },
    {
        "semana": 8, "label": "Sem 8", "dates": "17–22 ago",
        "unit": "Unidad II", "unit_full": "Matrices y Determinantes",
        "title": "Trabajo Autónomo 2 + Examen Parcial 2",
        "is_exam": True, "is_eval": True, "eval_pct": 22.5, "eval_label": "Autónomo 2 (2.5%) + Parcial 2 (20%)",
        "topics": [
            {"session": "Autónomo 2", "content": "⚡ EVALUACIÓN: Trabajo Autónomo 2 (2.5%) — tipos de matrices a aplicaciones"},
            {"session": "Parcial 2",  "content": "🎯 EXAMEN PARCIAL 2 (20%) — toda la Unidad II de matrices"},
        ],
    },
    # ── UNIDAD III ───────────────────────────────────────────────────
    {
        "semana": 9, "label": "Sem 9", "dates": "24–29 ago",
        "unit": "Unidad III", "unit_full": "Sistema Coordenado 2D",
        "title": "Geometría analítica — recta en el plano",
        "is_exam": False, "is_eval": False, "eval_pct": 0, "eval_label": "",
        "topics": [
            {"session": "Sesión 1", "content": "Distancia entre dos puntos"},
            {"session": "Sesión 1", "content": "Punto medio de un segmento"},
            {"session": "Sesión 1", "content": "División de un segmento en una razón dada"},
            {"session": "Sesión 1", "content": "Pendiente de una recta"},
            {"session": "Sesión 1", "content": "Rectas paralelas y perpendiculares"},
            {"session": "Sesión 1", "content": "Ángulo entre rectas"},
            {"session": "Sesión 2", "content": "Ecuaciones de la recta: punto-pendiente e intercepto"},
            {"session": "Sesión 2", "content": "Ecuación simétrica y general de la recta"},
            {"session": "Sesión 2", "content": "Distancia de un punto a una recta"},
            {"session": "Sesión 2", "content": "Distancia entre rectas paralelas"},
        ],
    },
    {
        "semana": 10, "label": "Sem 10", "dates": "31 ago–5 sep",
        "unit": "Unidad III", "unit_full": "Sistema Coordenado 2D",
        "title": "Cónicas — circunferencia y parábola",
        "is_exam": False, "is_eval": False, "eval_pct": 0, "eval_label": "",
        "topics": [
            {"session": "Sesión 1", "content": "La circunferencia: definición y elementos (centro, radio)"},
            {"session": "Sesión 1", "content": "Ecuación estándar y general de la circunferencia"},
            {"session": "Sesión 1", "content": "Gráficas de circunferencias"},
            {"session": "Sesión 2", "content": "La parábola: foco, directriz, vértice y eje"},
            {"session": "Sesión 2", "content": "Ecuaciones horizontal y vertical de la parábola"},
            {"session": "Sesión 2", "content": "Gráficas de parábolas"},
        ],
    },
    {
        "semana": 11, "label": "Sem 11", "dates": "7–12 sep",
        "unit": "Unidad III", "unit_full": "Sistema Coordenado 2D",
        "title": "Cónicas — elipse e hipérbola",
        "is_exam": False, "is_eval": False, "eval_pct": 0, "eval_label": "",
        "topics": [
            {"session": "Sesión 1", "content": "La elipse: focos, vértices, ejes y excentricidad"},
            {"session": "Sesión 1", "content": "Ecuaciones estándar de la elipse y gráficas"},
            {"session": "Sesión 2", "content": "La hipérbola: focos, vértices y asíntotas"},
            {"session": "Sesión 2", "content": "Ecuaciones estándar de la hipérbola y gráficas"},
        ],
    },
    {
        "semana": 12, "label": "Sem 12", "dates": "14–19 sep",
        "unit": "Unidad III", "unit_full": "Sistema Coordenado 2D",
        "title": "Trabajo Autónomo 3 + Examen Parcial 3",
        "is_exam": True, "is_eval": True, "eval_pct": 17.5, "eval_label": "Autónomo 3 (2.5%) + Parcial 3 (15%)",
        "topics": [
            {"session": "Autónomo 3", "content": "⚡ EVALUACIÓN: Trabajo Autónomo 3 (2.5%) — distancia a hipérbola"},
            {"session": "Parcial 3",  "content": "🎯 EXAMEN PARCIAL 3 (15%) — sistema coordenado 2D y cónicas"},
        ],
    },
    # ── UNIDAD IV ────────────────────────────────────────────────────
    {
        "semana": 13, "label": "Sem 13", "dates": "21–26 sep",
        "unit": "Unidad IV", "unit_full": "Vectores en el Plano y el Espacio",
        "title": "Sistema 3D — esfera y vectores fundamentales",
        "is_exam": False, "is_eval": False, "eval_pct": 0, "eval_label": "",
        "topics": [
            {"session": "Sesión 1", "content": "Ejes coordenados, planos y octantes en 3D"},
            {"session": "Sesión 1", "content": "Gráfica de puntos en el espacio"},
            {"session": "Sesión 1", "content": "Punto medio y puntos fuera del punto medio"},
            {"session": "Sesión 1", "content": "Ecuación de la esfera"},
            {"session": "Sesión 2", "content": "Vectores en 2D y 3D — definición y componentes"},
            {"session": "Sesión 2", "content": "Norma, vectores unitarios y fundamentales"},
            {"session": "Sesión 2", "content": "Igualdad, suma, resta y combinación lineal de vectores"},
            {"session": "Sesión 2", "content": "Producto escalar y forma alternativa"},
        ],
    },
    {
        "semana": 14, "label": "Sem 14", "dates": "28 sep–3 oct",
        "unit": "Unidad IV", "unit_full": "Vectores en el Plano y el Espacio",
        "title": "Proyecciones, producto vectorial y triple producto",
        "is_exam": False, "is_eval": False, "eval_pct": 0, "eval_label": "",
        "topics": [
            {"session": "Sesión 1", "content": "Ángulo entre vectores"},
            {"session": "Sesión 1", "content": "Vectores paralelos y perpendiculares"},
            {"session": "Sesión 1", "content": "Proyección vectorial y proyección escalar"},
            {"session": "Sesión 1", "content": "Ángulos directores y cosenos directores"},
            {"session": "Sesión 2", "content": "Producto vectorial: definición, cálculo y propiedades"},
            {"session": "Sesión 2", "content": "Triple producto escalar"},
            {"session": "Sesión 2", "content": "Aplicaciones: área de paralelogramo y volumen"},
        ],
    },
    {
        "semana": 15, "label": "Sem 15", "dates": "5–10 oct",
        "unit": "Unidad IV", "unit_full": "Vectores en el Plano y el Espacio",
        "title": "Rectas en el espacio 3D + Discusión 2",
        "is_exam": False, "is_eval": True, "eval_pct": 10, "eval_label": "Discusión 2 (10%)",
        "topics": [
            {"session": "Sesión 1",    "content": "Ecuación vectorial de la recta en 3D"},
            {"session": "Sesión 1",    "content": "Ecuaciones paramétricas de la recta"},
            {"session": "Sesión 1",    "content": "Ecuaciones simétricas e implícitas de la recta"},
            {"session": "Sesión 2",    "content": "Rectas paralelas y perpendiculares en 3D"},
            {"session": "Sesión 2",    "content": "Distancia de un punto a una recta"},
            {"session": "Sesión 2",    "content": "Rectas que se cortan y su punto de corte"},
            {"session": "Sesión 2",    "content": "Rectas cruzadas y distancia entre ellas"},
            {"session": "Discusión 2", "content": "⚡ EVALUACIÓN: Discusión 2 (10%) — toda la Unidad IV"},
        ],
    },
    {
        "semana": 16, "label": "Sem 16", "dates": "12–17 oct",
        "unit": "Unidad IV", "unit_full": "Vectores en el Plano y el Espacio",
        "title": "Planos en el espacio",
        "is_exam": False, "is_eval": False, "eval_pct": 0, "eval_label": "",
        "topics": [
            {"session": "Sesión 1", "content": "Ecuación vectorial y paramétrica del plano"},
            {"session": "Sesión 1", "content": "Ecuación punto-normal y general del plano"},
            {"session": "Sesión 2", "content": "Planos paralelos y perpendiculares"},
            {"session": "Sesión 2", "content": "Ángulo entre planos"},
            {"session": "Sesión 2", "content": "Distancia de un punto a un plano"},
            {"session": "Sesión 2", "content": "Distancia entre planos paralelos y gráficas"},
        ],
    },
    {
        "semana": 17, "label": "Sem 17", "dates": "19–24 oct",
        "unit": "Unidad IV", "unit_full": "Vectores en el Plano y el Espacio",
        "title": "Taller Discusión IV + Consolidación",
        "is_exam": False, "is_eval": True, "eval_pct": 2.5, "eval_label": "Taller Discusión IV (2.5%)",
        "topics": [
            {"session": "Taller",      "content": "⚡ EVALUACIÓN: Taller Discusión IV (2.5%) — rectas en el espacio"},
            {"session": "Consolidac.", "content": "Consolidación: ejercicios mezclados de todas las unidades"},
        ],
    },
    {
        "semana": 18, "label": "Sem 18", "dates": "26–31 oct",
        "unit": "Unidad IV", "unit_full": "Vectores en el Plano y el Espacio",
        "title": "Examen Parcial 4",
        "is_exam": True, "is_eval": True, "eval_pct": 15, "eval_label": "Parcial 4 (15%)",
        "topics": [
            {"session": "Repaso",    "content": "Repaso intensivo: rectas, planos y vectores 3D"},
            {"session": "Parcial 4", "content": "🎯 EXAMEN PARCIAL 4 (15%) — rectas hasta planos en 3D"},
        ],
    },
    {
        "semana": 19, "label": "Sem 19", "dates": "2–7 nov",
        "unit": "Cierre", "unit_full": "Cierre de Ciclo",
        "title": "Entrega de notas y diferidos",
        "is_exam": False, "is_eval": False, "eval_pct": 0, "eval_label": "",
        "topics": [
            {"session": "Cierre", "content": "Entrega de notas finales"},
            {"session": "Cierre", "content": "Exámenes diferidos (si aplica)"},
        ],
    },
]

# ─────────────────────────────────────────────
#  CONEXIÓN A SUPABASE (PostgreSQL)
# ─────────────────────────────────────────────

@st.cache_resource
def get_connection():
    """
    Conecta a Supabase (PostgreSQL) usando la URL del secrets.toml.

    Supabase genera URLs con IPv6 del tipo:
        postgresql://postgres.[REF]:[PASS]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
    o la clásica:
        postgresql://postgres:[PASS]@db.[REF].supabase.co:5432/postgres

    psycopg2.connect(dsn=url) maneja ambos formatos correctamente,
    a diferencia de urlparse que falla con corchetes IPv6.
    """
    url = st.secrets["supabase"]["url"]

    # Aseguramos que use el prefijo que psycopg2 entiende
    url = url.replace("postgres://", "postgresql://", 1)

    conn = psycopg2.connect(dsn=url, sslmode="require")
    conn.autocommit = False
    return conn


def run(sql: str, params=(), fetch: str = "none"):
    """
    Ejecuta una query con reconexión automática si la conexión cae.
    fetch: 'none' | 'one' | 'all'
    """
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params)
        conn.commit()
        if fetch == "one":  return cur.fetchone()
        if fetch == "all":  return cur.fetchall()
    except psycopg2.OperationalError:
        # Reconectar y reintentar una vez
        get_connection.clear()
        conn = get_connection()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params)
        conn.commit()
        if fetch == "one":  return cur.fetchone()
        if fetch == "all":  return cur.fetchall()


def read_df(sql: str, params=()) -> pd.DataFrame:
    """Ejecuta SELECT y devuelve DataFrame."""
    rows = run(sql, params, fetch="all")
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([dict(r) for r in rows])

# ─────────────────────────────────────────────
#  INICIALIZACIÓN DE TABLAS
# ─────────────────────────────────────────────

def init_db():
    """Crea tablas si no existen y las puebla la primera vez."""

    run("""
        CREATE TABLE IF NOT EXISTS weeks (
            id          SERIAL PRIMARY KEY,
            semana      INTEGER UNIQUE NOT NULL,
            label       TEXT,
            dates       TEXT,
            unit        TEXT,
            unit_full   TEXT,
            title       TEXT,
            is_exam     BOOLEAN DEFAULT FALSE,
            is_eval     BOOLEAN DEFAULT FALSE,
            eval_pct    REAL    DEFAULT 0,
            eval_label  TEXT    DEFAULT ''
        )
    """)

    run("""
        CREATE TABLE IF NOT EXISTS topics (
            id          SERIAL PRIMARY KEY,
            week_id     INTEGER NOT NULL REFERENCES weeks(id) ON DELETE CASCADE,
            session     TEXT,
            content     TEXT,
            status      TEXT DEFAULT 'Pendiente',
            note        TEXT DEFAULT '',
            updated_at  TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    run("""
        CREATE TABLE IF NOT EXISTS study_sessions (
            id           SERIAL PRIMARY KEY,
            week_id      INTEGER REFERENCES weeks(id) ON DELETE SET NULL,
            study_date   DATE,
            duration_min INTEGER DEFAULT 0,
            notes        TEXT    DEFAULT '',
            created_at   TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Poblar solo si la tabla está vacía
    count = run("SELECT COUNT(*) AS n FROM weeks", fetch="one")["n"]
    if count == 0:
        for w in COURSE_DATA:
            row = run("""
                INSERT INTO weeks (semana,label,dates,unit,unit_full,title,
                                   is_exam,is_eval,eval_pct,eval_label)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING id
            """, (
                w["semana"], w["label"], w["dates"],
                w["unit"], w["unit_full"], w["title"],
                w["is_exam"], w["is_eval"],
                w["eval_pct"], w.get("eval_label",""),
            ), fetch="one")
            week_id = row["id"]
            for t in w["topics"]:
                run("""
                    INSERT INTO topics (week_id, session, content)
                    VALUES (%s,%s,%s)
                """, (week_id, t["session"], t["content"]))

# ─────────────────────────────────────────────
#  QUERIES
# ─────────────────────────────────────────────

def fetch_weeks():
    rows = run("SELECT * FROM weeks ORDER BY semana", fetch="all")
    return [dict(r) for r in rows] if rows else []


def fetch_topics(week_id: int):
    rows = run("SELECT * FROM topics WHERE week_id=%s ORDER BY id", (week_id,), fetch="all")
    return [dict(r) for r in rows] if rows else []


def update_topic_status(topic_id: int, status: str):
    run("UPDATE topics SET status=%s, updated_at=NOW() WHERE id=%s", (status, topic_id))


def update_topic_note(topic_id: int, note: str):
    run("UPDATE topics SET note=%s, updated_at=NOW() WHERE id=%s", (note, topic_id))


def fetch_all_topics_df() -> pd.DataFrame:
    return read_df("""
        SELECT t.id, w.semana, w.label, w.unit, w.unit_full,
               w.title AS week_title, t.session, t.content,
               t.status, t.note, t.updated_at
        FROM topics t
        JOIN weeks w ON t.week_id = w.id
        ORDER BY w.semana, t.id
    """)


def get_progress_stats() -> dict:
    df = fetch_all_topics_df()
    if df.empty:
        return {"total":0,"pending":0,"studied":0,"mastered":0,"done":0,"pct":0}
    total    = len(df)
    mastered = len(df[df["status"] == "Dominado"])
    studied  = len(df[df["status"] == "Estudiado"])
    done     = mastered + studied
    return {"total":total,"pending":total-done,"studied":studied,
            "mastered":mastered,"done":done,
            "pct": round(done/total*100, 1) if total else 0}


def get_unit_progress() -> pd.DataFrame:
    df = fetch_all_topics_df()
    if df.empty:
        return pd.DataFrame()
    result = []
    for unit in df["unit"].unique():
        u        = df[df["unit"] == unit]
        total    = len(u)
        mastered = len(u[u["status"] == "Dominado"])
        studied  = len(u[u["status"] == "Estudiado"])
        result.append({"unit": unit, "unit_full": u["unit_full"].iloc[0],
                       "total": total, "mastered": mastered,
                       "studied": studied, "pending": total-mastered-studied})
    return pd.DataFrame(result)


def add_study_session(week_id, study_date, duration, notes):
    run("""
        INSERT INTO study_sessions (week_id, study_date, duration_min, notes)
        VALUES (%s,%s,%s,%s)
    """, (week_id, study_date, duration, notes))


def fetch_study_sessions() -> pd.DataFrame:
    return read_df("""
        SELECT s.id, w.label, w.unit, s.study_date,
               s.duration_min, s.notes, s.created_at
        FROM study_sessions s
        LEFT JOIN weeks w ON s.week_id = w.id
        ORDER BY s.study_date DESC
    """)

# ─────────────────────────────────────────────
#  CSS
# ─────────────────────────────────────────────
CUSTOM_CSS = """
<style>
[data-testid="stAppViewContainer"] { background:#0e0f14; color:#e8e9f0; }
[data-testid="stSidebar"]          { background:#161820 !important;
                                     border-right:1px solid rgba(255,255,255,0.08); }
[data-testid="stSidebar"] *        { color:#c8cadb !important; }

[data-testid="metric-container"] {
    background:#1e2029; border:1px solid rgba(255,255,255,0.08);
    border-radius:10px; padding:12px !important;
}
[data-testid="stExpander"] {
    background:#1e2029 !important;
    border:1px solid rgba(255,255,255,0.08) !important;
    border-radius:10px !important;
}
.stButton > button {
    background:#252733 !important; color:#e8e9f0 !important;
    border:1px solid rgba(255,255,255,0.12) !important;
    border-radius:8px !important; font-size:12px !important;
}
.stButton > button:hover { background:#2e3142 !important; }

.unit-badge {
    display:inline-block; font-size:11px; font-weight:700;
    padding:2px 9px; border-radius:20px; margin-right:5px;
}
.badge-u1 { background:rgba(91,142,240,.15); color:#5b8ef0; }
.badge-u2 { background:rgba(76,175,130,.15); color:#4caf82; }
.badge-u3 { background:rgba(232,164,74,.15); color:#e8a44a; }
.badge-u4 { background:rgba(155,125,232,.15);color:#9b7de8; }
.badge-ev { background:rgba(232,164,74,.15); color:#e8a44a; }
</style>
"""

# ─────────────────────────────────────────────
#  HELPERS UI
# ─────────────────────────────────────────────

def unit_badge(unit: str) -> str:
    cls = {"Unidad I":"badge-u1","Unidad II":"badge-u2",
           "Unidad III":"badge-u3","Unidad IV":"badge-u4"}.get(unit,"badge-u1")
    return f'<span class="unit-badge {cls}">{unit}</span>'


def chart_layout(fig, height=300):
    fig.update_layout(
        paper_bgcolor="#1e2029", plot_bgcolor="#1e2029",
        font=dict(color="#c8cadb", size=12),
        margin=dict(l=10,r=10,t=30,b=60),
        height=height,
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
    )
    return fig


def render_progress_chart():
    df = get_unit_progress()
    if df.empty: return
    fig = go.Figure()
    for label, color in [("Dominado ✅","#4caf82"),("Estudiado 🟡","#e8a44a"),("Pendiente ⬜","#2e3142")]:
        key = label.split()[0].lower()
        fig.add_trace(go.Bar(name=label, x=df["unit"], y=df[key],
                             marker_color=color, text=df[key], textposition="inside"))
    fig.update_layout(barmode="stack",
                      legend=dict(orientation="h",y=-0.25,bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(chart_layout(fig), use_container_width=True)


def render_donut():
    s = get_progress_stats()
    fig = go.Figure(go.Pie(
        labels=["Dominado","Estudiado","Pendiente"],
        values=[s["mastered"],s["studied"],s["pending"]],
        hole=0.65, textinfo="none",
        marker=dict(colors=["#4caf82","#e8a44a","#2e3142"]),
    ))
    fig.add_annotation(text=f"<b>{s['pct']}%</b>", x=0.5, y=0.5,
                       font_size=28, showarrow=False,
                       font=dict(color="#e8e9f0"))
    fig.update_layout(paper_bgcolor="#1e2029", showlegend=False,
                      margin=dict(l=0,r=0,t=0,b=0), height=200)
    st.plotly_chart(fig, use_container_width=True)


def render_cumulative_chart():
    df = fetch_all_topics_df()
    if df.empty: return
    rows, cum = [], 0
    for sem in sorted(df["semana"].unique()):
        sub  = df[df["semana"] == sem]
        done = len(sub[sub["status"].isin(["Estudiado","Dominado"])])
        cum += done
        rows.append({"Semana": f"Sem {int(sem)}", "Completados": cum})
    dfc = pd.DataFrame(rows)
    fig = go.Figure(go.Scatter(
        x=dfc["Semana"], y=dfc["Completados"],
        fill="tozeroy", fillcolor="rgba(91,142,240,0.1)",
        line=dict(color="#5b8ef0", width=2),
        mode="lines+markers", marker=dict(size=5, color="#5b8ef0"),
    ))
    st.plotly_chart(chart_layout(fig, height=220), use_container_width=True)


def render_topic_row(topic: dict):
    tid    = topic["id"]
    status = topic["status"]
    icon   = STATUS_ICONS.get(status, "⬜")

    c1, c2, c3 = st.columns([0.5, 4, 1.5])
    with c1: st.write(icon)
    with c2:
        st.write(f"**{topic['session']}** — {topic['content']}")
        if topic.get("note"):
            st.caption(f"📝 {topic['note']}")
    with c3:
        opts = ["Pendiente","Estudiado","Dominado"]
        new  = st.selectbox("", opts, index=opts.index(status),
                            key=f"sel_{tid}", label_visibility="collapsed")
        if new != status:
            update_topic_status(tid, new)
            st.rerun()

    with st.expander("✏️ Nota personal", expanded=bool(topic.get("note"))):
        new_note = st.text_area("", value=topic.get("note",""),
                                key=f"note_{tid}", height=68,
                                label_visibility="collapsed",
                                placeholder="Apuntes, dudas, recordatorios…")
        if st.button("💾 Guardar", key=f"save_{tid}"):
            update_topic_note(tid, new_note)
            st.success("Guardado ✅")
            st.rerun()

# ─────────────────────────────────────────────
#  PÁGINAS
# ─────────────────────────────────────────────

def page_dashboard():
    st.title("📊 Dashboard de progreso")
    s = get_progress_stats()

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Avance total",   f"{s['pct']}%")
    c2.metric("✅ Dominados",   s["mastered"])
    c3.metric("🟡 Estudiados",  s["studied"])
    c4.metric("⬜ Pendientes",  s["pending"])

    st.markdown("---")
    st.caption("Progreso acumulado del ciclo")
    st.progress(s["pct"] / 100)

    col_d, col_b = st.columns([1, 2])
    with col_d:
        st.caption("Estado global")
        render_donut()
    with col_b:
        st.caption("Avance por unidad")
        render_progress_chart()

    st.markdown("---")
    st.caption("Temas completados acumulados por semana")
    render_cumulative_chart()

    st.markdown("---")
    st.subheader("Resumen por unidad")
    df_u = get_unit_progress()
    if not df_u.empty:
        df_u["Avance %"] = ((df_u["mastered"]+df_u["studied"])/df_u["total"]*100).round(1)
        df_u = df_u.rename(columns={"unit":"Unidad","unit_full":"Nombre",
                                    "total":"Total","mastered":"Dominado",
                                    "studied":"Estudiado","pending":"Pendiente"})
        st.dataframe(df_u[["Unidad","Nombre","Total","Dominado","Estudiado","Pendiente","Avance %"]],
                     use_container_width=True, hide_index=True)


def page_weekly_plan():
    st.title("📅 Plan semanal")
    units        = ["Todas"] + list(dict.fromkeys(w["unit"] for w in COURSE_DATA))
    selected     = st.sidebar.selectbox("Filtrar por unidad", units)
    weeks_data   = fetch_weeks()
    if selected != "Todas":
        weeks_data = [w for w in weeks_data if w["unit"] == selected]

    for w in weeks_data:
        topics = fetch_topics(w["id"])
        done   = sum(1 for t in topics if t["status"] in ["Estudiado","Dominado"])
        total  = len(topics)
        pct    = int(done/total*100) if total else 0
        prefix = "🎯 " if w["is_exam"] else ("⚡ " if w["is_eval"] else "")
        label  = f"{prefix}**{w['label']}** · {w['title']}  —  {pct}% completado"

        with st.expander(label, expanded=False):
            ci, cp = st.columns([3,1])
            with ci:
                badge_html = unit_badge(w["unit"])
                if w["is_eval"]:
                    badge_html += f'<span class="unit-badge badge-ev">⚡ {w["eval_label"]}</span>'
                st.markdown(badge_html, unsafe_allow_html=True)
                st.caption(f"📆 {w['dates']}  ·  {done}/{total} temas")
            with cp:
                st.progress(pct/100)

            st.divider()
            for t in topics:
                render_topic_row(t)

            st.divider()
            if st.button("✅ Marcar todos como Dominado", key=f"all_{w['id']}"):
                for t in topics:
                    update_topic_status(t["id"], "Dominado")
                st.success("¡Todos marcados como Dominado!")
                st.rerun()


def page_topics_table():
    st.title("📋 Todos los temas")
    df = fetch_all_topics_df()
    if df.empty:
        st.info("Sin datos aún.")
        return

    units_f  = st.sidebar.multiselect("Unidades", df["unit"].unique().tolist(),
                                       default=df["unit"].unique().tolist())
    status_f = st.sidebar.multiselect("Estado", ["Pendiente","Estudiado","Dominado"],
                                       default=["Pendiente","Estudiado","Dominado"])
    df_f = df[(df["unit"].isin(units_f)) & (df["status"].isin(status_f))]
    st.caption(f"{len(df_f)} de {len(df)} temas")

    st.dataframe(
        df_f[["label","unit","session","content","status","note"]].rename(columns={
            "label":"Semana","unit":"Unidad","session":"Sesión",
            "content":"Tema","status":"Estado","note":"Nota",
        }),
        use_container_width=True, hide_index=True,
    )
    csv = df_f.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Exportar CSV", csv, "temas_algebra.csv", "text/csv")


def page_study_log():
    st.title("📓 Diario de estudio")
    weeks_data   = fetch_weeks()
    week_options = {f"{w['label']} — {w['title']}": w["id"] for w in weeks_data}

    st.subheader("Registrar sesión")
    with st.form("study_form"):
        c1, c2 = st.columns(2)
        with c1:
            chosen = st.selectbox("Semana trabajada", list(week_options.keys()))
            sdate  = st.date_input("Fecha", value=date.today())
        with c2:
            dur    = st.number_input("Duración (min)", 5, 480, 60, 5)
        notes  = st.text_area("¿Qué practiqué hoy?", height=90,
                              placeholder="Ej: Resolví 5 ejercicios de De Moivre…")
        if st.form_submit_button("💾 Guardar sesión"):
            add_study_session(week_options[chosen], str(sdate), dur, notes)
            st.success("Sesión guardada ✅")
            st.rerun()

    st.divider()
    st.subheader("Historial")
    df_log = fetch_study_sessions()
    if df_log.empty:
        st.info("Aún no hay sesiones registradas. ¡Empieza a estudiar!")
        return

    total_min = int(df_log["duration_min"].sum())
    st.metric("Total horas estudiadas", f"{total_min//60}h {total_min%60}m")

    st.dataframe(
        df_log[["study_date","label","unit","duration_min","notes"]].rename(columns={
            "study_date":"Fecha","label":"Semana","unit":"Unidad",
            "duration_min":"Min","notes":"Notas",
        }),
        use_container_width=True, hide_index=True,
    )

    if len(df_log) > 1:
        df_d = df_log.groupby("study_date")["duration_min"].sum().reset_index()
        fig  = px.bar(df_d, x="study_date", y="duration_min",
                      labels={"study_date":"Fecha","duration_min":"Minutos"},
                      color_discrete_sequence=["#5b8ef0"])
        st.plotly_chart(chart_layout(fig, 220), use_container_width=True)


def page_settings():
    st.title("⚙️ Configuración")

    st.subheader("Conexión a Supabase")
    try:
        url = st.secrets["supabase"]["url"]
        p   = urlparse(url)
        st.success(f"✅ Conectado a `{p.hostname}`")
    except Exception:
        st.error("No se encontró `supabase.url` en secrets.toml")
        st.code("""
# .streamlit/secrets.toml
[supabase]
url = "postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres"
        """, language="toml")

    st.divider()
    st.subheader("Exportar datos")
    df = fetch_all_topics_df()
    if not df.empty:
        st.download_button("⬇️ JSON completo",
                           df.to_json(orient="records", force_ascii=False),
                           "progreso_algebra.json", "application/json")
        st.download_button("⬇️ CSV completo",
                           df.to_csv(index=False).encode("utf-8"),
                           "progreso_algebra.csv", "text/csv")

    st.divider()
    st.subheader("Estadísticas de la BD")
    try:
        n_t = run("SELECT COUNT(*) AS n FROM topics",        fetch="one")["n"]
        n_w = run("SELECT COUNT(*) AS n FROM weeks",         fetch="one")["n"]
        n_s = run("SELECT COUNT(*) AS n FROM study_sessions",fetch="one")["n"]
        c1,c2,c3 = st.columns(3)
        c1.metric("Temas",    n_t)
        c2.metric("Semanas",  n_w)
        c3.metric("Sesiones", n_s)
    except Exception as e:
        st.warning(f"No se pudo consultar la BD: {e}")

    st.divider()
    st.subheader("Reiniciar progreso")
    st.warning("Esto restablece el estado de todos los temas a Pendiente y borra el diario.")
    if st.button("🔄 Reiniciar todo", type="secondary"):
        if st.checkbox("Confirmo que quiero borrar todo mi progreso"):
            run("UPDATE topics SET status='Pendiente', note=''")
            run("DELETE FROM study_sessions")
            st.success("Progreso reiniciado. Recarga la página.")

# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # Inicializar BD (solo la primera vez)
    try:
        init_db()
    except Exception as e:
        st.error(f"Error al conectar con Supabase: {e}")
        st.info("Configura tus credenciales en `.streamlit/secrets.toml`")
        st.code("""
[supabase]
url = "postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres"
        """, language="toml")
        st.stop()

    # Sidebar
    with st.sidebar:
        st.markdown("## 📐 Álgebra Vectorial")
        st.caption("UDB · Ciclo II-2026")
        st.divider()
        s = get_progress_stats()
        st.metric("Avance del curso", f"{s['pct']}%")
        st.progress(s["pct"] / 100)
        st.caption(f"✅ {s['mastered']} dom  ·  🟡 {s['studied']} est  ·  ⬜ {s['pending']} pend")
        st.divider()
        page = st.radio("Navegación",
                        ["📊 Dashboard","📅 Plan semanal","📋 Todos los temas",
                         "📓 Diario de estudio","⚙️ Configuración"],
                        label_visibility="collapsed")
        st.divider()
        st.caption("Coord.: Karen Denisse Umanzor Z.")
        st.caption("Dpto. de Ciencias Básicas")

    # Router
    if   page == "📊 Dashboard":        page_dashboard()
    elif page == "📅 Plan semanal":     page_weekly_plan()
    elif page == "📋 Todos los temas":  page_topics_table()
    elif page == "📓 Diario de estudio":page_study_log()
    elif page == "⚙️ Configuración":    page_settings()


if __name__ == "__main__":
    main()
