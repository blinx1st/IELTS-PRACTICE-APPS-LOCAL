param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $taskRoot

function Find-Python {
    $candidates = @((Join-Path $taskRoot '.venv\Scripts\python.exe'))
    $command = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($command) { $candidates += $command.Source }
    $candidates += Get-ChildItem -LiteralPath (Join-Path $env:LOCALAPPDATA 'Programs\Python') -Filter python.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
    foreach ($candidate in $candidates) {
        if ((Test-Path -LiteralPath $candidate) -and $candidate -notlike '*\WindowsApps\*') {
            & $candidate -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' 2>$null
            if ($LASTEXITCODE -eq 0) { return $candidate }
        }
    }
    return $null
}

function Find-Node {
    $command = Get-Command node.exe -ErrorAction SilentlyContinue
    $candidates = @()
    if ($command) { $candidates += $command.Source }
    $candidates += Get-ChildItem -Path (Join-Path $taskRoot '.runtime\node-*\node.exe') -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
    foreach ($candidate in $candidates) {
        $version = & $candidate -p 'process.versions.node'
        if ($LASTEXITCODE -eq 0 -and [version]$version -ge [version]'22.12.0') { return $candidate }
    }
    return $null
}

try {
    $taskPython = Find-Python
    $taskNode = Find-Node
    if ($CheckOnly) {
        Write-Output "Python: $taskPython"
        Write-Output "Node: $taskNode"
        if (!$taskPython -or !$taskNode) { exit 1 }
        exit 0
    }
    if (!$taskPython) {
        $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
        if (!$winget) { throw 'Install Python 3.11+ from https://www.python.org/downloads/windows/ then run this file again. Windows App Installer (winget) is unavailable.' }
        Write-Output 'Installing Python for the current Windows user...'
        & $winget.Source install --id Python.Python.3.13 --exact --scope user --silent --accept-source-agreements --accept-package-agreements --disable-interactivity
        $env:PATH = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
        $taskPython = Find-Python
        if (!$taskPython) { throw 'Python installation did not finish. Reopen this setup file after installing Python 3.11+.' }
    }
    if (!$taskNode) {
        # Portable official LTS package; no system-wide Node installation required.
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $taskArch = if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { 'arm64' } else { 'x64' }
        $taskFileType = "win-$taskArch-zip"
        $releases = Invoke-RestMethod -Uri 'https://nodejs.org/dist/index.json'
        $release = $releases | Where-Object { $_.lts -and $taskFileType -in $_.files -and [version]$_.version.TrimStart('v') -ge [version]'22.12.0' } | Select-Object -First 1
        if (!$release) { throw 'No supported Node LTS package found.' }
        $taskRuntime = Join-Path $taskRoot '.runtime'
        New-Item -ItemType Directory -Path $taskRuntime -Force | Out-Null
        $taskArchiveName = "node-$($release.version)-win-$taskArch.zip"
        $taskArchive = Join-Path $taskRuntime $taskArchiveName
        $taskBase = "https://nodejs.org/dist/$($release.version)"
        Write-Output 'Downloading the official Node.js LTS package...'
        Invoke-WebRequest -UseBasicParsing -Uri "$taskBase/$taskArchiveName" -OutFile $taskArchive
        $checksums = (Invoke-WebRequest -UseBasicParsing -Uri "$taskBase/SHASUMS256.txt").Content
        $checksumLine = ($checksums -split "`n" | Where-Object { $_.Trim().EndsWith("  $taskArchiveName") })
        $expected = ($checksumLine -split '\s+')[0]
        if (!$expected -or (Get-FileHash -LiteralPath $taskArchive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) { throw 'Node.js package checksum mismatch. Run setup again.' }
        Expand-Archive -LiteralPath $taskArchive -DestinationPath $taskRuntime -Force
        $taskNode = Find-Node
        if (!$taskNode) { throw 'Unable to prepare Node.js.' }
    }
    $env:PATH = (Split-Path -Parent $taskNode) + ';' + $env:PATH
    & $taskPython -X utf8 (Join-Path $PSScriptRoot 'setup.py')
    exit $LASTEXITCODE
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
