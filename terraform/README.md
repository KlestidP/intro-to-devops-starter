# FruitAPI on AWS (Terraform)

Provisions everything FruitAPI needs to run on AWS Fargate against an RDS MySQL database. Used in Lecture 4 of the Intro to DevOps course.

```
VPC (10.0.0.0/16)
├── 2 public subnets (one per AZ, eu-central-1a + 1b)
├── Internet gateway + public route table
├── Application Load Balancer (port 80, public)
│   └── Target group "fruitapi-tg" health-checks /health on port 8000
├── ECS cluster (Fargate)
│   └── Service "fruitapi-svc" → N tasks registered with the target group
│       ├── Inbound only from the ALB SG (no direct internet)
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

## Hitting the API

```powershell
$url = terraform output -raw alb_url
curl "$url/health"
curl "$url/fruits"
```

The ALB DNS name is stable across deploys and task restarts — unlike the per-task public IP from Lecture 4. Direct task-IP access is now blocked by the security-group changes (ECS task SG only accepts traffic from the ALB SG).

## CI/CD setup (Lecture 6)

The deploy job in [`main.yml`](../.github/workflows/main.yml) assumes an IAM role via GitHub OIDC and triggers a rolling redeploy after each successful image push.

One-time setup:

1. **Apply terraform** so the role exists. After apply, copy the role ARN:
   ```powershell
   terraform output -raw github_actions_role_arn
   ```
2. **Add a repo Variable in GitHub** — Repo → Settings → Secrets and variables → Actions → **Variables** tab → "New repository variable":
   - Name: `AWS_DEPLOY_ROLE_ARN`
   - Value: paste the ARN from step 1
3. **That's it** — the next push to `main` (or merge to `main`) builds and pushes the image, then the `deploy` job force-deploys ECS to roll the new image. The job is gated by `if: vars.AWS_DEPLOY_ROLE_ARN != ''`, so it sits out cleanly until you've done step 2.

Watch the deploy in CloudWatch:
```powershell
aws logs tail (terraform output -raw log_group) --follow
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
| ECS Fargate (0.25 vCPU, 512 MB) × `desired_count` | Not in FT | ~$8.50/mo per task always-on |
| Application Load Balancer | Not in FT | ~$18/mo always-on + tiny LCU charge |
| CloudWatch Logs | 5 GB ingest free | ~$0 here |
| Secrets Manager | Not in FT | $0.40/mo per secret + tiny API cost |
| Data egress | 100 GB/mo free | ~$0 here |

`terraform destroy` when not actively working keeps the running cost at $0. The ALB is the most expensive idle resource — definitely don't leave it running between sessions.
