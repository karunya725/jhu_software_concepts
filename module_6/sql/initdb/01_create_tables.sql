CREATE TABLE IF NOT EXISTS applicants (
    p_id INTEGER PRIMARY KEY,
    program TEXT,
    comments TEXT,
    date_added DATE,
    url TEXT,
    status TEXT,
    term TEXT,
    us_or_international TEXT,
    gpa FLOAT,
    gre FLOAT,
    gre_v FLOAT,
    gre_aw FLOAT,
    degree TEXT,
    llm_generated_program TEXT,
    llm_generated_university TEXT
);

CREATE TABLE IF NOT EXISTS ingestion_watermark (
    source TEXT PRIMARY KEY,
    last_seen TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO ingestion_watermark (source, last_seen)
VALUES ('gradcafe', NULL)
ON CONFLICT (source) DO NOTHING;