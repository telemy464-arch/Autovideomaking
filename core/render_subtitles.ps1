param([string]$jsonPath)
Add-Type -AssemblyName System.Drawing

$raw = [System.IO.File]::ReadAllText($jsonPath, [System.Text.Encoding]::UTF8)
$data = $raw | ConvertFrom-Json
$fmt = [System.Drawing.StringFormat]::new()
$fmt.Alignment = [System.Drawing.StringAlignment]::Center
$fmt.LineAlignment = [System.Drawing.StringAlignment]::Center

$font = [System.Drawing.Font]::new("Nirmala UI", [float]$data.fontSize, [System.Drawing.FontStyle]::Bold)
$blackBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 0, 0, 0))
$yellowBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 255, 235, 59))

foreach ($item in $data.subtitles) {
    $bmp = [System.Drawing.Bitmap]::new($data.width, 220)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
    $rect = [System.Drawing.RectangleF]::new(20, 10, $data.width - 40, 200)

    for ($dx = -3; $dx -le 3; $dx++) {
        for ($dy = -3; $dy -le 3; $dy++) {
            if ($dx -ne 0 -or $dy -ne 0) {
                $oRect = [System.Drawing.RectangleF]::new($rect.X + $dx, $rect.Y + $dy, $rect.Width, $rect.Height)
                $g.DrawString($item.text, $font, $blackBrush, $oRect, $fmt)
            }
        }
    }
    $g.DrawString($item.text, $font, $yellowBrush, $rect, $fmt)
    
    $bmp.Save($item.outPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose()
    $bmp.Dispose()
}
$font.Dispose()
$blackBrush.Dispose()
$yellowBrush.Dispose()
Write-Host "All subtitles generated successfully!"
