$ErrorActionPreference = "Stop"
$env:PYTHONDONTWRITEBYTECODE = "1"
python -m unittest discover -s tests -v
