$ErrorActionPreference = 'Stop'
$env:TEMP = $PSScriptRoot
$env:TMP = $PSScriptRoot
Add-Type -AssemblyName System.Drawing

function New-Comparison([string[]]$Views, [string]$File, [string]$Title, [int]$RowHeight = 416) {
    $size = 400
    $spacing = 416
    $height = 130 + $RowHeight * $Views.Count + 48
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
        $tags = @('control', 'relaxed', 'profile')
        $names = @('r498 B control', 'r499 A | Curvature relaxation', 'r499 B | Depth profile')
        for ($column = 0; $column -lt $tags.Count; $column++) {
            $x = 16 + $spacing * $column
            $graphics.DrawString($names[$column], $label, [Drawing.Brushes]::WhiteSmoke, $x, 91)
            for ($row = 0; $row -lt $Views.Count; $row++) {
                $source = Join-Path $PSScriptRoot "$($tags[$column])-$($Views[$row]).png"
                $frame = [Drawing.Image]::FromFile($source)
                try {
                    $graphics.DrawImage($frame, [Drawing.Rectangle]::new($x, 126 + $RowHeight * $row, $size, [int][math]::Round($size*$frame.Height/$frame.Width)))
                } finally { $frame.Dispose() }
            }
        }
        $graphics.DrawString('Matched pose within each row. Continuous contact and engine checks remain open.', $footnote, [Drawing.Brushes]::LightSteelBlue, 16, $height - 42)
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

New-Comparison @('open', 'closed-oblique', 'closed-profile') 'r0499-head-comparison.png' 'r499 | Native eyelid correction'
New-Comparison @('half-blink', 'rear-oblique', 'full-body') 'r0499-blink-body-comparison.png' 'r499 | Blink and whole-character review'

New-Comparison @('closing-macro', 'closed-macro') 'r0499-macro-comparison.png' 'r499 | Closing and closed eyelid detail' 170
