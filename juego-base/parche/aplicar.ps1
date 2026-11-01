param([string]$Juego = '')
# Aplica las correcciones al juego base. Solo cambia archivos originales reconocidos y guarda antes una copia.
$ErrorActionPreference = 'Stop'
if (-not $Juego) { $Juego = Split-Path -Parent $PSScriptRoot }
if (-not (Test-Path (Join-Path $Juego 'v2game.exe'))) {
  Write-Host 'No encuentro v2game.exe. Descomprime esta carpeta dentro de la carpeta del juego.'
  exit 1
}
if (Get-Process v2game -ErrorAction SilentlyContinue) { Write-Host 'Cierra el juego antes de aplicar las correcciones.'; exit 1 }

$sha = [Security.Cryptography.SHA256]::Create()
function Huella([byte[]]$b) { [BitConverter]::ToString($sha.ComputeHash($b)).Replace('-', '').ToLower() }

$archivos = New-Object Collections.ArrayList
$actual = $null
foreach ($l in [IO.File]::ReadAllLines((Join-Path $PSScriptRoot 'parche.txt'))) {
  $c = $l.Split("`t")
  if ($c[0] -eq 'F') {
    $actual = [pscustomobject]@{ Ruta = $c[1]; Antes = $c[2]; Despues = $c[3]; Cambios = New-Object Collections.ArrayList }
    [void]$archivos.Add($actual)
  } elseif ($c[0] -eq 'E') {
    [void]$actual.Cambios.Add([pscustomobject]@{ Pos = [int]$c[1]; Quita = [int]$c[2]; Nuevo = [Convert]::FromBase64String($c[3]) })
  }
}

# Primero se comprueba todo: o se aplica entero o no se toca nada.
$pendientes = New-Object Collections.ArrayList
$hechos = 0
foreach ($a in $archivos) {
  $p = Join-Path $Juego $a.Ruta
  if (-not (Test-Path -LiteralPath $p)) { Write-Host "Falta el archivo: $($a.Ruta)"; exit 1 }
  $h = Huella ([IO.File]::ReadAllBytes($p))
  if ($h -eq $a.Despues) { $hechos++ }
  elseif ($h -eq $a.Antes) { [void]$pendientes.Add($a) }
  else {
    Write-Host "Este archivo es distinto del original esperado: $($a.Ruta)"
    Write-Host 'Tu copia del juego no es la misma. No se ha cambiado nada.'
    exit 1
  }
}
if (-not $pendientes.Count) { Write-Host 'Las correcciones ya estaban aplicadas. No hay nada que hacer.'; exit 0 }

$copia = Join-Path $Juego '_copia_antes_de_corregir'
foreach ($a in $pendientes) {
  $p = Join-Path $Juego $a.Ruta
  $d = [IO.File]::ReadAllBytes($p)
  $m = New-Object IO.MemoryStream
  $ult = 0
  foreach ($e in $a.Cambios) {
    $m.Write($d, $ult, $e.Pos - $ult)
    $m.Write($e.Nuevo, 0, $e.Nuevo.Length)
    $ult = $e.Pos + $e.Quita
  }
  $m.Write($d, $ult, $d.Length - $ult)
  $n = $m.ToArray()
  if ((Huella $n) -ne $a.Despues) { Write-Host "Error al preparar $($a.Ruta). No se ha cambiado este archivo."; exit 1 }
  $c = Join-Path $copia $a.Ruta
  New-Item -ItemType Directory -Path (Split-Path -Parent $c) -Force | Out-Null
  Copy-Item -LiteralPath $p -Destination $c -Force
  [IO.File]::WriteAllBytes($p, $n)
}
Write-Host ''
Write-Host "Hecho: $($pendientes.Count) archivos corregidos."
Write-Host "Los originales están en: $copia"
Write-Host 'Abre el juego como siempre. El código del menú debe ser V2 v3.04 (YYWO).'
Write-Host 'La primera vez en un PC puede salir otro: abre y cierra el juego una vez.'
