CREATE TABLE projects (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, objective TEXT, stack_json TEXT NOT NULL DEFAULT '{}',
  path TEXT, state TEXT NOT NULL DEFAULT 'active', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE project_decisions (
  id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  decision TEXT NOT NULL, reason TEXT, alternatives_json TEXT NOT NULL DEFAULT '[]', result TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE agent_actions (
  id TEXT PRIMARY KEY, project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
  command TEXT NOT NULL, tool TEXT NOT NULL, parameters_json TEXT NOT NULL DEFAULT '{}',
  result_json TEXT NOT NULL DEFAULT '{}', error TEXT, status TEXT NOT NULL,
  permission TEXT, model TEXT, duration_ms INTEGER, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE INDEX idx_agent_actions_created ON agent_actions(created_at DESC);
CREATE INDEX idx_agent_actions_project ON agent_actions(project_id, created_at DESC);
CREATE TABLE lessons_learned (
  id TEXT PRIMARY KEY, project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
  problem TEXT NOT NULL, solution TEXT NOT NULL, context TEXT, evidence TEXT,
  confidence REAL NOT NULL CHECK(confidence BETWEEN 0 AND 1), global_scope INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE suggestions (
  id TEXT PRIMARY KEY, project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
  title TEXT NOT NULL, description TEXT NOT NULL, priority TEXT NOT NULL, impact TEXT,
  justification TEXT NOT NULL, source_lesson_id TEXT REFERENCES lessons_learned(id) ON DELETE SET NULL,
  decision TEXT NOT NULL DEFAULT 'pending', created_at TEXT NOT NULL
);
CREATE TABLE artifacts (
  id TEXT PRIMARY KEY, project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
  kind TEXT NOT NULL, path TEXT NOT NULL, checksum TEXT, metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);
CREATE TABLE user_preferences (
  key TEXT PRIMARY KEY, value_json TEXT NOT NULL, authorized_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE memory_sources (
  id TEXT PRIMARY KEY, source_type TEXT NOT NULL, source_ref TEXT, consent TEXT NOT NULL,
  retention TEXT NOT NULL, scope TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE checkpoints (
  id TEXT PRIMARY KEY, project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
  commit_hash TEXT, files_json TEXT NOT NULL DEFAULT '[]', diff TEXT, test_result TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE tech_versions (
  technology TEXT PRIMARY KEY, version TEXT NOT NULL, verified_at TEXT NOT NULL,
  source TEXT, approved INTEGER NOT NULL DEFAULT 0
);

