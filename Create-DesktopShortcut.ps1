# Create Desktop Shortcut for Google Photos Manager
# This script creates a shortcut on your desktop to launch the GUI

$WshShell = New-Object -ComObject WScript.Shell
$Desktop = [System.Environment]::GetFolderPath('Desktop')
$ShortcutPath = Join-Path $Desktop "Google Photos Manager.lnk"

$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "E:\Workspace\VS_Code_Workspace\System_Automation\Mikes_GooglePhoto-Fixer\START_GUI.vbs"
$Shortcut.WorkingDirectory = "E:\Workspace\VS_Code_Workspace\System_Automation\Mikes_GooglePhoto-Fixer"
$Shortcut.Description = "Launch Google Photos Manager - Duplicate Detection & Photo Organization"
$Shortcut.IconLocation = "%SystemRoot%\System32\imageres.dll,71"  # Photo/Image icon
$Shortcut.Save()

Write-Host "✅ Desktop shortcut created successfully!" -ForegroundColor Green
Write-Host "📍 Location: $ShortcutPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now double-click 'Google Photos Manager' on your desktop to launch the app!" -ForegroundColor Yellow
