param([switch]$StaticOnly)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
Set-Location -LiteralPath $PSScriptRoot
$records=(Get-Content -LiteralPath preview-progress.json -Raw | ConvertFrom-Json -AsHashtable)
$modes=@('rigid','spring','rod')
$headings=@('Rigid head follow','Spring guides','Projected guides')
$palette=@([Drawing.Color]::FromArgb(208,218,223),[Drawing.Color]::FromArgb(166,220,206),[Drawing.Color]::FromArgb(235,199,149))
$bg=[Drawing.Color]::FromArgb(18,23,27)
$textColor=[Drawing.Brushes]::WhiteSmoke
$font=[Drawing.Font]::new('Segoe UI',15,[Drawing.FontStyle]::Regular,[Drawing.GraphicsUnit]::Pixel)
$large=[Drawing.Font]::new('Segoe UI',22,[Drawing.FontStyle]::Bold,[Drawing.GraphicsUnit]::Pixel)
$small=[Drawing.Font]::new('Segoe UI',13,[Drawing.FontStyle]::Regular,[Drawing.GraphicsUnit]::Pixel)

function DrawShot($g,[string]$mode,[string]$view,[int]$x,[int]$y,[int]$width,[int]$height) {
    $item=$records["${mode}:$view"]
    if(-not $item){throw "Missing $mode $view"}
    $img=[Drawing.Image]::FromFile($item.path)
    try {
        $s=[Math]::Min($width/$img.Width,$height/$img.Height)
        $w=[int][Math]::Round($img.Width*$s)
        $h=[int][Math]::Round($img.Height*$s)
        $g.DrawImage($img,($x+[int](($width-$w)/2)),($y+[int](($height-$h)/2)),$w,$h)
    } finally {$img.Dispose()}
}

function Board([string]$name,[string]$title,[array]$views,[array]$captions,[int]$tileWidth=346,[int]$tileHeight=325) {
    $width=48+3*$tileWidth
    $height=83+($tileHeight+26)*$views.Count
    $bmp=[Drawing.Bitmap]::new($width,$height)
    $g=[Drawing.Graphics]::FromImage($bmp)
    try {
        $g.Clear($bg)
        $g.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $g.TextRenderingHint=[Drawing.Text.TextRenderingHint]::AntiAliasGridFit
        $g.DrawString($title,$large,$textColor,24,14)
        for($j=0;$j -lt $modes.Count;$j++){
            $brush=[Drawing.SolidBrush]::new($palette[$j])
            try{$g.DrawString($headings[$j],$font,$brush,(24+$tileWidth*$j+6),53)}finally{$brush.Dispose()}
        }
        for($i=0;$i -lt $views.Count;$i++){
            $y=82+($tileHeight+26)*$i
            $g.DrawString($captions[$i],$small,$textColor,27,$y)
            for($j=0;$j -lt $modes.Count;$j++){
                DrawShot $g $modes[$j] $views[$i] (25+$tileWidth*$j) ($y+20) ($tileWidth-4) $tileHeight
            }
        }
        $dest=Join-Path $PSScriptRoot $name
        $fmt=if($name.EndsWith('.gif')){[Drawing.Imaging.ImageFormat]::Gif}else{[Drawing.Imaging.ImageFormat]::Png}
        $bmp.Save($dest,$fmt)
    }finally{$g.Dispose();$bmp.Dispose()}
}

$reopen=Get-Content -LiteralPath reopen-verification.json -Raw | ConvertFrom-Json
$peak=[int]$reopen.rodGuideApexFrame
Board 'r0506-head-comparison.png' "Aevrynd r0506   |   Frame $peak" @('front','oblique','profile') @('Front','Three-quarter','Profile')
Board 'r0506-body-comparison.png' "Aevrynd r0506   |   Frame $peak" @('rear','crown','full') @('Rear','Crown','Whole character') 346 360
if($StaticOnly){exit}
$motion=Get-Content -LiteralPath preview-receipt.json -Raw | ConvertFrom-Json
$timeline=@($motion.motionFrames)
Board 'r0506-motion-comparison.png' 'Aevrynd r0506   |   Turn, brake and settle' @(('f{0:00}' -f 5),('f{0:00}' -f $peak),'f12','f17','f37') @('05   Turn',('{0:00}   Maximum guide displacement' -f $peak),'12   Stop','17   Rebound','37   Hold') 300 286
$frameDirectory=Join-Path $PSScriptRoot 'gif-frames'
New-Item -ItemType Directory -Path $frameDirectory -Force | Out-Null
foreach($frame in $timeline){
    $view='f{0:00}' -f $frame
    Board "gif-frames/$view.gif" 'Aevrynd r0506   |   Head turn' @($view) @("Frame $frame   /   $($timeline[-1])") 280 260
}

