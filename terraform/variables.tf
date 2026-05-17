variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "eu-central-1"
}

variable "project_name" {
  description = "Prefix used for resource names and tags."
  type        = string
  default     = "fruitapi"
}

variable "github_owner" {
  description = "GitHub owner that hosts the container image at ghcr.io/<owner>/fruitapi. Required."
  type        = string
}

variable "github_repo_name" {
  description = "Name of the GitHub repo (used to scope which repo can assume the OIDC deploy role)."
  type        = string
  default     = "intro-to-devops-starter"
}

variable "image_tag" {
  description = "Tag of the FruitAPI image to deploy. The main pipeline tags each push with the short SHA and 'latest'."
  type        = string
  default     = "latest"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDRs for the two public subnets (one per AZ)."
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "db_name" {
  description = "MySQL schema name."
  type        = string
  default     = "fruitapi"
}

variable "db_username" {
  description = "MySQL admin user."
  type        = string
  default     = "fruitapi"
}

variable "db_instance_class" {
  description = "RDS instance class. db.t3.micro is free-tier eligible for 12 months."
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB. 20 GB is the free-tier max."
  type        = number
  default     = 20
}

variable "container_port" {
  description = "Port exposed by the FruitAPI container."
  type        = number
  default     = 8000
}

variable "task_cpu" {
  description = "Fargate task CPU units (256 = 0.25 vCPU, the Fargate minimum)."
  type        = number
  default     = 256
}

variable "task_memory" {
  description = "Fargate task memory in MiB (512 is the min for 256 CPU)."
  type        = number
  default     = 512
}

variable "desired_count" {
  description = "Number of ECS tasks to run behind the ALB."
  type        = number
  default     = 2
}

variable "log_retention_days" {
  description = "CloudWatch log retention for the ECS log group."
  type        = number
  default     = 7
}
