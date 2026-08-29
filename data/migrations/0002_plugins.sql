CREATE TABLE plugin_states (
  plugin_id TEXT PRIMARY KEY,
  version TEXT NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 0,
  installed_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE plugin_grants (
  plugin_id TEXT NOT NULL REFERENCES plugin_states(plugin_id) ON DELETE CASCADE,
  permission TEXT NOT NULL,
  granted INTEGER NOT NULL DEFAULT 0,
  granted_at TEXT,
  PRIMARY KEY (plugin_id, permission)
);

