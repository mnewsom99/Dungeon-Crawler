$TargetFile = "c:\Users\mnews\OneDrive\Documents\AI_Projects\Dungeon-Crawler\hard_reset.bat"
# Try standard Desktop
$DesktopPath = [Environment]::GetFolderPath("Desktop")
if (-not $DesktopPath) { $DesktopPath = "$env:USERPROFILE\Desktop" }

$ShortcutFile = "$DesktopPath\Reset and Play Dungeon.lnk"
$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut($ShortcutFile)
$Shortcut.TargetPath = $TargetFile
$Shortcut.WorkingDirectory = "c:\Users\mnews\OneDrive\Documents\AI_Projects\Dungeon-Crawler"
$Shortcut.IconLocation = "c:\Users\mnews\OneDrive\Documents\AI_Projects\Dungeon-Crawler\static\img\player.png"
$Shortcut.Save()
echo "Shortcut created at $ShortcutFile"
