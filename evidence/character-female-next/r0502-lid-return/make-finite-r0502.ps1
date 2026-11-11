$ErrorActionPreference='Stop'
$env:TEMP=$PSScriptRoot
$env:TMP=$PSScriptRoot
Add-Type -AssemblyName System.Drawing

$data=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'finite-face-witness.json') -Raw | ConvertFrom-Json -AsHashtable
$canvas=[Drawing.Bitmap]::new(1200,590)
$g=[Drawing.Graphics]::FromImage($canvas)
$heading=[Drawing.Font]::new('Segoe UI',23)
$label=[Drawing.Font]::new('Segoe UI',15)
$small=[Drawing.Font]::new('Segoe UI',12)
$cornea=[Drawing.Pen]::new([Drawing.Color]::FromArgb(82,201,190),2.5)
$normal=[Drawing.Pen]::new([Drawing.Color]::FromArgb(203,212,226),1.7)
$return=[Drawing.Pen]::new([Drawing.Color]::FromArgb(244,121,89),2.5)
$grid=[Drawing.Pen]::new([Drawing.Color]::FromArgb(62,76,91),1)
try {
 $g.Clear([Drawing.Color]::FromArgb(23,28,33))
 $g.SmoothingMode=[Drawing.Drawing2D.SmoothingMode]::AntiAlias
 $g.DrawString('r502 | Eye open, inner eyelid wall and cornea cross-section',$heading,[Drawing.Brushes]::WhiteSmoke,20,13)
 $g.DrawString('Frame 1, blink 0%. Each slice passes through the marked native face centre.',$small,[Drawing.Brushes]::LightSteelBlue,20,61)
 $g.DrawLine($normal,22,103,55,103)
 $g.DrawString('r500 inner wall',$small,[Drawing.Brushes]::WhiteSmoke,64,93)
 $g.DrawLine($return,238,103,271,103)
 $g.DrawString('r502 inner wall',$small,[Drawing.Brushes]::WhiteSmoke,280,93)
 $g.DrawLine($cornea,454,103,487,103)
 $g.DrawString('Cornea layer',$small,[Drawing.Brushes]::WhiteSmoke,496,93)
 $modes=@('arc','rolled')
 $labels=@('r502 A | Arc return','r502 B | Rolled return')
 for($j=0;$j -lt $modes.Count;$j++){
  $p=$data.results[$modes[$j]]
  $point=$p.witness.positionMetres
  $x0=20+$j*585
  $y0=165
  $left=$point[1]-.0085
  $top=$point[2]+.005
  $scale=31000
  $plot=[Drawing.Rectangle]::new($x0,$y0,527,310)
  $g.DrawString($labels[$j],$label,[Drawing.Brushes]::WhiteSmoke,$x0,130)
  $g.SetClip($plot)
  for($k=0;$k -lt 19;$k++){
   $g.DrawLine($grid,$x0+$k*31,$y0,$x0+$k*31,$y0+310)
   if($k -lt 11){$g.DrawLine($grid,$x0,$y0+$k*31,$x0+527,$y0+$k*31)}
  }
  $layers=[ordered]@{baselineReturn=$normal;cornea=$cornea;rebuiltReturn=$return}
  foreach($layer in $layers.GetEnumerator()){
   foreach($edge in $p[$layer.Key]){
    $a,$b=$edge
    $g.DrawLine($layer.Value,[single]($x0+($a[0]-$left)*$scale),[single]($y0+($top-$a[1])*$scale),
       [single]($x0+($b[0]-$left)*$scale),[single]($y0+($top-$b[1])*$scale))
   }
  }
  $px=[single]($x0+($point[1]-$left)*$scale)
  $py=[single]($y0+($top-$point[2])*$scale)
  $g.FillEllipse([Drawing.Brushes]::WhiteSmoke,[single]($px-4),[single]($py-4),[single]8,[single]8)
  $g.ResetClip()
  $g.DrawRectangle($grid,$plot)
  $dist=[Math]::Round($p.witness.faceCentreSignedMetres*1000,3)
  $slice=[Math]::Round($p.sectionXMetres*1000,2)
  $g.DrawString("Slice X = $slice mm. Face centre signed distance = $dist mm.",$small,[Drawing.Brushes]::LightSteelBlue,$x0,488)
 }
 $g.DrawString('Grid spacing 1 mm. Forward is left and up is vertical. White dot marks the checked face centre.',$small,[Drawing.Brushes]::LightSteelBlue,20,551)
 $canvas.Save((Join-Path $PSScriptRoot 'r0502-finite-face-comparison.png'),[Drawing.Imaging.ImageFormat]::Png)
} finally {
 $grid.Dispose()
 $return.Dispose()
 $normal.Dispose()
 $cornea.Dispose()
 $small.Dispose()
 $label.Dispose()
 $heading.Dispose()
 $g.Dispose()
 $canvas.Dispose()
}

