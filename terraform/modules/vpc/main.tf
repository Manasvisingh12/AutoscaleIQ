variable "cidr_block" {
  default = "10.0.0.0/16"
}

output "vpc_id" {
  value = "local-vpc-123"
}