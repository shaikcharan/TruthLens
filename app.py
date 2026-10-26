"""
TruthLens — Multilingual News Analysis & Media Literacy Platform
Main Flask Application Server
Configured for port 8765 exclusively.
"""

import sys
import os
import socket
from pathlib import Path
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    flash,
    abort,
)

# Ensure project root is in Python sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import Config
from database.db_manager import (
    init_db,
    get_analysis,
    list_analyses,
    delete_analysis,
    get_dashboard_stats,
    check_db_health,
)
from backend.analysis_service import analyze_story
from backend.article_extractor import ExtractorError, SSRFBlockedError
from backend.ai_analyzer import AIAnalyzerError, call_gemini_api

app = Flask(__name__)
app.config["SECRET_KEY"] = Config.SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024  # 4MB max request payload


@app.before_request
def ensure_database_ready():
    """Ensure SQLite database schema is initialized on first request."""
    if not Config.DATABASE_PATH.exists():
        bundled_db = Config.STORAGE_DIR / "truthlens.db"
        is_temp_env = os.getenv("VERCEL") or "tmp" in str(Config.DATABASE_PATH).lower() or "temp" in str(Config.DATABASE_PATH).lower()
        if bundled_db.exists() and is_temp_env:
            try:
                import shutil
                Config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(bundled_db, Config.DATABASE_PATH)
            except Exception:
                init_db()
        else:
            init_db()


# ==============================================================================
# UI Web Routes
# ==============================================================================


@app.route("/")
def index():
    """Main analysis page: Enter URL or paste text in English, Hindi, or Telugu."""
    return render_template(
        "index.html",
        languages=Config.SUPPORTED_LANGUAGES,
        api_configured=Config.is_api_key_configured(),
        masked_api_key=Config.get_masked_api_key(),
    )


@app.route("/results/<analysis_id>")
def results(analysis_id):
    """Detailed analytical breakdown for a specific analyzed news story."""
    analysis = get_analysis(analysis_id)
    if not analysis:
        if request.args.get("format") == "json":
            return jsonify({"success": False, "error": "Record not found"}), 404
        flash("The requested analysis record was not found.", "warning")
        return redirect(url_for("history_page"))

    if request.args.get("format") == "json":
        return jsonify(analysis)

    return render_template("results.html", analysis=analysis)


@app.route("/dashboard")
def dashboard():
    """Analytics dashboard with aggregate metrics and Chart.js visualizations."""
    stats = get_dashboard_stats()
    return render_template("dashboard.html", stats=stats)


@app.route("/history")
def history_page():
    """Searchable historical records of analyzed stories."""
    query = request.args.get("q", "").strip()
    records = list_analyses(search_query=query if query else None)
    return render_template("history.html", records=records, search_query=query)


@app.route("/settings")
def settings():
    """System status, API configuration status, and database details."""
    db_health = check_db_health()
    return render_template(
        "settings.html",
        api_configured=Config.is_api_key_configured(),
        masked_api_key=Config.get_masked_api_key(),
        model_name=Config.GEMINI_MODEL,
        port=Config.PORT,
        host=Config.HOST,
        db_health=db_health,
        db_path=str(Config.DATABASE_PATH),
    )


# ==============================================================================
# JSON API Endpoints
# ==============================================================================


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    """Endpoint for initiating a news story analysis."""
    data = request.get_json(silent=True) or request.form.to_dict()

    source_type = data.get("source_type", "text").strip().lower()
    content_input = data.get("content_input", "").strip()
    selected_language = data.get("selected_language", "auto").strip().lower()
    custom_title = data.get("custom_title", "").strip()

    if not content_input:
        return jsonify({"success": False, "error": "Please provide article text or a URL."}), 400

    try:
        report = analyze_story(
            source_type=source_type,
            content_input=content_input,
            selected_language=selected_language,
            custom_title=custom_title,
        )
        return jsonify(
            {
                "success": True,
                "analysis_id": report["id"],
                "redirect_url": url_for("results", analysis_id=report["id"]),
            }
        )
    except SSRFBlockedError as ssrf_err:
        return jsonify({"success": False, "error": f"Security Notice: {str(ssrf_err)}"}), 400
    except ExtractorError as ext_err:
        return jsonify({"success": False, "error": f"Content Extraction Error: {str(ext_err)}"}), 400
    except AIAnalyzerError as ai_err:
        return jsonify({"success": False, "error": f"AI Processing Error: {str(ai_err)}"}), 502
    except Exception as exc:
        return jsonify({"success": False, "error": f"An unexpected error occurred: {str(exc)}"}), 500


@app.route("/api/dashboard-data")
def api_dashboard_data():
    """JSON endpoint for Chart.js live rendering."""
    stats = get_dashboard_stats()
    return jsonify(stats)


@app.route("/api/history/<analysis_id>", methods=["DELETE", "POST"])
def api_delete_history(analysis_id):
    """Deletes an analysis record and associated claims/techniques."""
    success = delete_analysis(analysis_id)
    if success:
        return jsonify({"success": True, "message": "Record deleted successfully."})
    return jsonify({"success": False, "error": "Record not found or already deleted."}), 404


@app.route("/api/test-connection", methods=["POST"])
def api_test_connection():
    """Tests connection to Gemini API or reports mock readiness."""
    if not Config.is_api_key_configured():
        return jsonify(
            {
                "success": True,
                "mode": "offline_mock",
                "message": (
                    "TruthLens is running in Offline Demonstration Mode. "
                    "GEMINI_API_KEY is not set. All functions and dashboard features are active with realistic mock analysis."
                ),
            }
        )

    try:
        # Send a minimal ping prompt
        test_prompt = "Output JSON: {\"status\": \"ok\", \"ping\": \"pong\"}"
        reply = call_gemini_api(test_prompt)
        return jsonify(
            {
                "success": True,
                "mode": "live_gemini",
                "message": f"Successfully connected to Gemini API using model '{Config.GEMINI_MODEL}'.",
            }
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "mode": "error",
                    "error": f"Connection to Gemini API failed: {str(e)}",
                }
            ),
            500,
        )


@app.route("/api/health")
def api_health():
    """Health check endpoint for automated testing and status monitoring."""
    db_status = check_db_health()
    return jsonify(
        {
            "status": "healthy" if db_status.get("healthy") else "degraded",
            "project": Config.PROJECT_NAME,
            "version": Config.VERSION,
            "port": Config.PORT,
            "api_key_configured": Config.is_api_key_configured(),
            "database": db_status,
        }
    )


# ==============================================================================
# Error Handlers
# ==============================================================================


@app.errorhandler(404)
def page_not_found(e):
    return render_template("base.html", error_message="Page Not Found (404)"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("base.html", error_message="Internal Server Error (500)"), 500


# ==============================================================================
# Server Startup Verification
# ==============================================================================


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if the designated port is already occupied."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False
        except OSError:
            return True


def main():
    """Main launch entrypoint with strict port isolation."""
    # Ensure database is initialized before starting server
    init_db()

    target_port = Config.PORT
    target_host = Config.HOST

    if is_port_in_use(target_port, target_host):
        print(
            f"Port {target_port} is already in use. "
            f"Close the existing TruthLens instance or select a different port in config.py."
        )
        sys.exit(1)

    print(f"TruthLens is running at http://{target_host}:{target_port}")
    app.run(host=target_host, port=target_port, debug=False)


if __name__ == "__main__":
    main()
