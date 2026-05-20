# auto_heal.py

import sqlite3
import time
import subprocess
from datetime import datetime, timedelta

from kubernetes import client, config

# =========================================================
# CONFIGURATION
# =========================================================

CHECK_INTERVAL = 5  # seconds

MEMORY_THRESHOLD_MI = 400

RESTART_COOLDOWN_MINUTES = 10

# Track restart timestamps
last_restart_time = {}

# =========================================================
# LOAD KUBERNETES CONFIG
# =========================================================

config.load_kube_config()

v1 = client.CoreV1Api()

# =========================================================
# LOGGER
# =========================================================

def log_event(message):

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_message = f"[{timestamp}] {message}"

    print(log_message)

    with open("auto_heal.log", "a") as f:
        f.write(log_message + "\n")

# =========================================================
# STORE EVENTS IN SQLITE
# =========================================================

def store_event(
    namespace,
    pod_name,
    issue_type,
    action_taken,
    status
):

    conn = sqlite3.connect("healing_events.db")

    cursor = conn.cursor()

    # Create table if not exists
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

    # Insert event
    cursor.execute("""
    INSERT INTO healing_events (
        timestamp,
        namespace,
        pod_name,
        issue_type,
        action_taken,
        status
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        namespace,
        pod_name,
        issue_type,
        action_taken,
        status
    ))

    conn.commit()

    conn.close()

# =========================================================
# GET DEPLOYMENT NAME FROM POD
# =========================================================

def get_deployment_name_from_pod(pod):

    try:

        owner_refs = pod.metadata.owner_references

        if owner_refs:

            replica_set_name = owner_refs[0].name

            # Example:
            # broken-nginx-5f7d9c7b6d

            deployment_name = "-".join(
                replica_set_name.split("-")[:-1]
            )

            return deployment_name

    except Exception as e:

        log_event(
            f"Failed to get deployment name: {e}"
        )

    return None

# =========================================================
# RESTART DEPLOYMENT
# =========================================================

def restart_deployment(namespace, deployment_name):

    current_time = datetime.now()

    # Cooldown protection
    if deployment_name in last_restart_time:

        last_time = last_restart_time[deployment_name]

        if current_time - last_time < timedelta(
            minutes=RESTART_COOLDOWN_MINUTES
        ):

            log_event(
                f"Cooldown active for deployment: {deployment_name}"
            )

            # Store cooldown event
            store_event(
                namespace,
                deployment_name,
                "Cooldown",
                "Skipped Restart",
                "INFO"
            )

            return

    try:

        log_event(
            f"Restarting deployment: {deployment_name}"
        )

        subprocess.run(
            [
                "kubectl",
                "rollout",
                "restart",
                f"deployment/{deployment_name}",
                "-n",
                namespace
            ],
            check=True
        )

        last_restart_time[deployment_name] = current_time

        log_event(
            f"Successfully restarted deployment: {deployment_name}"
        )

        # Store success event
        store_event(
            namespace,
            deployment_name,
            "CrashLoopBackOff",
            "Restart Deployment",
            "SUCCESS"
        )

    except subprocess.CalledProcessError as e:

        log_event(
            f"Failed to restart deployment {deployment_name}: {e}"
        )

        # Store failure event
        store_event(
            namespace,
            deployment_name,
            "CrashLoopBackOff",
            "Restart Deployment",
            "FAILED"
        )

# =========================================================
# SCALE DEPLOYMENT
# =========================================================

def scale_deployment(namespace, deployment_name, replicas):

    try:

        log_event(
            f"Scaling deployment {deployment_name} to {replicas} replicas"
        )

        subprocess.run(
            [
                "kubectl",
                "scale",
                f"deployment/{deployment_name}",
                f"--replicas={replicas}",
                "-n",
                namespace
            ],
            check=True
        )

        log_event(
            f"Successfully scaled deployment: {deployment_name}"
        )

        # Store scaling event
        store_event(
            namespace,
            deployment_name,
            "HighMemoryUsage",
            f"Scaled to {replicas} replicas",
            "SUCCESS"
        )

    except subprocess.CalledProcessError as e:

        log_event(
            f"Failed to scale deployment {deployment_name}: {e}"
        )

        # Store failed scaling event
        store_event(
            namespace,
            deployment_name,
            "HighMemoryUsage",
            "Scale Deployment",
            "FAILED"
        )

# =========================================================
# DETECT CRASHED PODS
# =========================================================

def detect_crashed_pods():

    pods = v1.list_pod_for_all_namespaces(watch=False)

    for pod in pods.items:

        namespace = pod.metadata.namespace
        pod_name = pod.metadata.name

        if not pod.status.container_statuses:
            continue

        for container_status in pod.status.container_statuses:

            waiting_state = container_status.state.waiting

            if waiting_state:

                reason = waiting_state.reason

                print(
                    f"Pod: {pod_name}, Reason: {reason}"
                )

                if reason in [
                    "CrashLoopBackOff",
                    "Error",
                    "ImagePullBackOff",
                    "RunContainerError",
                    "CreateContainerConfigError",
                    "ContainerCannotRun"
                ]:

                    log_event(
                        f"Issue detected in pod: {pod_name} | Reason: {reason}"
                    )

                    deployment_name = get_deployment_name_from_pod(
                        pod
                    )

                    if deployment_name:

                        restart_deployment(
                            namespace,
                            deployment_name
                        )

# =========================================================
# DETECT HIGH MEMORY USAGE
# =========================================================

def detect_high_memory_usage():

    try:

        result = subprocess.check_output(
            [
                "kubectl",
                "top",
                "pods",
                "-A",
                "--no-headers"
            ],
            text=True
        )

        lines = result.strip().split("\n")

        for line in lines:

            columns = line.split()

            if len(columns) < 4:
                continue

            namespace = columns[0]

            # Ignore system namespaces
            if namespace in [
                "kube-system",
                "kube-public",
                "kube-node-lease",
                "monitoring"
            ]:
                continue

            pod_name = columns[1]

            cpu = columns[2]
            memory = columns[3]

            # Example:
            # 450Mi

            if "Mi" in memory:

                memory_value = int(
                    memory.replace("Mi", "")
                )

                if memory_value > MEMORY_THRESHOLD_MI:

                    log_event(
                        f"High memory usage detected in pod: {pod_name} | Memory: {memory}"
                    )

                    # Fetch full pod object
                    pod_obj = v1.read_namespaced_pod(
                        name=pod_name,
                        namespace=namespace
                    )

                    deployment_name = get_deployment_name_from_pod(
                        pod_obj
                    )

                    if deployment_name:

                        scale_deployment(
                            namespace,
                            deployment_name,
                            replicas=4
                        )

    except Exception as e:

        log_event(
            f"Failed to check memory usage: {e}"
        )

# =========================================================
# DETECT NODE PRESSURE
# =========================================================

def detect_node_pressure():

    nodes = v1.list_node()

    for node in nodes.items:

        node_name = node.metadata.name

        conditions = node.status.conditions

        for condition in conditions:

            if (
                condition.type in [
                    "MemoryPressure",
                    "DiskPressure",
                    "PIDPressure"
                ]
                and condition.status == "True"
            ):

                log_event(
                    f"Node pressure detected: {node_name} | Condition: {condition.type}"
                )

                try:

                    subprocess.run(
                        [
                            "kubectl",
                            "cordon",
                            node_name
                        ],
                        check=True
                    )

                    log_event(
                        f"Successfully cordoned node: {node_name}"
                    )

                    # Store node pressure event
                    store_event(
                        "cluster",
                        node_name,
                        condition.type,
                        "Cordon Node",
                        "SUCCESS"
                    )

                except subprocess.CalledProcessError as e:

                    log_event(
                        f"Failed to cordon node {node_name}: {e}"
                    )

                    # Store failed node event
                    store_event(
                        "cluster",
                        node_name,
                        condition.type,
                        "Cordon Node",
                        "FAILED"
                    )

# =========================================================
# MAIN LOOP
# =========================================================

def main():

    log_event(
        "Starting Auto-Healing Engine..."
    )

    while True:

        try:

            log_event(
                "Running health checks..."
            )

            detect_crashed_pods()

            detect_high_memory_usage()

            detect_node_pressure()

            log_event(
                "Health check cycle completed"
            )

        except Exception as e:

            log_event(
                f"Unexpected error: {e}"
            )

        time.sleep(CHECK_INTERVAL)

# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()