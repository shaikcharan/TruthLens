# TruthLens — Multilingual News Analysis & Media Literacy Platform

**TruthLens** is an independent, lightweight, multilingual media literacy platform engineered for rigorous news discourse analysis. It helps readers, journalists, and students evaluate online information by dissecting rhetorical manipulation, detecting propaganda techniques, extracting verifiable factual claims, and surfacing narrative framing across **English**, **Hindi**, **Telugu**, **Tamil**, and **Kannada** (with support for **Punjabi**).

> **Academic Milestone:** B.Tech Computer Science & Engineering Final-Year Capstone Project.  
> **Key Architectural Mandate:** Separates rhetorical analysis from factual verification. Emotional prose does not automatically render an article "fake"; linguistic framing and empirical truth require distinct investigative pipelines.

---

## 1. Problem Statement
The proliferation of algorithmically amplified digital news, partisan opinion pieces, and viral social media forwards has created an information landscape saturated with cognitive manipulation:
1. **Sensationalism & Fear-Mongering:** Articles frequently deploy hyperbolic adjectives and crisis rhetoric to drive engagement rather than inform.
2. **Conflation of Style and Veracity:** Mainstream fact-checking often commits the inverse fallacy: labeling opinion pieces as outright falsehoods or assuming that polished, neutral-sounding prose is factual.
3. **Linguistic Divide:** Most automated media literacy tools cater exclusively to English, leaving regional language readers (such as Hindi and Telugu speakers) vulnerable to targeted disinformation and unverified claims.
4. **Opaque AI "Black Boxes":** Many AI fact-checkers output a binary "Real/Fake" score without explaining what specific phrases constitute manipulation or what factual claims need verification.

---

## 2. Proposed Solution
TruthLens provides an explainable, multi-stage analytical dashboard that:
- **Dissects Persuasive Mechanics:** Flags specific techniques (e.g., *Emotional Appeal, Sensationalism, Ad Hominem, Cherry-Picking, False Dilemma, Unsupported Generalization*) and highlights the exact quoted text snippet.
- **Extracts Empirical Claims:** Isolates verifiable statistical data, event chronologies, and quotes, categorizing them into verifiable assertions.
- **Performs Evidence Verification:** Integrates with genuine open-access knowledge bases (Wikipedia OpenSearch) to find authentic corroboration. Uncorroborated statements are explicitly marked **Unverified**—TruthLens never fabricates citations or URLs.
- **Explains Media Framing:** Identifies narrative lenses (e.g., *Conflict Framing, Economic Burden, Crisis Urgency*) and highlights omitted context.
- **Guarantees Local Data Sovereignty:** Operates with embedded SQLite (`storage/truthlens.db`) on dedicated **Port 8765**, without telemetry, external user tracking, or cloud database dependencies.

---

## 3. Technology Stack

| Layer | Technologies | Justification |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript, Jinja2 | Zero Node.js build overhead; fast client rendering; accessible styling. |
| **Visualizations** | Chart.js (v4.4.2) | Lightweight client-side charting; bundled locally for 100% offline support. |
| **Backend Framework** | Python 3.11+, Flask 2.2.5, Werkzeug | Stable WSGI routing, minimal dependencies, beginner-friendly maintainability. |
| **Web Scraping & SSRF** | Requests, BeautifulSoup4, Socket, IPAddress | Secure HTTP streaming, DNS revalidation, private IP range blocking. |
| **AI Rhetoric Engine** | Google Gemini (`gemini-1.5-flash`) via `google-genai` & `google-generativeai` | High-fidelity multilingual reasoning with prompt-injection defense and JSON schema enforcement. |
| **Data Storage** | SQLite3 (Embedded) | ACID-compliant relational storage with foreign keys, zero configuration needed. |
| **Automated Testing** | PyTest (8.0+) | 42 unit and integration tests covering routes, database, SSRF, and AI pipelines. |

---

## 4. Project Directory Structure

