param([string]$Mod = '')
# Arranca Victoria 2 dejando la caché del mapa lista, para que todos veáis el mismo código de versión.
$ErrorActionPreference = 'Stop'
$juego = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $juego 'v2game.exe'
if (-not (Test-Path $exe)) { Write-Host "No encuentro v2game.exe. Esta carpeta debe estar dentro de la del juego."; exit 1 }

$documentos = [Environment]::GetFolderPath('MyDocuments')
$base = Join-Path $documentos 'Paradox Interactive\Victoria II'

function Leer-Mod($archivo) {
  $t = [IO.File]::ReadAllText($archivo, [Text.Encoding]::Default)
  $n = [regex]::Match($t, '(?m)^\s*name\s*=\s*"([^"]+)"').Groups[1].Value
  $p = [regex]::Match($t, '(?m)^\s*path\s*=\s*"([^"]+)"').Groups[1].Value
  $u = [regex]::Match($t, '(?m)^\s*user_dir\s*=\s*"([^"]+)"').Groups[1].Value
  [pscustomobject]@{ Archivo = $archivo; Nombre = $n; Ruta = $p; UserDir = $u }
}

$mods = @(Get-ChildItem (Join-Path $juego 'mod') -Filter '*.mod' | ForEach-Object { Leer-Mod $_.FullName })
$elegido = $null
if ($Mod) {
  $elegido = $mods | Where-Object { $_.Nombre -eq $Mod -or [IO.Path]::GetFileNameWithoutExtension($_.Archivo) -eq $Mod } | Select-Object -First 1
  if (-not $elegido) { Write-Host "No existe el mod '$Mod'."; exit 1 }
} else {
  Write-Host ''
  Write-Host '  0) Juego original, sin mods'
  for ($i = 0; $i -lt $mods.Count; $i++) { Write-Host ("  {0}) {1}" -f ($i + 1), $mods[$i].Nombre) }
  Write-Host ''
  $r = Read-Host 'Elige un número'
  if ($r -notmatch '^\d+$' -or [int]$r -gt $mods.Count) { Write-Host 'Opción no válida.'; exit 1 }
  if ([int]$r -gt 0) { $elegido = $mods[[int]$r - 1] }
}

$argumentos = ''
$dirUsuario = $base
$claveMapa = 'base'
if ($elegido) {
  $argumentos = '-mod=mod/' + [IO.Path]::GetFileName($elegido.Archivo)
  if ($elegido.UserDir) { $dirUsuario = Join-Path $base $elegido.UserDir }
  elseif (Test-Path (Join-Path $juego ($elegido.Ruta + '\map\default.map'))) { $claveMapa = $elegido.Nombre }
}
New-Item -ItemType Directory -Path $dirUsuario -Force | Out-Null

# Un mod con carpeta de usuario propia no ve tu configuración: sin ella pone la intro y pierde el idioma.
$cfg = Join-Path $dirUsuario 'settings.txt'
if (-not (Test-Path $cfg)) {
  $origen = Join-Path $juego 'settings.txt'
  if (Test-Path $origen) { Copy-Item $origen $cfg }
}

# El juego calcula el código ANTES de crear la caché: la primera vez saldría otro código.
$tiempo = Join-Path $dirUsuario 'map\cache\time'
$marca = Join-Path $base 'ultimo_mapa.txt'
$anterior = if (Test-Path $marca) { (Get-Content $marca -TotalCount 1) } else { '' }
$compartida = -not ($elegido -and $elegido.UserDir)
$preparar = (-not (Test-Path $tiempo)) -or ($compartida -and $anterior -and $anterior -ne $claveMapa)

function Lanzar {
  $sp = @{ FilePath = $exe; WorkingDirectory = $juego; PassThru = $true }
  if ($argumentos) { $sp.ArgumentList = $argumentos }
  Start-Process @sp
}

if ($preparar) {
  Write-Host 'Preparando el mapa (solo hace falta una vez, tarda un par de minutos)...'
  $fecha = if (Test-Path $tiempo) { (Get-Item $tiempo).LastWriteTime } else { [datetime]::MinValue }
  $p = Lanzar
  $t0 = Get-Date
  $ultimo = -1
  $quieto = 0
  while (-not $p.HasExited -and ((Get-Date) - $t0).TotalMinutes -lt 8) {
    Start-Sleep -Seconds 2
    if ((Test-Path $tiempo) -and (Get-Item $tiempo).LastWriteTime -gt $fecha) { break }
    # Si la caché ya era válida el juego no la reescribe: basta con que llegue al menú.
    $p.Refresh()
    $cpu = [math]::Round($p.TotalProcessorTime.TotalSeconds)
    if ($cpu -eq $ultimo) { $quieto++ } else { $quieto = 0 }
    $ultimo = $cpu
    if ($quieto -ge 6 -and $p.Responding -and $p.MainWindowHandle -ne 0) { break }
  }
  Start-Sleep -Seconds 3
  if (-not $p.HasExited) { $p.Kill(); $p.WaitForExit(15000) | Out-Null }
}
if ($compartida) { Set-Content -Path $marca -Value $claveMapa -Encoding Ascii }

Lanzar | Out-Null
Write-Host 'Juego iniciado.'
