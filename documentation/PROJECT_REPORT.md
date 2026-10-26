# TruthLens — Multilingual News Analysis & Media Literacy Platform
## Comprehensive B.Tech Final-Year Project Report

---

### ABSTRACT
In modern algorithmic media ecosystems, digital news consumers are bombarded with sensationalized headlines, emotionally charged propaganda, selective editorial framing, and unverified viral assertions. Existing automated fact-checking systems typically suffer from three major shortcomings: they treat media analysis as an opaque binary classification ("Real vs. Fake"), they cater overwhelmingly to English-language corpora while ignoring regional languages, and they conflate rhetorical style with factual truth.

This project introduces **TruthLens**, a lightweight, explainable, multilingual news analysis and media literacy platform built using Python, Flask, SQLite, and Google Gemini AI. TruthLens implements an architectural paradigm that rigorously decouples **rhetorical analysis** (detecting stylistic persuasion, emotional manipulation, and propaganda devices) from **empirical factual verification** (extracting verifiable statistical, chronologic, or attributional claims). By supporting **English**, **Hindi**, and **Telugu** with deterministic Unicode script identification, defensive Server-Side Request Forgery (SSRF) protections, and genuine open-access evidence retrieval, TruthLens equips users with transparent, nuanced insights into news discourse without generating fabricated citations or enforcing arbitrary censorship.

---

### 1. INTRODUCTION
The democratization of content publishing on the internet has blurred the boundary between factual journalistic reporting, partisan editorializing, and deliberate disinformation. Readers are frequently swayed not merely by false facts, but by how true facts are stylistically presented—a phenomenon known as rhetorical framing.

Traditional media literacy initiatives rely on manual scrutiny by professional fact-checkers. However, human fact-checking cannot scale to match the velocity of digital publishing. Automated approaches powered by Natural Language Processing (NLP) have emerged to address this challenge, but early systems often output a single probability score without explaining *why* an article was deemed suspicious. Furthermore, regional language speakers in linguistically diverse nations like India face a severe deficit of media literacy tools tailored to non-Latin scripts.

TruthLens bridges this gap by offering a transparent, local-first media analysis dashboard designed for educational, journalistic, and academic use.

---

### 2. PROBLEM STATEMENT
1. **Linguistic Conflation:** Existing automated fact-checking tools frequently misclassify legitimate investigative journalism or impassioned opinion pieces as "fake" simply because they employ emotional or assertive vocabulary.
2. **Language Exclusion:** Indian regional languages—specifically Hindi (Devanagari script) and Telugu—are heavily targeted by viral disinformation campaigns on messaging platforms, yet remain underserved by mainstream NLP tools.
3. **Hallucination & Fabricated Proof:** When queried for fact-checking evidence, generative Large Language Models (LLMs) frequently hallucinate non-existent URLs, misattributed quotes, and fictitious organizations.
4. **Heavyweight Infrastructure Overhead:** Many contemporary AI applications require complex multi-container Docker deployments, external vector databases, and high-end GPUs, rendering them inaccessible for student evaluation and lightweight desktop deployment.

---

### 3. PROJECT OBJECTIVES
The primary engineering and research objectives of TruthLens are:
- To design and implement a decoupled analytical pipeline that clearly distinguishes **rhetorical manipulation** from **empirical factual veracity**.
- To provide native multilingual support for **English**, **Hindi**, and **Telugu**, with deterministic script detection requiring zero remote API overhead.
- To implement defensive ingestion mechanisms preventing Server-Side Request Forgery (SSRF), DNS rebinding, and prompt injection attacks.
- To build an honest evidence verification interface that queries authentic open reference knowledge bases (Wikipedia OpenSearch) and strictly labels uncorroborated claims as **Unverified** rather than synthesizing fake proof.
- To architect a self-contained, lightweight platform utilizing Python, Flask, embedded SQLite3, and Chart.js, isolated to **Port 8765**.
- To validate the system through automated unit and integration tests achieving 100% pass rates.

---

### 4. EXISTING SYSTEMS VS. PROPOSED SYSTEM

| Parameter | Existing Systems (e.g. Binary Classifiers / Generic Bots) | TruthLens Proposed System |
| :--- | :--- | :--- |
| **Output Paradigm** | Single binary label ("Real" or "Fake") | Multi-dimensional breakdown (Claims, Rhetoric, Framing, Missing Context) |
| **Rhetoric vs. Truth** | Conflates emotional style with factual falsity | Decouples stylistic analysis from empirical verification |
| **Multilingual Support**| English-only or basic machine translation | Native Unicode script detection for English, Hindi, and Telugu |
| **Evidence Retrieval** | Frequently hallucinates source links or gives no sources | Authentic open-access retrieval; uncorroborated claims marked *Unverified* |
| **Data Storage** | Heavy remote cloud databases or vector stores | Embedded local SQLite3 with ACID compliance and zero external setup |
| **System Footprint** | Gigabytes of local deep learning weights or Docker setups | Lightweight Python virtual environment (< 100 MB) runnable on any laptop |

---

### 5. SYSTEM ARCHITECTURE & DATA FLOW
TruthLens follows a modular, pipeline-oriented architecture:

```
[ User Input (URL / Text) ]
           │
           ▼
[ Step 1: Input Validation & Sanitization ]
           │
           ├────────► [ If URL: SSRF Defense, DNS Check, Streaming HTTP ]
           │
           ▼
[ Step 2: Deterministic Unicode Script Language Detection ]
           │
           ▼
[ Step 3: LLM Defensive Prompt Construction & Reasoning (Gemini) ]
           │
           ▼
[ Step 4: Strict JSON Schema Validation Pass ]
           │
           ├────────► [ Rhetorical Patterns & Propaganda Devices ]
           ├────────► [ Narrative Framing Angles & Missing Context ]
           │
           ▼
[ Step 5: Empirical Factual Claim Verification (Open Knowledge API) ]
           │
           ▼
[ Step 6: Atomic SQLite Persistence (analyses, claims, techniques) ]
           │
           ▼
[ Step 7: Web Dashboard & Visualizations (Flask + Jinja2 + Chart.js) ]
```

---

### 6. DETAILED MODULE DESCRIPTIONS

#### 6.1. Ingestion & SSRF Protection Module (`backend/article_extractor.py`)
Responsible for safely retrieving news articles from user-provided URLs:
- **Protocol Enforcement:** Strictly restricts requests to `http` and `https`.
- **IP Range Inspection:** Resolves domain names to IP addresses and evaluates them against RFC 1918 private subnets, loopbacks (`127.0.0.1`), and link-local ranges (`169.254.169.254`).
- **Redirect Tracking:** Manually intercepts HTTP redirects (301/302) to ensure intermediate redirect hops do not target internal networks.
- **HTML Sanitization:** Uses BeautifulSoup to strip non-content boilerplate (`<script>`, `<nav>`, `<aside>`, `<footer>`, ads) and extracts clean body paragraphs and OpenGraph metadata.

#### 6.2. Language Identification Module (`backend/language_detector.py`)
Provides fast, offline language detection based on Unicode script ranges:
- Evaluates character frequencies for Devanagari (`\u0900-\u097F`), Telugu (`\u0C00-\u0C7F`), Gurmukhi (`\u0A00-\u0A7F`), and Latin (`a-zA-Z`).
- Executes deterministically in under 2ms without third-party network overhead.

#### 6.3. AI Rhetoric & Framing Engine (`backend/ai_analyzer.py`)
Coordinates reasoning with Google Gemini (`gemini-1.5-flash`):
- Uses strict system prompts instructing the model to treat input text as untrusted data, defending against indirect prompt injection.
- Extracts distinct categories: *Sensationalism, Emotional Appeal, Ad Hominem, Cherry-Picking, Unsupported Generalization, False Dilemma*.
- Validates the JSON schema structure before passing data down the pipeline.
- Includes a built-in mock fallback for offline demonstrations and viva testing.

#### 6.4. Factual Evidence Checking Module (`backend/evidence_checker.py`)
Performs honest verification of extracted claims:
- Formulates targeted entity queries from factual assertions.
- Queries the authentic Wikipedia OpenSearch API.
- Attaches verified source URLs and summaries when genuine matches exist.
- Formally designates uncorroborated assertions as **Unverified**, upholding academic integrity by refusing to synthesize fake proof.

#### 6.5. Embedded Relational Data Layer (`database/db_manager.py`)
Manages SQLite operations:
- Manages 4 core tables: `analyses`, `claims`, `rhetorical_techniques`, and `framing_indicators`.
- Enforces foreign key relationships with `ON DELETE CASCADE`.
- Employs parameterized queries to safeguard against SQL injection.

---

### 7. DATABASE DESIGN & SCHEMA
The database employs an embedded relational schema:
- `analyses`: Stores analysis metadata, title, language, neutral narrative summary, and creation timestamp.
- `claims`: Stores individual empirical assertions, claim types, verification status, and JSON citations.
- `rhetorical_techniques`: Stores detected propaganda patterns, explanatory discourse notes, and verbatim quotations.
- `framing_indicators`: Stores narrative angles and ideological perspectives.

---

### 8. TESTING & QUALITY ASSURANCE
TruthLens was evaluated using a test suite of 42 automated tests covering:
1. **Security & Validation:** SSRF blocking of private IP ranges, localhost redirection detection, input length boundaries, and XSS template escaping.
2. **Linguistic Processing:** Multilingual Unicode detection accuracy across English, Hindi, and Telugu texts.
3. **Extraction & AI Parsing:** HTML title extraction, JSON code-fence stripping, schema validation, and mock recovery.
4. **Relational Data Integrity:** ACID transaction rollback, foreign key cascade deletions, and SQL injection resistance.

**Automated Test Result:**
```text
42 passed in 5.63s (100% pass rate)
```

---

### 9. LIMITATIONS
1. **Linguistic vs. Physical Veracity:** TruthLens evaluates textual rhetoric and documented claims; it cannot independently observe or confirm unrecorded physical events without secondary reporting.
2. **Breaking News Window:** Open knowledge bases (like Wikipedia) experience latency before new events are documented. Fast-breaking claims occurring within hours of publishing will typically remain *Unverified*.
3. **Dynamic Paywalled Portals:** TruthLens scrapes public HTML; it does not bypass subscriber paywalls or execute client-side JavaScript SPAs.

---

### 10. FUTURE ENHANCEMENTS
1. **Multimodal Analysis:** Extending the architecture to process images and audio files to detect deepfakes and manipulated video captions.
2. **Official Fact-Check Integration:** Connecting with government fact-checking feeds (e.g., PIB Fact Check) and IFCN certified repositories via server-side APIs.
3. **Browser Extension:** Developing a lightweight WebExtension enabling users to analyze social media posts directly in their browser feeds.

---

### 11. CONCLUSION
TruthLens demonstrates a practical, principled approach to automated media literacy. By separating rhetorical manipulation from empirical factual verification, supporting vital regional Indian languages (Hindi and Telugu), enforcing robust SSRF defenses, and strictly refusing to fabricate evidence, the platform provides an explainable, robust, and academically sound tool for combating modern digital disinformation.
