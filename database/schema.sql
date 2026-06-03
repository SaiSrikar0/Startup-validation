-- ============================================================
-- 1. CREATE ENUM for startup status
-- ============================================================
CREATE TYPE startup_status AS ENUM ('Operating', 'Exited', 'Dead');


-- ============================================================
-- 2. CREATE TABLE
-- ============================================================
CREATE TABLE startups (
  id                    BIGSERIAL PRIMARY KEY,
  company               TEXT NOT NULL,
  status                startup_status NOT NULL,
  year_founded          INTEGER,
  description           TEXT,
  categories            TEXT,
  founders              TEXT,
  investors             TEXT,
  funding_rounds        TEXT,
  headquarters_city     TEXT,
  headquarters_state    TEXT,
  headquarters_country  TEXT,
  created_at            TIMESTAMPTZ DEFAULT NOW()
);


-- ============================================================
-- 3. INDEXES (for faster filtering/searching)
-- ============================================================
CREATE INDEX idx_startups_status        ON startups(status);
CREATE INDEX idx_startups_year_founded  ON startups(year_founded);
CREATE INDEX idx_startups_country       ON startups(headquarters_country);
CREATE INDEX idx_startups_company       ON startups(company);


-- ============================================================
-- 4. ENABLE ROW LEVEL SECURITY (recommended for Supabase)
-- ============================================================
ALTER TABLE startups ENABLE ROW LEVEL SECURITY;

-- Allow anyone to READ (public read access)
CREATE POLICY "Public read access"
  ON startups FOR SELECT
  USING (true);

-- Only authenticated users can INSERT
CREATE POLICY "Authenticated users can insert"
  ON startups FOR INSERT
  TO authenticated
  WITH CHECK (true);

-- Only authenticated users can UPDATE
CREATE POLICY "Authenticated users can update"
  ON startups FOR UPDATE
  TO authenticated
  USING (true);
