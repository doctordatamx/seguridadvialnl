$ErrorActionPreference = 'Stop'
Push-Location (Join-Path $PSScriptRoot '..')
try {
    & ./.venv/Scripts/python.exe -m pipelines.run
    if ($LASTEXITCODE -ne 0) { throw 'Falló el pipeline' }
    Push-Location web
    try { npm run build; if ($LASTEXITCODE -ne 0) { throw 'Falló la compilación' } }
    finally { Pop-Location }
} finally { Pop-Location }
