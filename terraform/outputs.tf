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

output "alb_dns_name" {
  description = "ALB DNS name — stable public hostname for FruitAPI."
  value       = aws_lb.main.dns_name
}

output "alb_url" {
  description = "Full URL of FruitAPI behind the ALB."
  value       = "http://${aws_lb.main.dns_name}"
}

output "github_actions_role_arn" {
  description = "ARN of the IAM role GitHub Actions assumes via OIDC for ECS deploys. Save this as a repo Variable named AWS_DEPLOY_ROLE_ARN."
  value       = aws_iam_role.github_actions.arn
}
