param([Parameter(Mandatory=$true)][string]$Records)
$ErrorActionPreference = 'Stop'
$recordsAbsolute = (Resolve-Path -LiteralPath $Records).Path
Push-Location (Join-Path $PSScriptRoot '..')
try {
    $pythonCommand = if (Test-Path '.venv/Scripts/python.exe') { '.venv/Scripts/python.exe' } else { 'python' }
    & $pythonCommand scripts/fetch_intelligence_sources.py
    if ($LASTEXITCODE -ne 0) { throw 'Falló la adquisición de insumos' }
    foreach ($script in @('build_intelligence.py','compare_spatial.py','audit_spatial.py')) {
        & $pythonCommand (Join-Path 'scripts' $script) --records $recordsAbsolute
        if ($LASTEXITCODE -ne 0) { throw "Falló $script" }
    }
    & $pythonCommand scripts/prepare_atlas.py
    if ($LASTEXITCODE -ne 0) { throw 'Falló el atlas' }
    & $pythonCommand scripts/finalize_intelligence_release.py
    if ($LASTEXITCODE -ne 0) { throw 'Falló el manifiesto público' }
    & $pythonCommand scripts/check_public.py
    if ($LASTEXITCODE -ne 0) { throw 'Falló la revisión de publicación' }
    node scripts/stage_public.mjs
    if ($LASTEXITCODE -ne 0) { throw 'Falló la preparación web' }
    Push-Location web
    try { npm run build -- --mode pages; if ($LASTEXITCODE -ne 0) { throw 'Falló el build' } }
    finally { Pop-Location }
} finally { Pop-Location }
