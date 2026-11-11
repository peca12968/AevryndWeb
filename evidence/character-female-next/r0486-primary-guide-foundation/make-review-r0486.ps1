$ErrorActionPreference='Stop'
$env:TEMP=$PSScriptRoot;$env:TMP=$PSScriptRoot
Add-Type -AssemblyName System.Drawing
function New-Review([string[]]$Views,[string]$Name,[string]$Title){
 $h=140+443*$Views.Count+68
 $b=[Drawing.Bitmap]::new(934,$h);$g=[Drawing.Graphics]::FromImage($b)
 $g.Clear([Drawing.Color]::FromArgb(21,24,28));$g.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
 $f=[Drawing.Font]::new('Segoe UI',21);$l=[Drawing.Font]::new('Segoe UI',14);$s=[Drawing.Font]::new('Segoe UI',12)
 $g.DrawString($Title,$f,[Drawing.Brushes]::WhiteSmoke,20,12)
 $g.DrawString('Same woman, camera, lights, exposure, shader, radii and render carrier.',$s,[Drawing.Brushes]::LightSteelBlue,20,52)
 $tags=@('control','candidate');$labels=@('Control | r485 native B','r486 | 126 primary guides (unaccepted)')
 for($i=0;$i -lt 2;$i++){
  $x=20+464*$i;$g.DrawString($labels[$i],$l,[Drawing.Brushes]::WhiteSmoke,$x,91)
  for($j=0;$j -lt $Views.Count;$j++){
   $photo=[Drawing.Image]::FromFile((Join-Path $PSScriptRoot "$($tags[$i])-$($Views[$j]).png"))
   $g.DrawImage($photo,[Drawing.Rectangle]::new($x,(127+443*$j),430,430));$photo.Dispose()
  }
 }
 $g.DrawString('Appearance study only. No score increase or character adoption.',$s,[Drawing.Brushes]::LightSteelBlue,20,($h-58))
 $g.DrawString('Finite collision, hair dynamics, clothing and engine performance remain unverified.',$s,[Drawing.Brushes]::LightSteelBlue,20,($h-32))
 $p=Join-Path $PSScriptRoot $Name;if(Test-Path -LiteralPath $p){throw 'Review already exists'}
 $b.Save($p,[Drawing.Imaging.ImageFormat]::Png);$g.Dispose();$b.Dispose();$f.Dispose();$l.Dispose();$s.Dispose()
}
New-Review @('face','rear-oblique') 'r0486-head-comparison.png' 'r486 | New scalp-region guide foundation'
New-Review @('opposite-profile','posterior-detail','full-body') 'r0486-profile-body-comparison.png' 'r486 | Profile, posterior detail and whole woman'
