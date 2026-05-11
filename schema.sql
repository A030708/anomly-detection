-- 1. Add columns to logs
ALTER TABLE logs ADD COLUMN IF NOT EXISTS structured_data JSONB DEFAULT '{}';
ALTER TABLE logs ADD COLUMN IF NOT EXISTS is_analyzed BOOLEAN DEFAULT FALSE;

-- 2. Ensure analysis table has all dashboard columns
ALTER TABLE analysis ADD COLUMN IF NOT EXISTS confidence_score FLOAT DEFAULT 0.0;
ALTER TABLE analysis ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();

-- 2. Add indexes so searching is 100x faster
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_logs_level ON logs (log_level);
CREATE INDEX IF NOT EXISTS idx_logs_source ON logs (source);
CREATE INDEX IF NOT EXISTS idx_logs_anomaly ON logs (is_anomaly) WHERE is_anomaly = TRUE;

-- 3. Add index to analysis table
CREATE INDEX IF NOT EXISTS idx_analysis_severity ON analysis (severity);

-- 4. Create Alerts table for the new dashboard
CREATE TABLE IF NOT EXISTS alerts (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    log_id BIGINT REFERENCES logs(id) ON DELETE CASCADE,
    severity VARCHAR(20),
    message TEXT,
    is_resolved BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON alerts (is_resolved);

-- 5. Refresh schema
NOTIFY pgrst, 'reload schema';
