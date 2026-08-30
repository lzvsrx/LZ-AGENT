CREATE TABLE memory_retention_policies (
  category TEXT PRIMARY KEY,
  retention_days INTEGER CHECK(retention_days IS NULL OR retention_days >= 1),
  updated_at TEXT NOT NULL
);

INSERT INTO memory_retention_policies(category, retention_days, updated_at)
VALUES ('action_ledger', 365, CURRENT_TIMESTAMP), ('private_session', 1, CURRENT_TIMESTAMP);

CREATE INDEX idx_lessons_search
ON lessons_learned(project_id, updated_at DESC);
CREATE INDEX idx_suggestions_search
ON suggestions(project_id, created_at DESC);
