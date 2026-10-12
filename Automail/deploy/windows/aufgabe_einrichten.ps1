# Richtet Automail als geplante Aufgabe fuer den angemeldeten Benutzer ein:
# Start bei Anmeldung, ohne Konsolenfenster, ohne Zeitbegrenzung, nur eine Instanz.
# Outlook braucht eine angemeldete Sitzung, deshalb "Nur ausfuehren, wenn Benutzer angemeldet ist".
#
# Aufruf im Projektordner:
#   powershell -ExecutionPolicy Bypass -File deploy\windows\aufgabe_einrichten.ps1
# Entfernen:
#   Unregister-ScheduledTask -TaskName Automail -Confirm:$false

$ErrorActionPreference = "Stop"
$Projekt = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Pythonw = Join-Path $Projekt ".venv\Scripts\pythonw.exe"
$Start   = Join-Path $Projekt "automail_start.py"
$Benutzer = "$env:USERDOMAIN\$env:USERNAME"

if (-not (Test-Path $Pythonw)) { throw "Nicht gefunden: $Pythonw - zuerst die venv anlegen (docs\windows.md)." }
if (-not (Test-Path (Join-Path $Projekt "config.toml"))) { throw "config.toml fehlt in $Projekt." }

$Aktion = New-ScheduledTaskAction -Execute $Pythonw -Argument "`"$Start`"" -WorkingDirectory $Projekt
$Ausloeser = New-ScheduledTaskTrigger -AtLogOn -User $Benutzer
$Einstellungen = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable
$Konto = New-ScheduledTaskPrincipal -UserId $Benutzer -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName "Automail" -Action $Aktion -Trigger $Ausloeser `
    -Settings $Einstellungen -Principal $Konto -Force `
    -Description "Automail: E-Mail-Entwuerfe aus eingehenden PDFs" | Out-Null
Start-ScheduledTask -TaskName "Automail"
Write-Host "Aufgabe 'Automail' eingerichtet und gestartet. Protokoll: siehe [pfade] protokoll in config.toml."
