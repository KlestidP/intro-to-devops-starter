locals {
  # GHCR is case-insensitive in pulls but stores lowercase, so normalize.
  image_url = "ghcr.io/${lower(var.github_owner)}/${var.project_name}:${var.image_tag}"
}
