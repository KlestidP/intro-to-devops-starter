output "vpc_id" {
  value = aws_vpc.main.id
}

output "rds_endpoint" {
  description = "MySQL endpoint hostname (the ECS task uses this as DB_HOST)."
  value       = aws_db_instance.main.address
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  value = aws_ecs_service.fruitapi.name
}

output "log_group" {
  value = aws_cloudwatch_log_group.ecs.name
}

output "image_url" {
  description = "Container image the ECS task is pinned to."
  value       = local.image_url
}

output "db_secret_arn" {
  description = "Secrets Manager ARN that stores the MySQL admin password."
  value       = aws_secretsmanager_secret.db_password.arn
}
