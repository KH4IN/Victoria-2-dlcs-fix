param([string]$Comparar = '')
# Crea la "huella" de tu instalación y la compara con la de un amigo para ver qué archivo os separa.
$ErrorActionPreference = 'Stop'
$juego = Split-Path -Parent $PSScriptRoot
$carpetas = 'common', 'decisions', 'events', 'history', 'inventions', 'technologies', 'units', 'poptypes', 'script', 'missions', 'battleplans'

function Listar($raiz, $prefijo) {
  foreach ($c in $carpetas) {
    $d = Join-Path $raiz $c
    if (Test-Path $d) {
      Get-ChildItem $d -Recurse -File | Where-Object { $_.Extension -in '.txt', '.lua', '.pln', '.csv' } |
        ForEach-Object { [pscustomobject]@{ Ruta = $prefijo + $_.FullName.Substring($raiz.Length + 1).Replace('\', '/'); Archivo = $_.FullName } }
    }
  }
  $m = Join-Path $raiz 'map\default.map'
  if (Test-Path $m) { [pscustomobject]@{ Ruta = $prefijo + 'map/default.map'; Archivo = $m } }
}

$mods = @(Get-ChildItem (Join-Path $juego 'mod') -Filter '*.mod')
Write-Host ''
Write-Host '¿Con qué vais a jugar?'
Write-Host '  0) Juego sin mods'
for ($i = 0; $i -lt $mods.Count; $i++) { Write-Host ("  {0}) {1}" -f ($i + 1), $mods[$i].BaseName) }
$r = Read-Host 'Elige un número'
if ($r -notmatch '^\d+$' -or [int]$r -gt $mods.Count) { Write-Host 'Opción no válida.'; exit 1 }
$nombre = 'juego'
$lista = @(Listar $juego '')
$lista += [pscustomobject]@{ Ruta = 'v2game.exe'; Archivo = (Join-Path $juego 'v2game.exe') }
if ([int]$r -gt 0) {
  $f = $mods[[int]$r - 1]
  $nombre = $f.BaseName
  $t = [IO.File]::ReadAllText($f.FullName, [Text.Encoding]::Default)
  $ruta = [regex]::Match($t, '(?m)^\s*path\s*=\s*"([^"]+)"').Groups[1].Value
  $lista += @(Listar (Join-Path $juego $ruta) "MOD/")
}

Write-Host "Calculando la huella de $($lista.Count) archivos..."
$sha = [Security.Cryptography.SHA256]::Create()
$lineas = $lista | Sort-Object Ruta | ForEach-Object {
  $s = [IO.File]::OpenRead($_.Archivo)
  try { $h = [BitConverter]::ToString($sha.ComputeHash($s)).Replace('-', '').ToLower() } finally { $s.Dispose() }
  "$h  $($_.Ruta)"
}
$todo = [BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes(($lineas -join "`n")))).Replace('-', '').Substring(0, 8)
$salida = Join-Path $PSScriptRoot "huella_$nombre.txt"
Set-Content -Path $salida -Value $lineas -Encoding UTF8
Write-Host ''
Write-Host "Tu huella es: $todo"
Write-Host 'Si tus amigos tienen esta misma huella, tenéis exactamente los mismos archivos.'
Write-Host "Se ha guardado en: $salida"
Write-Host ''
Write-Host 'Si la huella coincide pero el código del juego (abajo a la izquierda) no, abre y cierra el juego'
Write-Host 'una vez: es la caché del mapa, que se crea la primera vez.'

if (-not $Comparar) {
  Write-Host ''
  $Comparar = Read-Host 'Arrastra aquí el archivo de huella de tu amigo y pulsa Enter (o solo Enter para terminar)'
  $Comparar = $Comparar.Trim('"', ' ')
}
if ($Comparar) {
  if (-not (Test-Path $Comparar)) { Write-Host 'No encuentro ese archivo.'; exit 1 }
  $parsea = { param($ls) $d = @{}; foreach ($l in $ls) { if ($l -match '^([0-9a-f]{64})  (.+)$') { $d[$Matches[2]] = $Matches[1] } }; $d }
  $yo = & $parsea $lineas
  $el = & $parsea (Get-Content $Comparar -Encoding UTF8)
  $distintos = @($yo.Keys | Where-Object { $el.ContainsKey($_) -and $el[$_] -ne $yo[$_] } | Sort-Object)
  $solo1 = @($yo.Keys | Where-Object { -not $el.ContainsKey($_) } | Sort-Object)
  $solo2 = @($el.Keys | Where-Object { -not $yo.ContainsKey($_) } | Sort-Object)
  if (($distintos.Count + $solo1.Count + $solo2.Count) -eq 0) { Write-Host 'Coincidís en todo.'; exit 0 }
  Write-Host "Archivos distintos: $($distintos.Count)"; $distintos | Select-Object -First 40 | ForEach-Object { Write-Host "   $_" }
  Write-Host "Solo los tienes tú: $($solo1.Count)"; $solo1 | Select-Object -First 40 | ForEach-Object { Write-Host "   $_" }
  Write-Host "Solo los tiene tu amigo: $($solo2.Count)"; $solo2 | Select-Object -First 40 | ForEach-Object { Write-Host "   $_" }
}