```text
TruthLens_Project/
├── app.py                     # Main Flask application and HTTP route controller
├── config.py                  # Central configuration (Port 8765, models, paths, limits)
├── requirements.txt           # Pinned Python package dependencies
├── README.md                  # Comprehensive platform documentation
├── .env.example               # Configuration template for API keys & settings
├── .gitignore                 # Excludes cache, bytecode, virtualenv, and local database
├── RUN_TRUTHLENS.bat          # Primary Windows double-click launcher
├── RUN_TRUTHLENS.command      # macOS / Linux terminal launcher
│
├── backend/                   # Core business logic & analytical pipeline
│   ├── __init__.py
│   ├── article_extractor.py   # URL fetching, SSRF defense, HTML parsing & sanitization
│   ├── language_detector.py   # Deterministic Unicode script counter (En, Hi, Te, Pa)
│   ├── ai_analyzer.py         # Gemini API client, system prompt, JSON validation, mock mode
│   ├── evidence_checker.py    # Open reference verification (Wikipedia OpenSearch)
│   └── analysis_service.py    # End-to-end pipeline orchestrator
│
├── database/                  # Embedded relational data layer
│   ├── __init__.py
│   ├── schema.sql             # Relational DDL (analyses, claims, techniques, framing)
│   └── db_manager.py          # SQLite connection manager, atomic CRUD operations
│
├── templates/                 # Jinja2 HTML5 presentation templates
│   ├── base.html              # Core navigation layout, status pill, footer
│   ├── index.html             # Analysis submission interface (URL/Text, sample loaders)
│   ├── results.html           # Detailed analytical report view with claims & techniques
│   ├── dashboard.html         # Aggregated metrics & Chart.js live visualizations
│   ├── history.html           # Searchable analysis archive with deletion modal
│   └── settings.html          # Environment diagnostics, API status, connection test
│
├── static/                    # Client static assets
│   ├── css/
│   │   └── style.css          # Fact-checking theme (charcoal, off-white, navy accents)
│   └── js/
│       ├── app.js             # Client controller (tabs, progress bar, AJAX, modals)
│       ├── charts.js          # Chart.js rendering for dashboard
│       └── chart.umd.min.js   # Bundled Chart.js for 100% offline rendering
│
├── storage/                   # Persistent local storage directory
│   ├── README.md              # Storage manual, inspection, backup, and privacy notes
│   ├── .gitkeep
│   └── truthlens.db           # SQLite database file (created upon initialization)
│
├── tests/                     # Automated PyTest test suite (42 tests)
│   ├── __init__.py
│   ├── test_routes.py         # Flask HTTP routes, status codes, XSS sanitization
│   ├── test_database.py       # SQLite CRUD, foreign keys, cascade deletion, SQL injection
│   ├── test_extractor.py      # HTML parsing, title fallback, size limits, network errors
│   ├── test_validation.py     # URL validation, SSRF checks, private IP blocking
│   └── test_analysis.py       # AI parsing, mock fallback, evidence checker
│
├── scripts/                   # Developer & administrator helper utilities
│   ├── setup.bat              # Initial Windows virtualenv setup script
│   ├── check_environment.py   # System diagnostics & pre-flight checker
│   ├── init_database.py       # Database creation and schema rebuild utility
│   ├── inspect_database.py    # CLI tool to inspect stored analyses and claims
│   └── run_tests.bat          # Automated batch test runner
│
└── documentation/             # Comprehensive academic project documentation
    ├── ARCHITECTURE.md        # Technical pipeline architecture and security design
    ├── DATABASE.md            # Schema design, table definitions, and SQL queries
    ├── VIVA_QUESTIONS.md      # 25+ detailed viva questions and answers
    ├── TROUBLESHOOTING.md     # Error resolutions (port occupied, missing key, etc.)
    └── PROJECT_REPORT.md      # Complete university-standard B.Tech project report
```

---

## 5. Installation & Setup

### Prerequisites
- **Python 3.11** (or any compatible Python version `>= 3.9`).
- Windows, macOS, or Linux operating system.
- An internet connection for initial setup (or offline use if dependencies are pre-installed).

### Step 1: Extract or Clone Project
Extract the `TruthLens_Project/` folder to your desired directory.

### Step 2: Configure Environment Variables (Optional but Recommended)
TruthLens works out of the box in **Offline Demonstration Mode** even without an API key! To enable live Gemini AI queries:
1. In the project root, copy `.env.example` to `.env`:
   ```cmd
   copy .env.example .env
   ```
2. Open `.env` in any text editor and add your free Google AI Studio key:
   ```env
   GEMINI_API_KEY=AIzaSyYourActualKeyHere
   GEMINI_MODEL=gemini-1.5-flash
   PORT=8765
   HOST=127.0.0.1
   DATABASE_PATH=storage/truthlens.db
   REQUEST_TIMEOUT=15
   MAX_ARTICLE_CHARS=25000
   ENABLE_FACT_CHECK_SEARCH=true
   ```

