-- ==============================================================================
-- TruthLens Database Schema
-- SQLite3 Relational Tables with Foreign Key Constraints & Cascade Deletion
-- ==============================================================================

PRAGMA foreign_keys = ON;

-- 1. Analyses Table: Stores metadata, neutral summary, and analysis results
CREATE TABLE IF NOT EXISTS analyses (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    publisher TEXT,
    publish_date TEXT,
    source_type TEXT NOT NULL CHECK(source_type IN ('url', 'text')),
    source_url TEXT,
    source_preview TEXT,
    language TEXT NOT NULL,
    analysis_mode TEXT DEFAULT 'local_offline',
    summary TEXT,
    overall_verdict TEXT,
    missing_context TEXT,
    limitations TEXT,
    recommended_steps TEXT, -- JSON array of suggested next steps
    raw_response_json TEXT,  -- Full structured JSON payload
    status TEXT NOT NULL DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Claims Table: Extracted factual statements and their external verification status
CREATE TABLE IF NOT EXISTS claims (
    id TEXT PRIMARY KEY,
    analysis_id TEXT NOT NULL,
    claim_text TEXT NOT NULL,
    source_passage TEXT,
    claim_type TEXT NOT NULL DEFAULT 'factual',
    verification_status TEXT NOT NULL DEFAULT 'Not yet verified' CHECK(
        verification_status IN (
            'Supported by evidence',
            'Contradicted by evidence',
            'Misleading or missing context',
            'Mixed evidence',
            'Not yet verified',
            'Supported by available evidence',
            'Contradicted by available evidence',
            'Partially supported',
            'Unverified',
            'Unable to analyze'
        )
    ),
    verification_notes TEXT,
    simple_explanation TEXT,
    evidence_quality TEXT DEFAULT 'Insufficient',
    verification_type TEXT DEFAULT 'Independently verified finding',
    claim_limitations TEXT,
    evidence_sources TEXT, -- JSON array of genuine retrieved citations
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (analysis_id) REFERENCES analyses (id) ON DELETE CASCADE
);

-- 3. Rhetorical Techniques Table: Detected propaganda/persuasive techniques
CREATE TABLE IF NOT EXISTS rhetorical_techniques (
    id TEXT PRIMARY KEY,
    analysis_id TEXT NOT NULL,
    technique_name TEXT NOT NULL,
    explanation TEXT,
    quote_snippet TEXT,
    FOREIGN KEY (analysis_id) REFERENCES analyses (id) ON DELETE CASCADE
);

-- 4. Framing Indicators Table: Noted ideological or narrative framing
CREATE TABLE IF NOT EXISTS framing_indicators (
    id TEXT PRIMARY KEY,
    analysis_id TEXT NOT NULL,
    indicator_name TEXT NOT NULL,
    explanation TEXT,
    FOREIGN KEY (analysis_id) REFERENCES analyses (id) ON DELETE CASCADE
);

-- Indexes for fast searching, dashboard aggregation, and sorting
CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_claims_analysis_id ON claims(analysis_id);
CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(verification_status);
CREATE INDEX IF NOT EXISTS idx_rhetorical_analysis_id ON rhetorical_techniques(analysis_id);
CREATE INDEX IF NOT EXISTS idx_rhetorical_name ON rhetorical_techniques(technique_name);
