param([switch]$Early)
$ErrorActionPreference='Stop'
$env:TEMP=$PSScriptRoot
$env:TMP=$PSScriptRoot
Add-Type -AssemblyName System.Drawing

function New-Board([string[]]$Views,[string]$Title,[string]$File) {
    $canvas=[Drawing.Bitmap]::new(1272,176+416*$Views.Count)
    $graphics=[Drawing.Graphics]::FromImage($canvas)
    $heading=[Drawing.Font]::new('Segoe UI',23)
    $label=[Drawing.Font]::new('Segoe UI',15)
    $note=[Drawing.Font]::new('Segoe UI',12)
    $tags=@('control','swept','returned')
    $names=@('r500 B | Working control','r504 A | Swept locks','r504 B | Returned waves')
    try {
        $graphics.Clear([Drawing.Color]::FromArgb(23,27,32))
        $graphics.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $graphics.DrawString($Title,$heading,[Drawing.Brushes]::WhiteSmoke,16,12)
        $graphics.DrawString('Same camera, material, fibre radii, light and exposure within each row.',$note,[Drawing.Brushes]::LightSteelBlue,16,55)
        for($c=0;$c -lt $tags.Count;$c++){
            $x=16+416*$c
            $graphics.DrawString($names[$c],$label,[Drawing.Brushes]::WhiteSmoke,$x,90)
            for($r=0;$r -lt $Views.Count;$r++){
                $input=Join-Path $PSScriptRoot "$($tags[$c])-$($Views[$r]).png"
                $img=[Drawing.Image]::FromFile($input)
                try{
                    $w=[Math]::Min(400,[Math]::Round(400*$img.Width/$img.Height))
                    $h=[Math]::Min(400,[Math]::Round(400*$img.Height/$img.Width))
                    $graphics.DrawImage($img,[Drawing.Rectangle]::new($x+[int]((400-$w)/2),126+416*$r,[int]$w,[int]$h))
                }finally{$img.Dispose()}
            }
        }
        $graphics.DrawString('Native Blender rest groom. The blink view exercises the facial controls.',$note,[Drawing.Brushes]::LightSteelBlue,16,$canvas.Height-44)
        $output=Join-Path $PSScriptRoot $File
        if(Test-Path -LiteralPath $output){throw "Already rendered $output"}
        $canvas.Save($output,[Drawing.Imaging.ImageFormat]::Png)
    }finally{
        $note.Dispose();$label.Dispose();$heading.Dispose();$graphics.Dispose();$canvas.Dispose()
    }
}
if($Early){
    New-Board @('front','oblique') 'r504 | Front and three-quarter silhouette' 'r0504-head-comparison.png'
    New-Board @('profile','opposite') 'r504 | Left and right temple profiles' 'r0504-profile-comparison.png'
}else{
    New-Board @('crown','rear') 'r504 | Crown and rear coverage' 'r0504-crown-comparison.png'
    New-Board @('blink','full-body') 'r504 | Blink and complete woman' 'r0504-body-comparison.png'
}

