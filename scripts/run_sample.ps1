param(
  [Parameter(Mandatory=$true)]
  [string]$Docx,
  [string]$Out = "out",
  [string]$ZoteroSqlite = "",
  [string]$JcrXlsx = "",
  [string]$Email = ""
)

$ErrorActionPreference = "Stop"

$argsList = @("run", "--docx", $Docx, "--out", $Out)
if ($ZoteroSqlite) { $argsList += @("--zotero-sqlite", $ZoteroSqlite) }
if ($JcrXlsx) { $argsList += @("--jcr-xlsx", $JcrXlsx) }
if ($Email) { $argsList += @("--email", $Email) }

python -m biomed_ref_pipeline @argsList
