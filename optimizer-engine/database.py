import sqlite3


# Create database + table
conn = sqlite3.connect("recommendations.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    issue TEXT,
    resource_name TEXT,
    recommendation TEXT,
    severity TEXT,
    estimated_savings TEXT
)
""")

conn.commit()

conn.close()


# Save recommendation function
def save_recommendation(
    issue,
    resource_name,
    recommendation,
    severity,
    estimated_savings
):

    conn = sqlite3.connect("recommendations.db")

    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO recommendations (
        issue,
        resource_name,
        recommendation,
        severity,
        estimated_savings
    )
    VALUES (?, ?, ?, ?, ?)
    """, (
        issue,
        resource_name,
        recommendation,
        severity,
        estimated_savings
    ))

    conn.commit()

    conn.close()