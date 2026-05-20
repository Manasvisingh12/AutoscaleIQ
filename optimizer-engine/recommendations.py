import sqlite3
from datetime import datetime

# =========================================================
# STORE OPTIMIZATION RECOMMENDATIONS
# =========================================================

def store_recommendation(
    deployment_name,
    recommendation,
    estimated_savings
):

    conn = sqlite3.connect(
        "../auto-healing/healing_events.db"
    )

    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        deployment_name TEXT,
        recommendation TEXT,
        estimated_savings TEXT
    )
    """)

    # Insert recommendation
    cursor.execute("""
    INSERT INTO recommendations (
        timestamp,
        deployment_name,
        recommendation,
        estimated_savings
    )
    VALUES (?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        deployment_name,
        recommendation,
        estimated_savings
    ))

    conn.commit()

    conn.close()

# =========================================================
# GENERATE OPTIMIZATION RECOMMENDATIONS
# =========================================================

def generate_recommendation(
    deployment_name,
    cpu_usage,
    memory_usage,
    replicas
):

    # -----------------------------------------------------
    # UNDERUTILIZED CPU
    # -----------------------------------------------------

    if cpu_usage < 10:

        recommendation = (
            f"Reduce replicas from {replicas} to 2"
        )

        estimated_savings = "35%"

        print(
            f"[RECOMMENDATION] {deployment_name}: "
            f"{recommendation}"
        )

        store_recommendation(
            deployment_name,
            recommendation,
            estimated_savings
        )

    # -----------------------------------------------------
    # HIGH MEMORY USAGE
    # -----------------------------------------------------

    if memory_usage > 80:

        recommendation = (
            "Increase memory limit or scale deployment"
        )

        estimated_savings = "Stability Improvement"

        print(
            f"[RECOMMENDATION] {deployment_name}: "
            f"{recommendation}"
        )

        store_recommendation(
            deployment_name,
            recommendation,
            estimated_savings
        )

    # -----------------------------------------------------
    # OVERSIZED CONTAINER
    # -----------------------------------------------------

    if cpu_usage < 20 and memory_usage < 20:

        recommendation = (
            "Lower CPU and memory requests"
        )

        estimated_savings = "22%"

        print(
            f"[RECOMMENDATION] {deployment_name}: "
            f"{recommendation}"
        )

        store_recommendation(
            deployment_name,
            recommendation,
            estimated_savings
        )

# =========================================================
# TESTING
# =========================================================

if __name__ == "__main__":

    generate_recommendation(
        deployment_name="nginx-app",
        cpu_usage=5,
        memory_usage=30,
        replicas=4
    )

    generate_recommendation(
        deployment_name="api-service",
        cpu_usage=15,
        memory_usage=90,
        replicas=3
    )