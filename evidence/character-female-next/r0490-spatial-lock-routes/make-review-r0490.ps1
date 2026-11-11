$ErrorActionPreference = 'Stop'
$env:TEMP = $PSScriptRoot
$env:TMP = $PSScriptRoot
Add-Type -AssemblyName System.Drawing

function New-Comparison([string[]]$Views, [string]$File, [string]$Title) {
    $size = 400
    $spacing = 416
    $height = 130 + $spacing * $Views.Count + 48
    $canvas = [Drawing.Bitmap]::new(1272, $height)
    $graphics = [Drawing.Graphics]::FromImage($canvas)
    $heading = [Drawing.Font]::new('Segoe UI', 23)
    $label = [Drawing.Font]::new('Segoe UI', 15)
    $footnote = [Drawing.Font]::new('Segoe UI', 12)
    try {
        $graphics.Clear([Drawing.Color]::FromArgb(21, 24, 28))
        $graphics.InterpolationMode = [Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $graphics.DrawString($Title, $heading, [Drawing.Brushes]::WhiteSmoke, 16, 12)
        $graphics.DrawString('Matched cameras, lights, pose, shader, strand radii and exposure.', $footnote, [Drawing.Brushes]::LightSteelBlue, 16, 55)
        $tags = @('control', 'waves', 'swept')
        $names = @('r488 A control', 'r490 A | Loose waves', 'r490 B | Asymmetric sweep')
        for ($column = 0; $column -lt $tags.Count; $column++) {
            $x = 16 + $spacing * $column
            $graphics.DrawString($names[$column], $label, [Drawing.Brushes]::WhiteSmoke, $x, 91)
            for ($row = 0; $row -lt $Views.Count; $row++) {
                $source = Join-Path $PSScriptRoot "$($tags[$column])-$($Views[$row]).png"
                $frame = [Drawing.Image]::FromFile($source)
                try {
                    $graphics.DrawImage($frame, [Drawing.Rectangle]::new($x, 126 + $spacing * $row, $size, $size))
                } finally { $frame.Dispose() }
            }
        }
        $graphics.DrawString('Matched neutral appearance study. Full contact, motion and engine checks remain open.', $footnote, [Drawing.Brushes]::LightSteelBlue, 16, $height - 42)
        $path = Join-Path $PSScriptRoot $File
        if (Test-Path -LiteralPath $path) { throw 'Comparison already exists' }
        $canvas.Save($path, [Drawing.Imaging.ImageFormat]::Png)
    } finally {
        $graphics.Dispose()
        $canvas.Dispose()
        $heading.Dispose()
        $label.Dispose()
        $footnote.Dispose()
    }
}

New-Comparison @('face', 'rear-oblique', 'opposite-profile') 'r0490-head-comparison.png' 'r490 | Full-length spatial locks'
New-Comparison @('posterior-detail', 'full-body') 'r0490-posterior-body-comparison.png' 'r490 | Posterior detail and whole-woman silhouette'
