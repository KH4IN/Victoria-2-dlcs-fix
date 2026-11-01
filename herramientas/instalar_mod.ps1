param([string]$Zip = '', [string]$Destino = '', [switch]$SinAntivirus)
# Instala un mod desde un .zip: revisa el contenido, lo coloca bien y no pisa nada sin copia de seguridad.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
$juego = Split-Path -Parent $PSScriptRoot
if (-not $Destino) { $Destino = Join-Path $juego 'mod' }

if (-not $Zip) {
  Add-Type -AssemblyName System.Windows.Forms
  $d = New-Object Windows.Forms.OpenFileDialog
  $d.Title = 'Elige el .zip del mod'
  $d.Filter = 'Archivos zip (*.zip)|*.zip'
  if ($d.ShowDialog() -ne 'OK') { exit 0 }
  $Zip = $d.FileName
}
if (-not (Test-Path $Zip)) { Write-Host "No encuentro $Zip"; exit 1 }
if ([IO.Path]::GetExtension($Zip) -ne '.zip') { Write-Host 'Solo admite .zip. Si es .rar o .7z, descomprímelo y vuelve a comprimirlo en .zip.'; exit 1 }

$PELIGROSOS = '.exe', '.dll', '.scr', '.bat', '.cmd', '.ps1', '.vbs', '.js', '.jse', '.msi', '.com', '.pif', '.lnk', '.reg', '.hta', '.jar'
$z = [IO.Compression.ZipFile]::OpenRead($Zip)
try {
  $entradas = @($z.Entries)
  $rutas = $entradas | ForEach-Object { $_.FullName.Replace('\', '/') }
  $malas = @($rutas | Where-Object { $_ -match '(^|/)\.\.(/|$)' -or $_ -match '^[A-Za-z]:' -or $_.StartsWith('/') })
  if ($malas.Count) { Write-Host 'Este zip tiene rutas peligrosas. Cancelado:'; $malas | Select-Object -First 5 | ForEach-Object { Write-Host "   $_" }; exit 1 }
  $ejec = @($entradas | Where-Object { $_.Name -and [IO.Path]::GetExtension($_.Name).ToLower() -in $PELIGROSOS })
  if ($ejec.Count) {
    Write-Host 'Este mod trae archivos ejecutables, algo que un mod normal no necesita. Cancelado:'
    $ejec | Select-Object -First 10 | ForEach-Object { Write-Host "   $($_.FullName)" }
    exit 1
  }
  $mods = @($entradas | Where-Object { $_.Name -like '*.mod' })
  if (-not $mods.Count) { Write-Host 'No hay ningún archivo .mod en el zip, así que no parece un mod de Victoria 2.'; exit 1 }
  if ($mods.Count -gt 1) { Write-Host 'El zip trae varios .mod. Se instalará cada uno.' }

  $tmp = Join-Path $env:TEMP ('v2mod_' + [guid]::NewGuid().ToString('N'))
  New-Item -ItemType Directory -Path $tmp | Out-Null
  try {
    [IO.Compression.ZipFileExtensions]::ExtractToDirectory($z, $tmp)
    if (-not $SinAntivirus) {
      $mp = Join-Path $env:ProgramFiles 'Windows Defender\MpCmdRun.exe'
      if (Test-Path $mp) {
        Write-Host 'Analizando con Windows Defender...'
        & $mp -Scan -ScanType 3 -File $tmp -DisableRemediation | Out-Null
        if ($LASTEXITCODE -eq 2) { Write-Host 'Defender ha detectado una amenaza. No se instala nada.'; exit 1 }
      }
    }
    foreach ($m in $mods) {
      $origenMod = Join-Path $tmp ($m.FullName.Replace('/', '\'))
      $texto = [IO.File]::ReadAllText($origenMod, [Text.Encoding]::Default)
      $nombre = [regex]::Match($texto, '(?m)^\s*name\s*=\s*"([^"]+)"').Groups[1].Value
      $ruta = [regex]::Match($texto, '(?m)^\s*path\s*=\s*"([^"]+)"').Groups[1].Value.Replace('\', '/')
      if (-not $ruta) { Write-Host "$($m.Name) no indica su carpeta (path). Saltado."; continue }
      $carpeta = $ruta.Split('/')[-1]
      # La carpeta del mod puede estar junto al .mod, dentro de mod/ o en otro nivel.
      $padre = Split-Path $origenMod -Parent
      $candidatos = @((Join-Path $padre $carpeta), (Join-Path $padre "mod\$carpeta"))
      $candidatos += @(Get-ChildItem $tmp -Recurse -Directory -Filter $carpeta | ForEach-Object { $_.FullName })
      $origen = $candidatos | Where-Object { Test-Path $_ } | Select-Object -First 1
      if (-not $origen) { Write-Host "No encuentro la carpeta '$carpeta' que pide $($m.Name). Saltado."; continue }
      $final = Join-Path $Destino $carpeta
      $finalMod = Join-Path $Destino $m.Name
      if ((Test-Path $final) -or (Test-Path $finalMod)) {
        $copia = Join-Path $Destino ("_copias\{0}_{1:yyyyMMdd_HHmmss}" -f $carpeta, (Get-Date))
        New-Item -ItemType Directory -Path $copia -Force | Out-Null
        if (Test-Path $final) { Move-Item $final (Join-Path $copia $carpeta) }
        if (Test-Path $finalMod) { Move-Item $finalMod (Join-Path $copia $m.Name) }
        Write-Host "Ya existía: la versión anterior se ha guardado en $copia"
      }
      New-Item -ItemType Directory -Path $Destino -Force | Out-Null
      Copy-Item $origen $final -Recurse
      Copy-Item $origenMod $finalMod
      $n = (Get-ChildItem $final -Recurse -File).Count
      Write-Host "Instalado: $(if ($nombre) { $nombre } else { $carpeta }) ($n archivos)"
      $noAnsi = @(Get-ChildItem $final -Recurse -File -Filter '*.txt' | Select-Object -First 400 | Where-Object {
        $b = [IO.File]::ReadAllBytes($_.FullName); $b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF })
      if ($noAnsi.Count) { Write-Host "Aviso: $($noAnsi.Count) archivos usan UTF-8 con BOM y pueden dar problemas en el juego." }
      if (Test-Path (Join-Path $final 'map\default.map')) {
        $ud = [regex]::Match($texto, '(?m)^\s*user_dir\s*=').Success
        if (-not $ud) { Write-Host 'Aviso: este mod cambia el mapa y no tiene user_dir. Usa Jugar.bat para que la versión salga bien.' }
      }
    }
  } finally {
    Remove-Item $tmp -Recurse -Force -Confirm:$false -ErrorAction SilentlyContinue
  }
} finally {
  $z.Dispose()
}
Write-Host 'Hecho. Aparecerá en el launcher y en Jugar.bat.'
