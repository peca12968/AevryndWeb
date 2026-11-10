$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$r=$PSScriptRoot
$canvas=[Drawing.Bitmap]::new(1384,1076)
$g=[Drawing.Graphics]::FromImage($canvas)
$g.Clear([Drawing.Color]::FromArgb(21,24,28))
$g.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$white=[Drawing.Brushes]::WhiteSmoke
$muted=[Drawing.Brushes]::LightSteelBlue
$title=[Drawing.Font]::new('Segoe UI',24)
$label=[Drawing.Font]::new('Segoe UI',16)
$small=[Drawing.Font]::new('Segoe UI',13)
$g.DrawString('r483 | Graduated cut and diagonal crown flow',$title,$white,20,12)
$g.DrawString('Same camera, lights, keratin shader and neutral skin fixture. Both candidates rejected.',$small,$muted,20,58)
$tags=@('base','A','B')
$labels=@('r482 B | Control','A | Graduated rear layers','B | Layers + diagonal flow')
$views=@('posterior-detail','rear-oblique')
for($i=0;$i -lt 3;$i++){
 $x=20+458*$i
 $g.DrawString($labels[$i],$label,$white,$x,92)
 for($j=0;$j -lt 2;$j++){
  $image=[Drawing.Image]::FromFile((Join-Path $r "$($tags[$i])-$($views[$j]).png"))
  $g.DrawImage($image,[Drawing.Rectangle]::new($x,(127+443*$j),430,430))
  $image.Dispose()
 }
}
$g.DrawString('No accepted appearance gain. Rebuilt lengths have no collision or motion certification.',$small,$muted,20,1023)
$g.DrawString('This study omits eyes, rig, clothing and engine runtime. No score or production asset changed.',$small,$muted,20,1047)
$output=Join-Path $r 'r0483-comparison.png'
if(Test-Path -LiteralPath $output){throw 'Comparison exists'}
$canvas.Save($output,[Drawing.Imaging.ImageFormat]::Png)
$g.Dispose();$canvas.Dispose();$title.Dispose();$label.Dispose();$small.Dispose()
Get-Item -LiteralPath $output | Select-Object FullName,Length
