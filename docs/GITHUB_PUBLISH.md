# GitHub Publish Guide

The project is GitHub-ready:

- `pyproject.toml` defines the installable Python package.
- `.github/workflows/ci.yml` runs unit tests on push and pull request.
- `.gitignore` excludes caches, virtual environments, build outputs, and SQLite snapshots.
- `scripts/publish_to_github.ps1` can publish through Git and GitHub CLI if they are installed.

## Option A: Codex GitHub Plugin

The Codex GitHub plugin is installed and connected to user account `LinYuan41319`.

Create or choose a repository on GitHub, then ask Codex:

```text
Push outputs/biomed-ref-pipeline to LinYuan41319/REPOSITORY_NAME and open a pull request if needed.
```

## Option B: GitHub CLI

Install Git for Windows and GitHub CLI, then authenticate:

```powershell
gh auth login
```

From this project directory:

```powershell
.\scripts\publish_to_github.ps1 -Repo "LinYuan41319/biomed-ref-pipeline" -CreateRepo
```

## Option C: Existing Repository

If the repository already exists:

```powershell
.\scripts\publish_to_github.ps1 -Repo "LinYuan41319/biomed-ref-pipeline"
```
