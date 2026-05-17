# FruitAPI on AWS (Terraform)

Provisions everything FruitAPI needs to run on AWS Fargate against an RDS MySQL database. Used in Lecture 4 of the Intro to DevOps course.

```
VPC (10.0.0.0/16)
├── 2 public subnets (one per AZ, eu-central-1a + 1b)
├── Internet gateway + public route table
├── ECS cluster (Fargate)
│   └── Service "fruitapi-svc" → 1 task with a public IP
│       └── Container pulled from ghcr.io/<owner>/fruitapi:<tag>
│           env: DB_HOST/PORT/USER/NAME from RDS
│           secret: DB_PASSWORD from Secrets Manager
│           logs: → CloudWatch /ecs/fruitapi
├── RDS MySQL 8.0 (db.t3.micro, 20 GB gp3, private)
└── Secrets Manager entry: fruitapi/db-password (random 24-char)
```

## Prereqs

- AWS account, IAM user with programmatic access, `aws configure`'d.
- Terraform >= 1.5 (you have 1.15.3, fine).
- A FruitAPI image pushed to `ghcr.io/<your-username>/fruitapi`. The main pipeline does this on every push to `main`.
- **The image must be public on GHCR.** Otherwise the ECS task can't pull it (we don't wire image-pull secrets here). Make it public at `github.com/<you>?tab=packages` → `fruitapi` → Package settings → "Change package visibility" → Public.

## First-time apply

```powershell
cd terraform
Copy-Item terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars and set github_owner to your GitHub username (lowercase is fine)

terraform init
terraform plan      # eyeball it - should show ~25 resources to create
terraform apply     # ~10 minutes (RDS is the slow one)
```

When apply finishes, useful values are printed by `terraform output`.

## Finding the running task's public IP

We deliberately don't put an ALB in front yet (that's Lecture 5). The task gets a public IP that changes on every restart.

```powershell
$cluster = terraform output -raw ecs_cluster_name
$service = terraform output -raw ecs_service_name

$task = aws ecs list-tasks --cluster $cluster --service-name $service --query 'taskArns[0]' --output text
$eni  = aws ecs describe-tasks --cluster $cluster --tasks $task `
        --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value" --output text
$ip   = aws ec2 describe-network-interfaces --network-interface-ids $eni `
        --query 'NetworkInterfaces[0].Association.PublicIp' --output text

curl "http://${ip}:8000/health"
curl "http://${ip}:8000/fruits"
```

## Tailing logs

```powershell
aws logs tail (terraform output -raw log_group) --follow
```

## Updating to a new image

When you push to `main`, the pipeline tags a new image (`:latest` and `:<sha7>`). To roll the ECS task onto a new build:

```powershell
# either: keep image_tag = "latest" and force a new deployment
aws ecs update-service --cluster (terraform output -raw ecs_cluster_name) `
                       --service (terraform output -raw ecs_service_name) `
                       --force-new-deployment

# or: pin a specific SHA
terraform apply -var "image_tag=abc1234"
```

## Tear down (do this whenever you stop working)

```powershell
terraform destroy
```

Removes the VPC, RDS, ECS, secret, log group — everything. RDS takes ~5 minutes to delete. The Secrets Manager entry has `recovery_window_in_days = 0` so it deletes immediately and a re-apply works cleanly.

## Cost notes (free-tier sandbox)

| Resource | Free tier? | Approx cost outside FT |
|---|---|---|
| VPC / subnets / route tables / IGW / SGs | Always free | $0 |
| RDS `db.t3.micro` MySQL, 20 GB | 750 hrs/mo, first 12 months | ~$15/mo |
| ECS Fargate task (0.25 vCPU, 512 MB) | Not in FT | ~$8.50/mo if always running |
| CloudWatch Logs | 5 GB ingest free | ~$0 here |
| Secrets Manager | Not in FT | $0.40/mo per secret + tiny API cost |
| Data egress | 100 GB/mo free | ~$0 here |

`terraform destroy` when not actively working keeps the running cost at $0.
