$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
Add-Type -AssemblyName System.Drawing
$modes=@('control','open_sweep','layered_tuck')
$front=[ordered]@{}
foreach($mode in $modes){
    $name="$mode-front.png"
    $image=[Drawing.Bitmap]::new((Join-Path $PWD $name))
    try{
        $top=[int[]]::new($image.Width)
        for($x=0;$x -lt $image.Width;$x++){
            $top[$x]=-1
            for($y=0;$y -lt [int]($image.Height*.48);$y++){
                $a=$image.GetPixel($x,$y)
                $b=$image.GetPixel($x,($y+1))
                if([Math]::Max([Math]::Max($a.R,$a.G),$a.B) -ge 28 -and
                   [Math]::Max([Math]::Max($b.R,$b.G),$b.B) -ge 28){
                    $top[$x]=$y
                    break
                }
            }
        }
        $valid=@($top | Where-Object {$_ -ge 0})
        $min=[int](($valid | Measure-Object -Minimum).Minimum)
        $left=[int]($image.Width*.48)
        $strip=@($top[([int]($image.Width*.17))..([int]($image.Width*.35))] | Where-Object {$_ -ge 0})
        $maxHeightPixels=@($top[0..$left] | Where-Object {$_ -ge 0 -and $_ -le ($min+10)}).Count
        $front[$mode]=[ordered]@{
            image=$name;sha256=(Get-FileHash -LiteralPath $name -Algorithm SHA256).Hash.ToLowerInvariant()
            resolution=@($image.Width,$image.Height);minimumY=$min
            leftNearTopColumnsWithin10px=$maxHeightPixels
            leftOuterCrownMeanY=[Math]::Round(($strip | Measure-Object -Average).Average,4)
            contourY=$top
        }
    }finally{$image.Dispose()}
}
$report=[ordered]@{
    scope='Front-view silhouettes under identical camera and lighting. For each x, first two consecutive foreground pixels with any channel at least 28/255, within the upper 48% of the image. This locates the apparent crown shoulder; image silhouette is not a collision or realism test.'
    modes=$front
}
[IO.File]::WriteAllText((Join-Path $PWD 'front-silhouette.json'),($report | ConvertTo-Json -Depth 8))
foreach($mode in $modes){"$mode $($front[$mode].leftNearTopColumnsWithin10px) $($front[$mode].leftOuterCrownMeanY)"}

