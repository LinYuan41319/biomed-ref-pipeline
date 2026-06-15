param(
  [Parameter(Mandatory=$true)]
  [string]$Repo,
  [switch]$CreateRepo,
  [string]$Branch = "main",
  [string]$Message = "Initial biomed reference pipeline"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  throw "git was not found in PATH. Install Git for Windows or publish through the Codex GitHub plugin."
}

if ($CreateRepo -and -not (Get-Command gh -ErrorAction SilentlyContinue)) {
  throw "GitHub CLI was not found in PATH. Create the repository manually or publish through the Codex GitHub plugin."
}

if (-not (Test-Path ".git")) {
  git init
}

git add .
git commit -m $Message
git branch -M $Branch

if ($CreateRepo) {
  gh repo create $Repo --private --source . --remote origin --push
} else {
  git remote remove origin 2>$null
  git remote add origin "https://github.com/$Repo.git"
  git push -u origin $Branch
}
