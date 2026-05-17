# FruitAPI — Intro to DevOps homework

A small FastAPI service that manages a catalog of fruits. Used as the project for the Intro to DevOps course; the app stays intentionally minimal so the focus is on DevOps practices.

**Spec:** [PROJECT-REQUIREMENTS.md](./PROJECT-REQUIREMENTS.md).

## Layout

```
app/             FastAPI application (models, in-memory store, routes, app factory)
tests/           test_main.py (unit) and test_integration.py (against a real server)
main.py          repo-root entrypoint — `python main.py` to run locally
```

## Run locally

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe main.py
```

Then hit http://127.0.0.1:8000/health.

## Run tests

```powershell
# unit tests only (fast, no server)
.\.venv\Scripts\python.exe -m pytest tests/test_main.py

# integration tests (spawns uvicorn automatically)
.\.venv\Scripts\python.exe -m pytest tests/test_integration.py

# everything
.\.venv\Scripts\python.exe -m pytest
```

Integration tests honour a `BASE_URL` env var — point it at a running container (Lecture 2+) instead of spawning a local server.

## Endpoints

| Method | Path                | Description                                      |
|--------|---------------------|--------------------------------------------------|
| GET    | `/health`           | `200 {"status": "ok"}`                           |
| GET    | `/fruits`           | List all fruits. Optional `?in_season=true/false`|
| GET    | `/fruits/cheapest`  | Fruit with the lowest price (404 if none)        |
| GET    | `/fruits/{id}`      | Single fruit or 404                              |
| POST   | `/fruits`           | Create. Body: `{name, price, in_season?}`        |
| PUT    | `/fruits/{id}`      | Partial update or 404                            |
| DELETE | `/fruits/{id}`      | 204 or 404                                       |

## Development workflow — GitHub Flow

This repo uses **GitHub Flow** for the rest of the course:

1. `main` is always deployable and protected — direct pushes are blocked.
2. Start work by branching off `main`: `git switch -c <topic-branch>`. Keep branches short-lived (hours to a couple of days).
3. Open a pull request as soon as there's something to discuss. The PR pipeline runs unit tests on every push to the branch (see Lecture 3).
4. Merge to `main` only when:
   - The PR has at least one green check from the unit-test pipeline.
   - The branch is up to date with `main` (rebase or merge as needed).
5. After merge, the `main` pipeline builds the Docker image, runs integration tests against it, versions the image, and pushes it to the registry.
6. Delete the branch after merging.

No long-lived release/develop branches; releases are tagged commits on `main`.

## Docker

The repo ships a multi-stage Dockerfile based on `python:3.12-slim` that runs as a non-root user and includes a stdlib-based `HEALTHCHECK`.

```powershell
docker build -t fruitapi:dev .
docker run --rm -p 8000:8000 fruitapi:dev
# in another shell:
curl http://127.0.0.1:8000/health
```

Run the integration tests against a running container (no local uvicorn spawn):

```powershell
docker run -d --name fruitapi-it -p 8000:8000 fruitapi:dev
$env:BASE_URL = "http://127.0.0.1:8000"
.\.venv\Scripts\python.exe -m pytest tests/test_integration.py
docker rm -f fruitapi-it
Remove-Item Env:\BASE_URL
```

### SBOM (optional, Lecture 2)

The CI workflow generates a Software Bill of Materials for each pushed image using [`anchore/sbom-action`](https://github.com/anchore/sbom-action) (see [main.yml](.github/workflows/main.yml)). To generate one locally:

```powershell
docker scout sbom fruitapi:dev --format spdx --output sbom.spdx.json
# or, with syft installed:
# syft fruitapi:dev -o spdx-json=sbom.spdx.json
```

## CI / CD

Two GitHub Actions workflows live in [`.github/workflows/`](.github/workflows/):

| Workflow | Trigger | What it does |
|---|---|---|
| [`pr.yml`](.github/workflows/pr.yml) | `pull_request` to `main` | Runs unit tests (`pytest tests/test_main.py`). Posts a summary on the PR's checks tab. Required check for branch protection. |
| [`main.yml`](.github/workflows/main.yml) | `push` to `main` | Unit tests → build Docker image → integration tests against the running container → tag with short SHA + `latest` → push to GHCR → generate SPDX SBOM artifact. |

### One-time GitHub setup (manual)

1. **Enable Actions** — Repo → Settings → Actions → General → "Allow all actions" (or your org's policy).
2. **Allow GHCR publishing** — Repo → Settings → Actions → General → Workflow permissions → choose **Read and write permissions**. This lets `GITHUB_TOKEN` push to `ghcr.io/<owner>/fruitapi`.
3. **Branch protection on `main`** — Repo → Settings → Branches → "Add rule" for `main`:
   - "Require a pull request before merging"
   - "Require status checks to pass" → search for and select **`Unit tests`** (the job from `pr.yml`)
   - "Require branches to be up to date before merging"
   - Save.

After the first successful run on `main`, the package appears at `https://github.com/<owner>?tab=packages`. Make it public there if you want the image pullable without auth.
