resource "docker_container" "app" {
  name  = "autoscaleiq-container"
  image = "nginx"

  ports {
    internal = 80
    external = 8080
  }
}

resource "docker_container" "prometheus" {
  name  = "prometheus"
  image = "prom/prometheus"

  ports {
    internal = 9090
    external = 9090
  }
}