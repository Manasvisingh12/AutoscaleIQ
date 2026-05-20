from k8s_client import get_deployments
from prometheus_client import query_prometheus
from cost_calculator import estimate_cpu_savings
from database import save_recommendation

CPU_THRESHOLD = 0.01
MEMORY_THRESHOLD = 0.2


# RULE 1 — Underutilized Pods
def detect_underutilized_pods():

    query = 'avg(rate(container_cpu_usage_seconds_total[1h]))'

    data = query_prometheus(query)

    recommendations = []

    results = data["data"]["result"]

    for item in results:

        cpu_usage = float(item["value"][1])

        pod = item["metric"].get("pod", "unknown")

        namespace = item["metric"].get("namespace", "unknown")

        if cpu_usage < CPU_THRESHOLD:

            recommendations.append({
                "type": "Underutilized Pod",
                "pod": pod,
                "namespace": namespace,
                "cpu_usage": round(cpu_usage, 5),
                "severity": "medium",
                "recommendation": "Reduce replicas or lower CPU requests",
                "estimated_cpu_savings": "30%"
            })

    return recommendations


# RULE 2 — Oversized Containers
# RULE 2 — Oversized Containers
def detect_oversized_containers():

    usage_query = 'avg(rate(container_cpu_usage_seconds_total[1h]))'

    request_query = 'kube_pod_container_resource_requests'

    usage_data = query_prometheus(usage_query)

    request_data = query_prometheus(request_query)

    recommendations = []

    usage_results = usage_data["data"]["result"]

    request_results = request_data["data"]["result"]

    usage_map = {}

    # Store actual usage
    for item in usage_results:

        pod = item["metric"].get("pod", "unknown")

        cpu_usage = float(item["value"][1])

        usage_map[pod] = cpu_usage

    # Compare requests vs usage
    for item in request_results:

        pod = item["metric"].get("pod", "unknown")

        namespace = item["metric"].get("namespace", "unknown")

        resource = item["metric"].get("resource", "")

        if resource != "cpu":
            continue

        requested_cpu = float(item["value"][1])

        actual_cpu = usage_map.get(pod, 0)

        if requested_cpu > 0 and actual_cpu < (requested_cpu * 0.2):

            recommended_cpu = round(requested_cpu * 0.5, 2)

            estimated_savings = estimate_cpu_savings(
                requested_cpu - actual_cpu
            )

            recommendations.append({

                "type": "Oversized Container",

                "pod": pod,

                "namespace": namespace,

                "requested_cpu": requested_cpu,

                "actual_cpu": round(actual_cpu, 5),

                "recommended_cpu_request": recommended_cpu,

                "severity": "high",

                "recommendation":
                    f"Reduce CPU request from "
                    f"{requested_cpu} → "
                    f"{recommended_cpu}",

                "estimated_monthly_savings":
                    f"${estimated_savings}/month"
            })
            save_recommendation(

    issue="Oversized Container",

    resource_name=pod,

    recommendation=
        f"Reduce CPU request to "
        f"{recommended_cpu}",

    severity="high",

    estimated_savings=
        f"${estimated_savings}/month"
)

    return recommendations

# RULE 3 — Excess Replicas
def detect_excess_replicas():

    recommendations = []

    deployments = get_deployments()

    cpu_query = '''
    avg(rate(container_cpu_usage_seconds_total[1h])) by (pod)
    '''

    cpu_data = query_prometheus(cpu_query)

    cpu_results = cpu_data["data"]["result"]

    low_cpu_pods = []

    # Detect low CPU pods
    for item in cpu_results:

        cpu_usage = float(item["value"][1])

        pod = item["metric"].get("pod", "")

        if cpu_usage < CPU_THRESHOLD:

            low_cpu_pods.append(pod)

    # Analyze deployments
    for deployment in deployments:

        deployment_name = deployment.metadata.name

        namespace = deployment.metadata.namespace

        current_replicas = deployment.spec.replicas

        # Only analyze deployments with many replicas
        if current_replicas > 3:

            recommended_replicas = max(1, current_replicas // 2)

            estimated_savings = (
                current_replicas - recommended_replicas
            ) * 5

            recommendations.append({

                "type": "Excess Replicas",

                "deployment": deployment_name,

                "namespace": namespace,

                "current_replicas": current_replicas,

                "recommended_replicas": recommended_replicas,

                "severity": "medium",

                "recommendation":
                    f"Scale deployment from "
                    f"{current_replicas} → "
                    f"{recommended_replicas} replicas",

                "estimated_monthly_savings":
                    f"${estimated_savings}/month"
            })

    return recommendations

# RULE 4 — Memory Waste
def detect_memory_waste():

    usage_query = 'container_memory_usage_bytes'

    limit_query = 'kube_pod_container_resource_limits'

    usage_data = query_prometheus(usage_query)

    limit_data = query_prometheus(limit_query)

    recommendations = []

    usage_results = usage_data["data"]["result"]

    limit_results = limit_data["data"]["result"]

    memory_usage_map = {}

    for item in usage_results:

        pod = item["metric"].get("pod", "unknown")

        usage = float(item["value"][1])

        memory_usage_map[pod] = usage

    for item in limit_results:

        pod = item["metric"].get("pod", "unknown")

        namespace = item["metric"].get("namespace", "unknown")

        resource = item["metric"].get("resource", "")

        if resource != "memory":
            continue

        memory_limit = float(item["value"][1])

        actual_memory = memory_usage_map.get(pod, 0)

        if memory_limit > 0 and actual_memory < (memory_limit * MEMORY_THRESHOLD):

            recommended_limit = round(memory_limit * 0.5, 2)

            recommendations.append({
                "type": "Memory Waste",
                "pod": pod,
                "namespace": namespace,
                "memory_limit": memory_limit,
                "actual_memory_usage": round(actual_memory, 2),
                "recommended_memory_limit": recommended_limit,
                "severity": "medium",
                "recommendation": "Lower memory limits",
                "estimated_memory_savings": "50%"
            })

    return recommendations