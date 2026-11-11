param([switch]$FrontalOnly)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
Set-Location -LiteralPath $PSScriptRoot
$records=(Get-Content -LiteralPath preview-progress.json -Raw | ConvertFrom-Json -AsHashtable)
$modes=@('control','side_sweep','over_under')
$labels=@('r0507 B','A | Side sweep','B | Layered sweep')
$bg=[Drawing.Color]::FromArgb(18,23,27)
$colors=@([Drawing.Color]::FromArgb(216,224,229),[Drawing.Color]::FromArgb(229,198,150),[Drawing.Color]::FromArgb(166,223,205))
$font=[Drawing.Font]::new('Segoe UI',16,[Drawing.FontStyle]::Regular,[Drawing.GraphicsUnit]::Pixel)
$large=[Drawing.Font]::new('Segoe UI',23,[Drawing.FontStyle]::Bold,[Drawing.GraphicsUnit]::Pixel)
$small=[Drawing.Font]::new('Segoe UI',14,[Drawing.FontStyle]::Regular,[Drawing.GraphicsUnit]::Pixel)

function DrawShot($g,[string]$mode,[string]$view,[int]$x,[int]$y,[int]$width,[int]$height){
    $item=$records["${mode}:$view"]
    if(-not $item){throw "Missing $mode $view"}
    $image=[Drawing.Image]::FromFile($item.path)
    try{
        $s=[Math]::Min($width/$image.Width,$height/$image.Height)
        $w=[int][Math]::Round($image.Width*$s)
        $h=[int][Math]::Round($image.Height*$s)
        $g.DrawImage($image,($x+[int](($width-$w)/2)),($y+[int](($height-$h)/2)),$w,$h)
    }finally{$image.Dispose()}
}

function Board([string]$name,[string]$title,[array]$views,[array]$captions,[int]$width=380,[int]$height=365){
    $bmp=[Drawing.Bitmap]::new((46+3*$width),(84+($height+29)*$views.Count))
    $g=[Drawing.Graphics]::FromImage($bmp)
    try{
        $g.Clear($bg)
        $g.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $g.TextRenderingHint=[Drawing.Text.TextRenderingHint]::AntiAliasGridFit
        $g.DrawString($title,$large,[Drawing.Brushes]::WhiteSmoke,24,13)
        for($j=0;$j -lt $modes.Count;$j++){
            $brush=[Drawing.SolidBrush]::new($colors[$j])
            try{$g.DrawString($labels[$j],$font,$brush,(29+$width*$j),53)}finally{$brush.Dispose()}
        }
        for($i=0;$i -lt $views.Count;$i++){
            $y=82+($height+29)*$i
            $g.DrawString($captions[$i],$small,[Drawing.Brushes]::WhiteSmoke,26,$y)
            for($j=0;$j -lt $modes.Count;$j++){
                DrawShot $g $modes[$j] $views[$i] (24+$width*$j) ($y+21) ($width-5) $height
            }
        }
        $bmp.Save((Join-Path $PSScriptRoot $name),[Drawing.Imaging.ImageFormat]::Png)
    }finally{$g.Dispose();$bmp.Dispose()}
}

Board 'r0508-frontal-comparison.png' 'Aevrynd r0508   |   Frontal and crown sweep' @('front','oblique','crown') @('Front','Three-quarter','Crown')
if($FrontalOnly){exit 0}
Board 'r0508-profile-comparison.png' 'Aevrynd r0508   |   Sides and rear' @('profile','opposite','rear-oblique') @('Left profile','Right profile','Rear three-quarter')
Board 'r0508-body-comparison.png' 'Aevrynd r0508   |   Whole character and pose' @('full','turn','blink') @('Whole character','32-degree head turn','Blink') 380 366
