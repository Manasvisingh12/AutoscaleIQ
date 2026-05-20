variable "allowed_ports" {
  default = [22, 80]
}

output "sg_id" {
  value = "local-sg-123"
}