ALTER TABLE artifacts ADD COLUMN updated_at TEXT;
UPDATE artifacts SET updated_at = created_at WHERE updated_at IS NULL;

ALTER TABLE memory_sources ADD COLUMN project_id TEXT REFERENCES projects(id) ON DELETE CASCADE;
ALTER TABLE memory_sources ADD COLUMN title TEXT NOT NULL DEFAULT '';
ALTER TABLE memory_sources ADD COLUMN notes TEXT NOT NULL DEFAULT '';
ALTER TABLE memory_sources ADD COLUMN updated_at TEXT;
UPDATE memory_sources SET updated_at = created_at WHERE updated_at IS NULL;

CREATE INDEX idx_artifacts_project_updated
ON artifacts(project_id, updated_at DESC);
CREATE INDEX idx_memory_sources_project_updated
ON memory_sources(project_id, updated_at DESC);
