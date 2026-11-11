$ErrorActionPreference='Stop'
$env:TEMP=$PSScriptRoot;$env:TMP=$PSScriptRoot
Add-Type -AssemblyName System.Drawing
function New-ReviewImage([string[]]$Views,[string]$Name,[string]$Headline){
 $height=154+443*$Views.Count+56
 $canvas=[Drawing.Bitmap]::new(1384,$height);$g=[Drawing.Graphics]::FromImage($canvas)
 $g.Clear([Drawing.Color]::FromArgb(21,24,28));$g.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
 $title=[Drawing.Font]::new('Segoe UI',24);$label=[Drawing.Font]::new('Segoe UI',16);$small=[Drawing.Font]::new('Segoe UI',13)
 $g.DrawString($Headline,$title,[Drawing.Brushes]::WhiteSmoke,20,12)
 $g.DrawString('Actual same-woman skin and ocular parts. Same lights, camera, exposure, hair shader and radii.',$small,[Drawing.Brushes]::LightSteelBlue,20,58)
 $tags=@('control','A','B');$labels=@('Control | r484 B rest','A | Native spherical comb','B | Native projected comb')
 for($i=0;$i -lt 3;$i++){
  $x=20+458*$i;$g.DrawString($labels[$i],$label,[Drawing.Brushes]::WhiteSmoke,$x,92)
  for($j=0;$j -lt $Views.Count;$j++){
   $photo=[Drawing.Image]::FromFile((Join-Path $PSScriptRoot "$($tags[$i])-$($Views[$j]).png"))
   $g.DrawImage($photo,[Drawing.Rectangle]::new($x,(127+443*$j),430,430));$photo.Dispose()
  }
 }
 $g.DrawString('Both reconstructions rejected. Coarse bands, veils and irregular ends remain. No score increase.',$small,[Drawing.Brushes]::LightSteelBlue,20,($height-55))
 $g.DrawString('Neutral rest only. Collision, hair animation, clothing, engine timing and female acceptance remain unverified.',$small,[Drawing.Brushes]::LightSteelBlue,20,($height-30))
 $path=Join-Path $PSScriptRoot $Name;if(Test-Path -LiteralPath $path){throw 'Review exists'}
 $canvas.Save($path,[Drawing.Imaging.ImageFormat]::Png)
 $g.Dispose();$canvas.Dispose();$title.Dispose();$label.Dispose();$small.Dispose()
}
New-ReviewImage @('face','rear-oblique') 'r0485-head-comparison.png' 'r485 | Actual native curve sculpt studies'
New-ReviewImage @('opposite-profile','posterior-detail','full-body') 'r0485-profile-body-comparison.png' 'r485 | Native rest / profile and whole woman'
Get-ChildItem -LiteralPath $PSScriptRoot -Filter 'r0485-*comparison.png' | Select-Object Name,Length
