from k8s_client import get_deployments

deployments = get_deployments()

for deployment in deployments:

    print(
        deployment.metadata.name,
        deployment.spec.replicas
    )