<#
.SYNOPSIS
  Harvest an Autohome gallery category into blender/reference/<car>/<dir>.

.DESCRIPTION
  Autohome's picture library (car.autohome.com.cn/pic/series/<series>-<cat>.html, <cat>:
  1 exterior, 3 cabin, 10 dashboard, 12 details, 53 official, 55 show) lists 60 photographs a
  page. This reads every page of a category, writes a manifest (id, spec, thumbnail and full
  URL, page order) and, with -Download, saves the full-size originals as c<cat>_<NNNN>.jpg
  (NNNN = position in the gallery, 1-based, the numbering the _sources.md files use).

  Run it from PowerShell, not node: the pages are only reachable through the system proxy.
  The photographs are third-party and stay local (blender/reference is gitignored); cite them
  in the car's _sources.md, as the other cars do.

.EXAMPLE
  ./scripts/autohome-harvest.ps1 -Series 8659 -Category 1 -OutDir blender/reference/xpeng-g9l/exterior -Download
#>
param(
  [Parameter(Mandatory)] [int]$Series,
  [Parameter(Mandatory)] [int]$Category,
  [Parameter(Mandatory)] [string]$OutDir,
  [switch]$Download,
  [int[]]$Only = @(),
  [int]$MaxPages = 12
)
$ErrorActionPreference = 'Stop'
$ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

function Get-Html($url) {
  for ($i = 0; $i -lt 4; $i++) {
    try {
      $r = Invoke-WebRequest -Uri $url -UserAgent $ua -UseBasicParsing -TimeoutSec 30
      return [Text.Encoding]::GetEncoding('gb18030').GetString($r.RawContentStream.ToArray())
    } catch { Start-Sleep -Seconds 2 }
  }
  throw "could not fetch $url"
}

$items = @()
for ($p = 1; $p -le $MaxPages; $p++) {
  $url = if ($p -eq 1) { "https://car.autohome.com.cn/pic/series/$Series-$Category.html" }
         else { "https://car.autohome.com.cn/pic/series/$Series-$Category-p$p.html" }
  $t = Get-Html $url
  $rx = '<a href="(https://www\.autohome\.com\.cn/cars/imgs-(\d+)-(\d+)-(\d+)-x/(\d+)\.html)" title="([^"]*)"[^>]*><img[^>]*data-webp="([^"]+)"'
  $m = [regex]::Matches($t, $rx)
  if ($m.Count -eq 0) { break }
  foreach ($x in $m) {
    $thumb = $x.Groups[7].Value
    $full = 'https:' + ($thumb -replace '/\d+x\d+_[^/]*?_autohomecar__', '/autohomecar__')
    $items += [pscustomobject]@{
      n = $items.Count + 1; id = $x.Groups[5].Value; spec = $x.Groups[3].Value
      title = $x.Groups[6].Value; page = $x.Groups[1].Value; full = $full
    }
  }
  if ($m.Count -lt 60) { break }
}
$items | ConvertTo-Json -Depth 3 | Set-Content -Encoding UTF8 (Join-Path $OutDir "manifest_c$Category.json")
"category $Category : $($items.Count) photographs"
$items | Group-Object spec | ForEach-Object { "  spec $($_.Name): $($_.Count)  ($($_.Group[0].title))" }

if ($Download) {
  foreach ($it in $items) {
    if ($Only.Count -and ($Only -notcontains $it.n)) { continue }
    $f = Join-Path $OutDir ('c{0}_{1:D4}.jpg' -f $Category, $it.n)
    if (Test-Path $f) { continue }
    for ($i = 0; $i -lt 4; $i++) {
      try { Invoke-WebRequest -Uri $it.full -UserAgent $ua -UseBasicParsing -TimeoutSec 60 -OutFile $f; break }
      catch { Start-Sleep -Seconds 2 }
    }
  }
  "downloaded to $OutDir"
}
