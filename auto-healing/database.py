import sqlite3

conn = sqlite3.connect("healing_events.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS healing_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    namespace TEXT,
    pod_name TEXT,
    issue_type TEXT,
    action_taken TEXT,
    status TEXT
)
""")

conn.commit()

conn.close()