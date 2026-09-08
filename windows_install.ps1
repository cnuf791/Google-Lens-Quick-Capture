# Define paths and variables
$CurrentDir = Get-Location
$TargetFile = Join-Path $CurrentDir "q.pyw"
$DesktopDir = [Environment]::GetFolderPath("Desktop")
$ShortcutName = "q.lnk"
$ShortcutPath = Join-Path $DesktopDir $ShortcutName

# Validate that the Python script exists
if (-not (Test-Path $TargetFile)) {
    Write-Host "Error: q.pyw not found in $CurrentDir" -ForegroundColor Red
    pause
    exit 1
}

# Locate pythonw.exe to ensure it is available
$PythonW = Get-Command pythonw.exe -ErrorAction SilentlyContinue
if (-not $PythonW) {
    Write-Host "Error: pythonw.exe not found in system PATH." -ForegroundColor Red
    Write-Host "Please install Python or add it to your environment variables." -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "Target: $TargetFile"
Write-Host "Shortcut: $ShortcutPath"
Write-Host ""

# Create the desktop shortcut with hotkey
try {
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = $PythonW.Source
    $Shortcut.Arguments = "`"$TargetFile`""
    $Shortcut.WorkingDirectory = $CurrentDir
    $Shortcut.Hotkey = "CTRL+ALT+Q"
    $Shortcut.IconLocation = "$($PythonW.Source),0"
    $Shortcut.Save()

    Write-Host "OK!" -ForegroundColor Green
    Write-Host "========================================"
    Write-Host "Installation Successful"
    Write-Host "Shortcut Key: Ctrl + Alt + Q"
    Write-Host "========================================"
} catch {
    Write-Host "Error creating shortcut: $_" -ForegroundColor Red
}

pause