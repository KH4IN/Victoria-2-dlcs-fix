param([string]$Juego = '')
# Aplica las correcciones a UPM. Solo cambia archivos originales reconocidos y guarda antes una copia.
$ErrorActionPreference = 'Stop'
if (-not $Juego) { $Juego = Split-Path -Parent $PSScriptRoot }
if (-not (Test-Path -LiteralPath (Join-Path $Juego 'v2game.exe'))) {
  Write-Host 'No encuentro v2game.exe. Descomprime esta carpeta dentro de la carpeta del juego.'
  exit 1
}
if (-not (Test-Path -LiteralPath (Join-Path $Juego 'mod\UPM'))) {
  Write-Host 'No encuentro mod\UPM. Instala antes Universal Project Mod 2.05 sin tocar.'
  exit 1
}
if (Get-Process v2game -ErrorAction SilentlyContinue) { Write-Host 'Cierra el juego antes de aplicar las correcciones.'; exit 1 }

$sha = [Security.Cryptography.SHA256]::Create()
function Huella([byte[]]$b) { [BitConverter]::ToString($sha.ComputeHash($b)).Replace('-', '').ToLower() }
function Ruta([string]$r) { Join-Path $Juego $r.Replace('/', '\') }
function Montar([byte[]]$d, $cambios) {
  $m = New-Object IO.MemoryStream
  $ult = 0
  foreach ($e in $cambios) {
    $m.Write($d, $ult, $e.Pos - $ult)
    $m.Write($e.Nuevo, 0, $e.Nuevo.Length)
    $ult = $e.Pos + $e.Quita
  }
  $m.Write($d, $ult, $d.Length - $ult)
  return , $m.ToArray()
}
function Rechazar([string]$r) {
  Write-Host "Este archivo es distinto del esperado: $r"
  Write-Host 'Tu copia no es la misma. No se ha cambiado nada.'
  exit 1
}

$entradas = New-Object Collections.ArrayList
$actual = $null
foreach ($l in [IO.File]::ReadAllLines((Join-Path $PSScriptRoot 'parche.txt'))) {
  $c = $l.Split("`t")
  switch ($c[0]) {
    'E' { [void]$actual.Cambios.Add([pscustomobject]@{ Pos = [int]$c[1]; Quita = [int]$c[2]; Nuevo = [Convert]::FromBase64String($c[3]) }) }
    'F' { $actual = [pscustomobject]@{ Tipo = 'F'; Ruta = $c[1]; Antes = $c[2]; Despues = $c[3]; Fuente = $c[1]; Cambios = New-Object Collections.ArrayList; Datos = $null }; [void]$entradas.Add($actual) }
    'N' { $actual = [pscustomobject]@{ Tipo = 'N'; Ruta = $c[1]; Antes = $c[3]; Despues = $c[4]; Fuente = $c[2]; Cambios = New-Object Collections.ArrayList; Datos = $null }; [void]$entradas.Add($actual) }
    'D' { [void]$entradas.Add([pscustomobject]@{ Tipo = 'D'; Ruta = $c[1]; Antes = $c[2] }) }
    'B' {
      $p = Ruta $c[1]
      if (-not (Test-Path -LiteralPath $p) -or (Huella ([IO.File]::ReadAllBytes($p))) -ne $c[2]) {
        Write-Host 'Falta corregir el juego base. Aplica primero Correcciones_V2_base.zip. No se ha cambiado nada.'
        exit 1
      }
    }
  }
}

# Primero se comprueba y se prepara todo: o se aplica entero o no se toca nada.
$pendientes = New-Object Collections.ArrayList
$hechos = 0
foreach ($a in $entradas) {
  $p = Ruta $a.Ruta
  $hay = Test-Path -LiteralPath $p
  if ($a.Tipo -eq 'D') {
    if (-not $hay) { $hechos++; continue }
    if ((Huella ([IO.File]::ReadAllBytes($p))) -ne $a.Antes) { Rechazar $a.Ruta }
    [void]$pendientes.Add($a)
    continue
  }
  if ($hay) {
    $h = Huella ([IO.File]::ReadAllBytes($p))
    if ($h -eq $a.Despues) { $hechos++; continue }
    if ($a.Tipo -eq 'N' -or $h -ne $a.Antes) { Rechazar $a.Ruta }
  } elseif ($a.Tipo -eq 'F') {
    Write-Host "Falta el archivo: $($a.Ruta)"
    Write-Host 'No se ha cambiado nada.'
    exit 1
  }
  $d = [byte[]]@()
  if ($a.Fuente -ne '-') {
    $f = Ruta $a.Fuente
    if (-not (Test-Path -LiteralPath $f)) { Write-Host "Falta el archivo: $($a.Fuente)"; Write-Host 'No se ha cambiado nada.'; exit 1 }
    $d = [IO.File]::ReadAllBytes($f)
    if ((Huella $d) -ne $a.Antes) { Rechazar $a.Fuente }
  }
  $a.Datos = Montar $d $a.Cambios
  if ((Huella $a.Datos) -ne $a.Despues) { Write-Host "Error al preparar $($a.Ruta). No se ha cambiado nada."; exit 1 }
  [void]$pendientes.Add($a)
}
if (-not $pendientes.Count) { Write-Host 'Las correcciones ya estaban aplicadas. No hay nada que hacer.'; exit 0 }

$copia = Join-Path $Juego '_copia_antes_de_corregir_UPM'
foreach ($t in 'F', 'N', 'D') {
  foreach ($a in $pendientes) {
    if ($a.Tipo -ne $t) { continue }
    $p = Ruta $a.Ruta
    $c = Join-Path $copia $a.Ruta.Replace('/', '\')
    if ($t -eq 'N') {
      [void][IO.Directory]::CreateDirectory((Split-Path -Parent $p))
    } else {
      [void][IO.Directory]::CreateDirectory((Split-Path -Parent $c))
      [IO.File]::Copy($p, $c, $true)
    }
    if ($t -eq 'D') { [IO.File]::Delete($p) } else { [IO.File]::WriteAllBytes($p, $a.Datos) }
  }
}
Write-Host ''
Write-Host "Hecho: $($pendientes.Count) archivos corregidos."
Write-Host "Los originales están en: $copia"
Write-Host 'Abre el launcher y marca Universal Project Mod. El código del menú debe ser V2 v3.04 (DWUE).'
Write-Host 'La primera vez en un PC puede salir otro: abre y cierra el juego una vez.'
