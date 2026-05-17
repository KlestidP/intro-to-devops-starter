resource "aws_security_group" "ecs_task" {
  name        = "${var.project_name}-ecs-task"
  description = "ECS task: inbound on container port, outbound anywhere."
  vpc_id      = aws_vpc.main.id

  # For Lecture 4 we expose the task directly to the internet.
  # Lecture 5 narrows this down to "only from the ALB SG".
  ingress {
    description = "FruitAPI container port"
    from_port   = var.container_port
    to_port     = var.container_port
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All outbound (image pull, RDS, Secrets Manager)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "rds" {
  name        = "${var.project_name}-rds"
  description = "RDS MySQL: only ECS tasks on 3306, no public access."
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "MySQL from ECS tasks"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_task.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
