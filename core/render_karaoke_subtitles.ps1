param([string]$jsonPath)
Add-Type -AssemblyName System.Drawing

$raw = [System.IO.File]::ReadAllText($jsonPath, [System.Text.Encoding]::UTF8)
$data = $raw | ConvertFrom-Json

$font = [System.Drawing.Font]::new("Nirmala UI", [float]$data.fontSize, [System.Drawing.FontStyle]::Bold)
$sf = [System.Drawing.StringFormat]::GenericTypographic
$sf.FormatFlags = [System.Drawing.StringFormatFlags]::NoClip -bor [System.Drawing.StringFormatFlags]::MeasureTrailingSpaces

$whiteBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 255, 255, 255))
$blackBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 0, 0, 0))
$pinkBadgeBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(240, 255, 20, 147))

foreach ($item in $data.subtitles) {
    $bmp = [System.Drawing.Bitmap]::new($data.width, 240)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
    
    $words = $item.words
    $activeIdx = [int]$item.activeWordIndex

    if ($words.Count -eq 0 -or $item.isTransparent -eq $true) {
        $bmp.Save($item.outPath, [System.Drawing.Imaging.ImageFormat]::Png)
        $g.Dispose()
        $bmp.Dispose()
        continue
    }
    
    $wordSizes = @()
    $totalW = 0
    $spaceW = ($g.MeasureString(" ", $font, [System.Drawing.PointF]::new(0,0), $sf)).Width
    
    foreach ($w in $words) {
        $sz = $g.MeasureString($w, $font, [System.Drawing.PointF]::new(0,0), $sf)
        $wordSizes += $sz
        $totalW += $sz.Width
    }
    if ($words.Count -gt 1) {
        $totalW += $spaceW * ($words.Count - 1)
    }
    
    $startX = ($data.width - $totalW) / 2
    $curX = $startX
    $curY = 80
    
    for ($i = 0; $i -lt $words.Count; $i++) {
        $w = $words[$i]
        $sz = $wordSizes[$i]
        
        if ($i -eq $activeIdx) {
            $padX = 14
            $padY = 8
            $r = 16
            $hRect = [System.Drawing.RectangleF]::new($curX - $padX, $curY - $padY, $sz.Width + ($padX * 2), $sz.Height + ($padY * 2))
            
            $path = [System.Drawing.Drawing2D.GraphicsPath]::new()
            $path.AddArc($hRect.X, $hRect.Y, $r, $r, 180, 90)
            $path.AddArc($hRect.Right - $r, $hRect.Y, $r, $r, 270, 90)
            $path.AddArc($hRect.Right - $r, $hRect.Bottom - $r, $r, $r, 0, 90)
            $path.AddArc($hRect.X, $hRect.Bottom - $r, $r, $r, 90, 90)
            $path.CloseFigure()
            $g.FillPath($pinkBadgeBrush, $path)
            $path.Dispose()
        }
        
        for ($dx = -3; $dx -le 3; $dx++) {
            for ($dy = -3; $dy -le 3; $dy++) {
                if ($dx -ne 0 -or $dy -ne 0) {
                    $g.DrawString($w, $font, $blackBrush, [System.Drawing.PointF]::new($curX + $dx, $curY + $dy), $sf)
                }
            }
        }
        
        $g.DrawString($w, $font, $whiteBrush, [System.Drawing.PointF]::new($curX, $curY), $sf)
        
        $curX += $sz.Width + $spaceW
    }
    
    $bmp.Save($item.outPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose()
    $bmp.Dispose()
}

$font.Dispose()
$whiteBrush.Dispose()
$blackBrush.Dispose()
$pinkBadgeBrush.Dispose()
Write-Host "Karaoke subtitle frames generated successfully!"