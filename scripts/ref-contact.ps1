<#
  Contact sheet of a reference folder: numbered thumbnails, 4 x 3 per sheet.
  usage: contact.ps1 -Dir <folder> -Out <prefix> [-From 1] [-To 999] [-Cols 4] [-Rows 3] [-Cell 480]
#>
param([string]$Dir, [string]$Out, [int]$From = 1, [int]$To = 9999, [int]$Cols = 4, [int]$Rows = 3, [int]$Cell = 480)
Add-Type -AssemblyName System.Drawing
$files = Get-ChildItem $Dir -Filter *.jpg | Sort-Object Name
$sel = @(); foreach ($f in $files) { if ($f.BaseName -match '_(\d+)$') { $n = [int]$Matches[1]; if ($n -ge $From -and $n -le $To) { $sel += [pscustomobject]@{ n = $n; f = $f } } } }
$per = $Cols * $Rows
$ch = [int]($Cell * 0.75)
for ($s = 0; $s * $per -lt $sel.Count; $s++) {
  $bmp = New-Object System.Drawing.Bitmap ($Cols * $Cell), ($Rows * $ch)
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.Clear([System.Drawing.Color]::Black)
  $g.InterpolationMode = 'HighQualityBicubic'
  $font = New-Object System.Drawing.Font 'Arial', 18, ([System.Drawing.FontStyle]::Bold)
  for ($i = 0; $i -lt $per; $i++) {
    $k = $s * $per + $i; if ($k -ge $sel.Count) { break }
    $img = [System.Drawing.Image]::FromFile($sel[$k].f.FullName)
    $x = ($i % $Cols) * $Cell; $y = [math]::Floor($i / $Cols) * $ch
    $r = [math]::Min($Cell / $img.Width, $ch / $img.Height)
    $w = $img.Width * $r; $h = $img.Height * $r
    $g.DrawImage($img, $x + ($Cell - $w) / 2, $y + ($ch - $h) / 2, $w, $h)
    $g.FillRectangle([System.Drawing.Brushes]::Black, $x, $y, 70, 30)
    $g.DrawString([string]$sel[$k].n, $font, [System.Drawing.Brushes]::Yellow, $x + 2, $y + 1)
    $img.Dispose()
  }
  $path = "{0}_{1}.jpg" -f $Out, ($s + 1)
  $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Jpeg)
  $g.Dispose(); $bmp.Dispose()
  $path
}
