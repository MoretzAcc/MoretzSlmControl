param(
    [ValidateSet('Inventory', 'Matrix', 'Hotplug')]
    [string]$Mode = 'Inventory',
    [string]$OutputDirectory
)

$ErrorActionPreference = 'Stop'
$projectPath = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$pythonPath = Join-Path $projectPath '.venv\Scripts\pythonw.exe'
$reviewPath = Join-Path $projectPath 'dev\windows_review.py'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Run uv sync --locked in the project first.'
}
if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $PSScriptRoot ('local-results\' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
}
$OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
if ($Mode -eq 'Hotplug') {
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Hotplug mode requires an elevated PowerShell to disable/re-enable the VDD device.'
    }
    if ((Test-Path (Join-Path $OutputDirectory 'ready.flag')) -or
        (Test-Path (Join-Path $OutputDirectory 'disconnected.flag'))) {
        throw 'Use a fresh output directory for each hotplug cycle.'
    }
    $vddDevices = @(Get-PnpDevice -Class Display | Where-Object FriendlyName -eq 'Virtual Display Driver')
    if ($vddDevices.Count -ne 1 -or $vddDevices[0].Status -ne 'OK') {
        throw 'Hotplug mode requires exactly one enabled Virtual Display Driver device.'
    }
    $vddInstance = $vddDevices[0].InstanceId
}

$outputTarget = if ($Mode -eq 'Inventory') { Join-Path $OutputDirectory 'environment.json' } else { $OutputDirectory }
$reviewArguments = '"{0}" --output "{1}"' -f $reviewPath, $outputTarget
if ($Mode -ne 'Inventory') { $reviewArguments += ' --' + $Mode.ToLowerInvariant() }
$taskName = 'MoretzSlmControl-Review-' + [guid]::NewGuid().ToString('N')
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument $reviewArguments -WorkingDirectory $projectPath
$taskPrincipal = New-ScheduledTaskPrincipal -UserId $identity.Name -LogonType Interactive -RunLevel Limited
$taskSettings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 5)
$vddDisabled = $false
try {
    Register-ScheduledTask -TaskName $taskName -Action $action -Principal $taskPrincipal -Settings $taskSettings | Out-Null
    Start-ScheduledTask -TaskName $taskName
    if ($Mode -eq 'Hotplug') {
        $readyDeadline = (Get-Date).AddSeconds(45)
        while (-not (Test-Path (Join-Path $OutputDirectory 'ready.flag'))) {
            if ((Get-Date) -gt $readyDeadline) { throw 'Review did not become ready; inspect runtime.log.' }
            Start-Sleep -Milliseconds 250
        }
        Disable-PnpDevice -InstanceId $vddInstance -Confirm:$false
        $vddDisabled = $true
        $disconnectDeadline = (Get-Date).AddSeconds(30)
        while (-not (Test-Path (Join-Path $OutputDirectory 'disconnected.flag'))) {
            if ((Get-Date) -gt $disconnectDeadline) { throw 'Disconnect verification timed out.' }
            Start-Sleep -Milliseconds 250
        }
        Enable-PnpDevice -InstanceId $vddInstance -Confirm:$false
        $vddDisabled = $false
    }
    Start-Sleep -Milliseconds 500
    $deadline = (Get-Date).AddMinutes(5)
    while ((Get-ScheduledTask -TaskName $taskName).State -eq 'Running') {
        if ((Get-Date) -gt $deadline) { throw 'Review exceeded five minutes.' }
        Start-Sleep -Milliseconds 500
    }
    $result = (Get-ScheduledTaskInfo -TaskName $taskName).LastTaskResult
    Write-Output "Review output: $OutputDirectory"
    if ($result -ne 0) { throw "Review exited with code $result. Inspect the JSON findings and runtime.log." }
}
finally {
    if ($vddDisabled) { Enable-PnpDevice -InstanceId $vddInstance -Confirm:$false }
    if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
        if ((Get-ScheduledTask -TaskName $taskName).State -eq 'Running') {
            Stop-ScheduledTask -TaskName $taskName
        }
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    }
}