---

## 6. How to Launch TruthLens

TruthLens is strictly isolated to **Port 8765** (`http://127.0.0.1:8765`) to prevent port conflicts with other applications.

### Method A: Windows Double-Click (Recommended)
Double-click `RUN_TRUTHLENS.bat` in File Explorer.
The launcher automatically:
1. Verifies Python 3.9+ is installed.
2. Creates the isolated virtual environment `.venv` (if not already present).
3. Installs pinned dependencies from `requirements.txt` (only on first run).
4. Creates the `storage/` directory and initializes `storage/truthlens.db`.
5. Confirms Port 8765 is available.
6. Starts the server and launches your default web browser to `http://127.0.0.1:8765`.

### Method B: Single Command Launch (Terminal)
After initial setup, launch directly from PowerShell or Command Prompt:

**Windows:**
```powershell
.\.venv\Scripts\python.exe app.py
```
*(Or if using your global Python environment: `python app.py`)*

**macOS / Linux:**
```bash
./.venv/bin/python app.py
```

### Method C: Initial Setup via Script
If setting up manually for the first time:
```cmd
scripts\setup.bat
```

Once running, access the application in your browser:
**URL:** [http://127.0.0.1:8765](http://127.0.0.1:8765)

---

## 7. Running Automated Tests

TruthLens includes a comprehensive PyTest test suite (42 tests) that runs completely offline using mocks for external APIs:

```bash
python -m pytest -q
```
Or run the Windows test launcher:
```cmd
scripts\run_tests.bat
```

**Verified Test Results:**
```text
..........................................                               [100%]
42 passed in 5.63s
```

Tested subsystems:
- Input validation (URL schemes, bounds, character counts)
- Server-Side Request Forgery (SSRF) defenses (private/local IP blocking, redirect interception)
- Deterministic multilingual Unicode script detection (English, Hindi, Telugu, Punjabi)
- HTML article parsing, title fallback, and boilerplate stripping
- AI JSON schema validation, code-fence stripping, and malformed payload recovery
- SQLite relational persistence, cascading deletions, and SQL injection safety
- Flask HTTP routes, 404/500 error handlers, and Jinja2 XSS escaping.

---

## 8. College Viva & Demonstration Guide

To demonstrate TruthLens during a college final-year presentation or viva:
1. Launch TruthLens via `RUN_TRUTHLENS.bat`.
2. On the **Analyze a Story** page, click any of the **Sample Demonstration Buttons**:
   - **English Sample:** Demonstrates sensational health claims and emotional manipulation.
   - **Hindi Sample (हिंदी):** Demonstrates policy claim extraction and Devanagari script processing.
   - **Telugu Sample (తెలుగు):** Demonstrates regional language discourse analysis and Telugu script handling.
3. Click **Start Discourse Analysis**. Observe the live progress indicator.
4. On the **Results Page**, walk the examiner through the 5 distinct analytical sections:
   - *Neutral Narrative Summary*
   - *Factual Claims & Verification Status* (highlight that external evidence is checked honestly; unverified claims are not marked "fake")
   - *Detected Rhetorical Techniques* (show exact quoted snippets)
   - *Narrative Framing Angles & Missing Context*
   - *Limitations & Reader Guidance*
5. Open the **Dashboard** to demonstrate live relational database aggregations with Chart.js.
6. Open the **Settings Page** to demonstrate security diagnostics and test the API connection.

---

## 9. Known Limitations & Responsible AI Notice
1. **Rhetoric vs. Veracity:** TruthLens evaluates persuasive language and argumentative framing. A scientifically true article can still use sensational language; an article full of falsehoods can be written in sober, professional prose. TruthLens separates style from empirical fact.
2. **Open Reference Verification:** Open knowledge sources (such as Wikipedia OpenSearch) provide initial contextual references for well-known historical or institutional claims. Fast-breaking breaking news or local unrecorded claims will naturally return **Unverified**, which accurately reflects the need for primary journalistic investigation.
3. **Paywalls & JavaScript SPAs:** TruthLens extracts public static HTML; it does not bypass paywalls or execute complex client-side JavaScript Single Page Applications.

---

## 10. License & Academic Attribution
Developed as an academic final-year capstone project. Open for educational, journalistic, and research media literacy use under the MIT License.
