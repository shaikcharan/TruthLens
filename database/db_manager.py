"""
Database Manager for TruthLens
Handles connection pooling, atomic transactions, schema initialization,
safe schema migrations, and CRUD operations.
"""

import sqlite3
import json
import uuid
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from config import Config

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def get_db_path(custom_path: Optional[str] = None) -> Path:
    """Resolve database path, ensuring parent directory exists."""
    path = Path(custom_path) if custom_path else Config.DATABASE_PATH
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return path


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Create a configured SQLite connection."""
    target_path = get_db_path(db_path)
    conn = sqlite3.connect(target_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def migrate_columns_if_missing(conn: sqlite3.Connection) -> None:
    """Safely adds missing columns to existing SQLite tables without losing data."""
    cursor = conn.cursor()

    # Check analyses columns
    cursor.execute("PRAGMA table_info(analyses);")
    analyses_cols = {r["name"] for r in cursor.fetchall()}
    
    analyses_to_add = [
        ("publisher", "TEXT"),
        ("publish_date", "TEXT"),
        ("analysis_mode", "TEXT DEFAULT 'local_offline'"),
        ("overall_verdict", "TEXT"),
    ]
    for col_name, col_type in analyses_to_add:
        if col_name not in analyses_cols:
            try:
                cursor.execute(f"ALTER TABLE analyses ADD COLUMN {col_name} {col_type};")
            except sqlite3.OperationalError:
                pass

    # Check claims columns
    cursor.execute("PRAGMA table_info(claims);")
    claims_cols = {r["name"] for r in cursor.fetchall()}

    claims_to_add = [
        ("source_passage", "TEXT"),
        ("simple_explanation", "TEXT"),
        ("evidence_quality", "TEXT DEFAULT 'Insufficient'"),
        ("verification_type", "TEXT DEFAULT 'Independently verified finding'"),
        ("claim_limitations", "TEXT"),
    ]
    for col_name, col_type in claims_to_add:
        if col_name not in claims_cols:
            try:
                cursor.execute(f"ALTER TABLE claims ADD COLUMN {col_name} {col_type};")
            except sqlite3.OperationalError:
                pass

    conn.commit()


def init_db(db_path: Optional[str] = None, reset: bool = False) -> None:
    """
    Initialize SQLite database tables from schema.sql.
    If reset is True, drops and recreates all tables.
    """
    target_path = get_db_path(db_path)
    if reset and target_path.exists():
        try:
            os.remove(target_path)
        except OSError:
            pass

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with get_connection(str(target_path)) as conn:
        conn.executescript(schema_sql)
        migrate_columns_if_missing(conn)
        conn.commit()


def normalize_status_for_reporting(status_str: str) -> str:
    """Normalizes status strings to standard plain English labels."""
    s = (status_str or "").strip()
    if not s:
        return "Not yet verified"
    valid_statuses = {
        "Supported by evidence",
        "Contradicted by evidence",
        "Misleading or missing context",
        "Mixed evidence",
        "Not yet verified",
        "Supported by available evidence",
        "Contradicted by available evidence",
        "Partially supported",
        "Unverified",
        "Unable to analyze",
    }
    if s in valid_statuses:
        return s
    s_lower = s.lower()
    if "supported by" in s_lower and "partially" not in s_lower:
        return "Supported by evidence"
    if "contradict" in s_lower:
        return "Contradicted by evidence"
    if "mislead" in s_lower or "missing context" in s_lower:
        return "Misleading or missing context"
    if "partially" in s_lower:
        return "Partially supported"
    if "mix" in s_lower:
        return "Mixed evidence"
    return "Not yet verified"


def to_db_compatible_status(status_str: str) -> str:
    """Ensures verification_status satisfies SQLite CHECK constraint across legacy and modern DBs."""
    s = (status_str or "").strip()
    s_lower = s.lower()
    if "contradict" in s_lower:
        return "Contradicted by available evidence"
    if "supported by" in s_lower and "partially" not in s_lower:
        return "Supported by available evidence"
    if "mislead" in s_lower or "partially" in s_lower or "mix" in s_lower:
        return "Partially supported"
    if "unable" in s_lower:
        return "Unable to analyze"
    return "Unverified"


def save_analysis(analysis_data: Dict[str, Any], db_path: Optional[str] = None) -> str:
    """
    Persist an analysis result atomically into the database.
    Returns the unique analysis ID.
    """
    analysis_id = analysis_data.get("id") or str(uuid.uuid4())

    title = analysis_data.get("title") or "Untitled Story Analysis"
    publisher = analysis_data.get("publisher") or "Direct Submission"
    publish_date = analysis_data.get("publish_date") or ""
    source_type = analysis_data.get("source_type", "text")
    source_url = analysis_data.get("source_url")
    source_preview = (analysis_data.get("source_preview") or "")[:300]
    language = analysis_data.get("language") or "English"
    analysis_mode = analysis_data.get("analysis_mode", "local_offline")
    summary = analysis_data.get("summary", "")
    overall_verdict = analysis_data.get("overall_verdict") or "Important claims remain unverified"
    missing_context = analysis_data.get("missing_context", "")
    limitations = analysis_data.get("limitations", "")
    
    recommended_steps = json.dumps(
        analysis_data.get("reader_next_steps") or analysis_data.get("recommended_verification_steps", []),
        ensure_ascii=False
    )
    raw_response = json.dumps(analysis_data, ensure_ascii=False)
    status = analysis_data.get("status", "completed")

    claims = analysis_data.get("factual_claims") or analysis_data.get("claims") or []
    persuasive_techniques = analysis_data.get("persuasive_techniques") or analysis_data.get("rhetorical_techniques") or []
    presentation_indicators = analysis_data.get("presentation_analysis") or analysis_data.get("framing_indicators") or []

    with get_connection(db_path) as conn:
        migrate_columns_if_missing(conn)
        cursor = conn.cursor()

        # Insert analysis record
        cursor.execute(
            """
            INSERT INTO analyses (
                id, title, publisher, publish_date, source_type, source_url, source_preview,
                language, analysis_mode, summary, overall_verdict, missing_context, limitations,
                recommended_steps, raw_response_json, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                analysis_id,
                title,
                publisher,
                publish_date,
                source_type,
                source_url,
                source_preview,
                language,
                analysis_mode,
                summary,
                overall_verdict,
                missing_context,
                limitations,
                recommended_steps,
                raw_response,
                status,
            ),
        )

        # Insert claims
        for claim in claims:
            claim_id = str(uuid.uuid4())
            claim_text = claim.get("claim", "")
            source_passage = claim.get("source_passage", "")
            claim_type = claim.get("claim_type", "factual")
            v_status = to_db_compatible_status(claim.get("verdict") or claim.get("verification_status"))
            simple_exp = claim.get("verdict_explanation") or claim.get("verification_notes", "")
            quality = claim.get("evidence_quality", "Insufficient")
            verif_type = claim.get("verification_type", "Independently verified finding")
            claim_limits = claim.get("limitations", "")
            evidence = json.dumps(
                claim.get("evidence_sources", []), ensure_ascii=False
            )

            cursor.execute(
                """
                INSERT INTO claims (
                    id, analysis_id, claim_text, source_passage, claim_type,
                    verification_status, verification_notes, simple_explanation,
                    evidence_quality, verification_type, claim_limitations, evidence_sources
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    claim_id,
                    analysis_id,
                    claim_text,
                    source_passage,
                    claim_type,
                    v_status,
                    simple_exp,
                    simple_exp,
                    quality,
                    verif_type,
                    claim_limits,
                    evidence,
                ),
            )

        # Insert persuasive techniques
        for tech in persuasive_techniques:
            tech_id = str(uuid.uuid4())
            t_name = tech.get("technique", "Persuasive Technique")
            t_exp = tech.get("explanation", "")
            t_quote = tech.get("quote", "") or tech.get("quote_snippet", "")

            cursor.execute(
                """
                INSERT INTO rhetorical_techniques (
                    id, analysis_id, technique_name, explanation, quote_snippet
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (tech_id, analysis_id, t_name, t_exp, t_quote),
            )

        # Insert presentation / framing indicators
        for frame in presentation_indicators:
            frame_id = str(uuid.uuid4())
            f_name = frame.get("aspect") or frame.get("indicator_name") or frame.get("indicator", "Presentation")
            f_exp = frame.get("explanation", "")

            cursor.execute(
                """
                INSERT INTO framing_indicators (
                    id, analysis_id, indicator_name, explanation
                ) VALUES (?, ?, ?, ?)
                """,
                (frame_id, analysis_id, f_name, f_exp),
            )

        conn.commit()

    return analysis_id


def get_analysis(analysis_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve full analysis report by ID including unpacked structured data."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,))
        row = cursor.fetchone()
        if not row:
            return None

        analysis = dict(row)

        # If raw_response_json exists, unpack all rich fields
        if analysis.get("raw_response_json"):
            try:
                raw_data = json.loads(analysis["raw_response_json"])
                for k, v in raw_data.items():
                    if k not in analysis or not analysis[k]:
                        analysis[k] = v
            except Exception:
                pass

        # Normalize recommended steps
        try:
            analysis["reader_next_steps"] = json.loads(
                analysis.get("recommended_steps") or "[]"
            )
            analysis["recommended_verification_steps"] = analysis["reader_next_steps"]
        except Exception:
            analysis["reader_next_steps"] = []
            analysis["recommended_verification_steps"] = []

        # Fetch claims from database table
        cursor.execute(
            "SELECT * FROM claims WHERE analysis_id = ? ORDER BY created_at ASC",
            (analysis_id,),
        )
        db_claims = []
        for c in cursor.fetchall():
            c_dict = dict(c)
            try:
                c_dict["evidence_sources"] = json.loads(
                    c_dict.get("evidence_sources") or "[]"
                )
            except Exception:
                c_dict["evidence_sources"] = []

            # Normalize verdict
            raw_v = c_dict.get("verification_status", "Unverified")
            c_dict["verdict"] = normalize_status_for_reporting(raw_v)
            c_dict["verification_status"] = raw_v
            c_dict["claim"] = c_dict.get("claim_text", "")
            db_claims.append(c_dict)

        # Prefer unpacked rich claims if available and matching count
        if analysis.get("factual_claims") and len(analysis["factual_claims"]) == len(db_claims):
            analysis["claims"] = analysis["factual_claims"]
        elif db_claims:
            analysis["claims"] = db_claims
            analysis["factual_claims"] = db_claims
        else:
            analysis["claims"] = []
            analysis["factual_claims"] = []

        # Fetch techniques
        cursor.execute(
            "SELECT * FROM rhetorical_techniques WHERE analysis_id = ?",
            (analysis_id,),
        )
        tech_rows = [dict(t) for t in cursor.fetchall()]
        source_techs = analysis.get("persuasive_techniques") or analysis.get("rhetorical_techniques") or tech_rows
        formatted_techs = []
        for t in source_techs:
            t_name = t.get("technique") or t.get("technique_name") or "Persuasive Device"
            t_exp = t.get("explanation", "")
            t_quote = t.get("quote") or t.get("quote_snippet", "")
            t_effect = t.get("likely_effect") or "Documented in source text."
            formatted_techs.append({
                "technique": t_name,
                "technique_name": t_name,
                "explanation": t_exp,
                "quote": t_quote,
                "quote_snippet": t_quote,
                "likely_effect": t_effect,
            })
        analysis["persuasive_techniques"] = formatted_techs
        analysis["rhetorical_techniques"] = formatted_techs

        # Fetch framing / presentation
        cursor.execute(
            "SELECT * FROM framing_indicators WHERE analysis_id = ?",
            (analysis_id,),
        )
        frame_rows = [dict(f) for f in cursor.fetchall()]
        if not analysis.get("presentation_analysis"):
            analysis["presentation_analysis"] = [
                {
                    "aspect": f["indicator_name"],
                    "explanation": f["explanation"]
                }
                for f in frame_rows
            ]
        analysis["framing_indicators"] = analysis["presentation_analysis"]

        # Ensure purpose structure exists
        if not analysis.get("possible_purpose"):
            analysis["possible_purpose"] = {
                "suggested_purpose": "Informing readers about public developments or viral claims.",
                "supporting_evidence": "Derived from source narrative structure.",
                "intent_disclaimer": "Possible effect: this content may shape reader perception. The creator's actual intention is unknown."
            }

        if not analysis.get("overall_verdict"):
            analysis["overall_verdict"] = "Important claims remain unverified"

        return analysis


def list_analyses(
    search_query: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List historical analyses with counts and search filter."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        base_sql = """
            SELECT
                a.id,
                a.title,
                a.publisher,
                a.publish_date,
                a.source_type,
                a.source_url,
                a.source_preview,
                a.language,
                a.analysis_mode,
                a.overall_verdict,
                a.status,
                a.created_at,
                COUNT(DISTINCT c.id) AS claims_count,
                COUNT(DISTINCT r.id) AS techniques_count
            FROM analyses a
            LEFT JOIN claims c ON a.id = c.analysis_id
            LEFT JOIN rhetorical_techniques r ON a.id = r.analysis_id
        """

        params: List[Any] = []
        if search_query:
            base_sql += " WHERE a.title LIKE ? OR a.source_preview LIKE ? OR a.language LIKE ? OR a.publisher LIKE ?"
            wildcard = f"%{search_query.strip()}%"
            params.extend([wildcard, wildcard, wildcard, wildcard])

        base_sql += " GROUP BY a.id ORDER BY a.created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(base_sql, params)
        return [dict(r) for r in cursor.fetchall()]


def delete_analysis(analysis_id: str, db_path: Optional[str] = None) -> bool:
    """Delete an analysis record. Relational tables are cleaned up via ON DELETE CASCADE."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
        conn.commit()
        return cursor.rowcount > 0


def get_dashboard_stats(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Calculate aggregated metrics directly from real SQLite records with clean verdict mapping."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # Total analyses
        cursor.execute("SELECT COUNT(*) AS total FROM analyses")
        total_analyses = cursor.fetchone()["total"]

        # Total claims
        cursor.execute("SELECT COUNT(*) AS total FROM claims")
        total_claims = cursor.fetchone()["total"]

        # Total detected techniques
        cursor.execute("SELECT COUNT(*) AS total FROM rhetorical_techniques")
        total_techniques = cursor.fetchone()["total"]

        # Claim verification distribution
        cursor.execute("SELECT verification_status FROM claims")
        status_dist: Dict[str, int] = {}
        for row in cursor.fetchall():
            v_val = row["verification_status"] or "Not yet verified"
            status_dist[v_val] = status_dist.get(v_val, 0) + 1

        # Remove zero entries to prevent empty chart wedges
        active_status_dist = {k: v for k, v in status_dist.items() if v > 0}

        # Top persuasive writing techniques distribution
        cursor.execute(
            """
            SELECT technique_name, COUNT(*) AS count
            FROM rhetorical_techniques
            WHERE technique_name NOT LIKE 'None detected%'
            GROUP BY technique_name
            ORDER BY count DESC
            LIMIT 8
            """
        )
        techniques_dist = [
            {"technique": row["technique_name"], "count": row["count"]}
            for row in cursor.fetchall()
        ]

        # Language distribution
        cursor.execute(
            """
            SELECT language, COUNT(*) AS count
            FROM analyses
            GROUP BY language
            ORDER BY count DESC
            """
        )
        languages_dist = [
            {"language": row["language"], "count": row["count"]}
            for row in cursor.fetchall()
        ]

        # Recent 5 analyses
        cursor.execute(
            """
            SELECT id, title, language, created_at, status
            FROM analyses
            ORDER BY created_at DESC
            LIMIT 5
            """
        )
        recent_analyses = [dict(row) for row in cursor.fetchall()]

        return {
            "total_analyses": total_analyses,
            "total_claims": total_claims,
            "total_techniques": total_techniques,
            "status_distribution": active_status_dist,
            "techniques_distribution": techniques_dist,
            "languages_distribution": languages_dist,
            "recent_analyses": recent_analyses,
        }


def check_db_health(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Check health, connectivity, and table integrity."""
    target_path = get_db_path(db_path)
    if not target_path.exists():
        return {
            "healthy": False,
            "exists": False,
            "path": str(target_path),
            "error": "Database file does not exist. Please run initialization.",
        }

    try:
        with get_connection(str(target_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [r["name"] for r in cursor.fetchall() if not r["name"].startswith("sqlite_")]
            size_bytes = os.path.getsize(target_path)
            return {
                "healthy": True,
                "exists": True,
                "path": str(target_path),
                "size_kb": round(size_bytes / 1024, 2),
                "tables": tables,
                "table_count": len(tables),
            }
    except Exception as exc:
        return {
            "healthy": False,
            "exists": True,
            "path": str(target_path),
            "error": str(exc),
        }
