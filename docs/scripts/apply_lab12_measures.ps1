param([int]$Port)

$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$bin = (Get-AppxPackage Microsoft.MicrosoftPowerBIDesktop).InstallLocation + '\bin'
Add-Type -Path "$bin\Microsoft.PowerBI.Amo.Core.dll"
Add-Type -Path "$bin\Microsoft.PowerBI.Amo.dll"
if (-not $Port) {
    $ports = @(Get-NetTCPConnection -State Listen | Where-Object { $_.OwningProcess -in (Get-Process msmdsrv).Id } | Select-Object -ExpandProperty LocalPort -Unique)
    if ($ports.Count -ne 1) { throw 'Indique -Port para identificar una sola instancia de Power BI.' }
    $Port = $ports[0]
}
$server = New-Object Microsoft.AnalysisServices.Tabular.Server
try {
    $server.Connect("localhost:$Port")
    if ($server.Databases.Count -ne 1) { throw 'Se esperaba un solo modelo abierto.' }
    $model = $server.Databases[0].Model
    $table = $model.Tables.Find('Medidas')
    if (-not $table -or -not $model.Tables.Find('Observaciones')) { throw 'El modelo no corresponde al observatorio.' }
    $definitions = Get-Content -LiteralPath "$root\powerbi\medidas_hugo.json" -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($definition in $definitions.PSObject.Properties) {
        $measure = $table.Measures.Find($definition.Name)
        if (-not $measure) {
            $measure = New-Object Microsoft.AnalysisServices.Tabular.Measure
            $measure.Name = $definition.Name
            $table.Measures.Add($measure)
        }
        $measure.Expression = $definition.Value.expression
        $measure.FormatString = $definition.Value.formatString
        $measure.DisplayFolder = 'Diseño Hugo'
    }
    $calendar = $model.Tables.Find('Calendario')
    $calendar.Columns.Find('Mes').SortByColumn = $calendar.Columns.Find('MesNum')
    $null = $model.SaveChanges()
    $errors = @($table.Measures | Where-Object { $_.ErrorMessage } | Select-Object Name,ErrorMessage)
    if ($errors.Count) { throw ($errors | ConvertTo-Json) }
    Write-Output "Medidas aplicadas: $(@($definitions.PSObject.Properties).Count). Guardar el informe desde Desktop."
}
finally {
    $server.Disconnect()
}
