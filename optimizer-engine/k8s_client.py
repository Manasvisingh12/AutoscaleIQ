from kubernetes import client, config

config.load_kube_config()

apps_v1 = client.AppsV1Api()
core_v1 = client.CoreV1Api()


def get_deployments():

    deployments = apps_v1.list_deployment_for_all_namespaces()

    return deployments.items


def get_pods():

    pods = core_v1.list_pod_for_all_namespaces()

    return pods.items