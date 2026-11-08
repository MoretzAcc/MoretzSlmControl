$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
$lab=Get-Volume | Where-Object FileSystemLabel -eq LABFILES | Select-Object -First 1
Copy-Item "$($lab.DriveLetter):\peek_probe.py" C:\Lab\MoretzSlmControl\peek_probe.py -Force
$env:WINDOWS_PEEK_EXTERNAL_INPUT='1'
$env:WINDOWS_TEST_BRIDGE_TOKEN=$headers.Authorization.Substring(7)
New-Item -Path HKCU:\Software\Microsoft\Windows\DWM -Force | Out-Null
Set-ItemProperty -Path HKCU:\Software\Microsoft\Windows\DWM -Name EnableAeroPeek -Type DWord -Value 1
Set-ItemProperty -Path HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced -Name DisablePreviewDesktop -Type DWord -Value 0
Set-Location C:\Lab\MoretzSlmControl
$probe=Start-Process -FilePath C:\Lab\MoretzSlmControl\.venv\Scripts\python.exe -ArgumentList "peek_probe.py --interactive" -WorkingDirectory C:\Lab\MoretzSlmControl -Wait -PassThru -NoNewWindow -RedirectStandardOutput C:\Lab\peek.stdout.log -RedirectStandardError C:\Lab\peek.stderr.log
Get-Content C:\Lab\peek.stderr.log
if ($probe.ExitCode -ne 0) {throw "Peek probe exited with $($probe.ExitCode)"}
Get-Content C:\Lab\peek\result.json -Raw
