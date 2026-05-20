from kubernetes import client, config

# Load local kubeconfig
config.load_kube_config()

v1 = client.CoreV1Api()

pods = v1.list_pod_for_all_namespaces()

for pod in pods.items:
    print(pod.metadata.name)