param([string]$Scope)
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
        $tags = @('control', 'arc', 'rolled')
        $names = @('r500 B control', 'r502 A | Arc return', 'r502 B | Rolled return')
        for ($column = 0; $column -lt $tags.Count; $column++) {
            $x = 16 + $spacing * $column
            $graphics.DrawString($names[$column], $label, [Drawing.Brushes]::WhiteSmoke, $x, 91)
            for ($row = 0; $row -lt $Views.Count; $row++) {
                $source = Join-Path $PSScriptRoot "$($tags[$column])-$($Views[$row]).png"
                if ($tags[$column] -eq 'control') {
                    $parent=Join-Path (Split-Path $PSScriptRoot) 'r0500-multi-pose-lid'
                    $source=Join-Path $parent "separated-$($Views[$row]).png"
                }
                $frame = [Drawing.Image]::FromFile($source)
                try {
                    $graphics.DrawImage($frame, [Drawing.Rectangle]::new($x, 126 + $RowHeight * $row, $size, [int][math]::Round($size*$frame.Height/$frame.Width)))
                } finally { $frame.Dispose() }
            }
        }
        $graphics.DrawString('Matched pose within each row. Both candidates failed the finite cornea contact check.', $footnote, [Drawing.Brushes]::LightSteelBlue, 16, $height - 42)
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

if($Scope -ne 'Macros'){
New-Comparison @('open', 'closed-oblique', 'closed-profile') 'r0502-head-comparison.png' 'r502 | Rebuilt eyelid return'
New-Comparison @('half-blink', 'rear-oblique', 'full-body') 'r0502-blink-body-comparison.png' 'r502 | Blink and whole-character review'

}
if($Scope -ne 'Whole'){
New-Comparison @('closing-macro', 'closed-macro') 'r0502-macro-comparison.png' 'r502 | Closing and closed eyelid detail' 170

New-Comparison @('turned-closing', 'turned-macro') 'r0502-turned-comparison.png' 'r502 | Frame 37 eyelid detail' 190

}
