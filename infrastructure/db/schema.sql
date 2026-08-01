CREATE TABLE IF NOT EXISTS agent_memory (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(64) NOT NULL,
    key VARCHAR(256) NOT NULL,
    value TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(agent_name, key)
);

CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    assigned_to VARCHAR(64),
    created_by VARCHAR(64),
    title TEXT NOT NULL,
    description TEXT,
    status VARCHAR(32) DEFAULT 'pending',
    result TEXT,
    artifact_type VARCHAR(64),
    artifact_payload JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS papers (
    id SERIAL PRIMARY KEY,
    arxiv_id VARCHAR(64) UNIQUE,
    source VARCHAR(32) DEFAULT 'arxiv',
    external_id VARCHAR(128),
    title TEXT,
    authors TEXT,
    abstract TEXT,
    url TEXT,
    fetched_at TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS papers_source_external_id_idx ON papers(source, external_id);

CREATE TABLE IF NOT EXISTS token_usage (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(64) NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sprints (
    id SERIAL PRIMARY KEY,
    sprint_number INTEGER NOT NULL,
    question TEXT NOT NULL,
    outcome TEXT,
    status VARCHAR(32) DEFAULT 'in_progress',
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Reviewer sign-off, adopted from AI-Scientist-v2's non-author review gate:
-- a sprint may not close (see log_sprint.py) without an 'approved' row here.
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    sprint_id INTEGER REFERENCES sprints(id),
    task_id INTEGER REFERENCES tasks(id),
    reviewer_agent VARCHAR(64) NOT NULL,
    result VARCHAR(32) NOT NULL,
    notes JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Promising leads/findings worth revisiting later (papers, patterns, tools)
-- that don't fit neatly into "this sprint's outcome" -- a running backlog so
-- flagged items (e.g. "read this paper before committing to a solution
-- direction") don't get buried in a brief's prose and forgotten.
CREATE TABLE IF NOT EXISTS candidate_approaches (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    category VARCHAR(64),
    source_reference TEXT,
    flagged_by VARCHAR(64),
    sprint_id INTEGER REFERENCES sprints(id),
    priority VARCHAR(16) DEFAULT 'medium',
    status VARCHAR(32) DEFAULT 'open',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Process retrospectives, distinct from per-sprint content reviews: every 3
-- sprints, Ingrid audits the TEAM'S OWN METHOD across the covered sprints
-- (not any single sprint's findings) -- retrieval depth vs claims, backlog
-- hygiene, observation-vs-prescription conflation, etc. -- and proposes
-- structural fixes so the next similar gap surfaces to the team, not the
-- founder.
CREATE TABLE IF NOT EXISTS process_reviews (
    id SERIAL PRIMARY KEY,
    covers_sprint_from INTEGER NOT NULL,
    covers_sprint_to INTEGER NOT NULL,
    conducted_by VARCHAR(64) NOT NULL,
    findings TEXT,
    actions_taken TEXT,
    conducted_at TIMESTAMP DEFAULT NOW()
);

-- Backlog of candidate SPRINT TOPICS/QUESTIONS (distinct from
-- candidate_approaches, which is research leads found mid-work). This is
-- what sprint planning draws from: ideas as they occur to anyone on the
-- team, triaged and picked from at each planning session rather than
-- invented fresh each time.
CREATE TABLE IF NOT EXISTS sprint_backlog (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    proposed_by VARCHAR(64),
    priority VARCHAR(16) DEFAULT 'medium',
    status VARCHAR(32) DEFAULT 'open',
    resolved_sprint_id INTEGER REFERENCES sprints(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
