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
 $tags=@('control','A','B');$labels=@('Control | r482 B rest','A | Spatial strip paths','B | Volumetric lock sections')
 for($i=0;$i -lt 3;$i++){
  $x=20+458*$i;$g.DrawString($labels[$i],$label,[Drawing.Brushes]::WhiteSmoke,$x,92)
  for($j=0;$j -lt $Views.Count;$j++){
   $photo=[Drawing.Image]::FromFile((Join-Path $PSScriptRoot "final-$($tags[$i])-$($Views[$j]).png"))
   $g.DrawImage($photo,[Drawing.Rectangle]::new($x,(127+443*$j),430,430));$photo.Dispose()
  }
 }
 $g.DrawString('Both reconstructions rejected. Flat bands, thick curls and unnatural root flow remain. No score increase.',$small,[Drawing.Brushes]::LightSteelBlue,20,($height-55))
 $g.DrawString('Neutral rest only. Collision, hair animation, clothing, engine timing and female acceptance remain unverified.',$small,[Drawing.Brushes]::LightSteelBlue,20,($height-30))
 $path=Join-Path $PSScriptRoot $Name;if(Test-Path -LiteralPath $path){throw 'Review exists'}
 $canvas.Save($path,[Drawing.Imaging.ImageFormat]::Png)
 $g.Dispose();$canvas.Dispose();$title.Dispose();$label.Dispose();$small.Dispose()
}
New-ReviewImage @('face','rear-oblique') 'r0484-head-comparison.png' 'r484 | Complete woman / root-to-tip studies'
New-ReviewImage @('opposite-profile','posterior-detail','full-body') 'r0484-profile-body-comparison.png' 'r484 | Profile, rear and whole-woman review'
$comparisons=@()
foreach($case in @(@('control-face.png','final-control-face.png'),@('A-rear-oblique.png','final-A-rear-oblique.png'))){
 $hashes=@()
 foreach($name in $case){
  $image=[Drawing.Bitmap]::FromFile((Join-Path $PSScriptRoot $name))
  $bounds=[Drawing.Rectangle]::new(0,0,$image.Width,$image.Height)
  $lock=$image.LockBits($bounds,[Drawing.Imaging.ImageLockMode]::ReadOnly,[Drawing.Imaging.PixelFormat]::Format32bppArgb)
  $bytes=[byte[]]::new([Math]::Abs($lock.Stride)*$image.Height)
  [Runtime.InteropServices.Marshal]::Copy($lock.Scan0,$bytes,0,$bytes.Length)
  $image.UnlockBits($lock);$image.Dispose()
  $hashes+=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant()
 }
 $comparisons+=[ordered]@{files=$case;rawPixelHashes=$hashes;rawPixelsExactlyEqual=($hashes[0] -eq $hashes[1])}
}
$comparisons | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'localization-render-comparison.json') -Encoding utf8
Get-ChildItem -LiteralPath $PSScriptRoot -Filter 'r0484-*comparison.png' | Select-Object Name,Length
