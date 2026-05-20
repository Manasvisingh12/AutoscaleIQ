module "vpc" {
  source = "./modules/vpc"
}

module "sg" {
  source = "./modules/security_group"
}

module "ec2" {
  source = "./modules/ec2"
}

module "k8s" {
  source = "./modules/k8s"
}