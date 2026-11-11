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
    $tags=@('control','graded','layered')
    $names=@('r504 B | Rest control','r505 A | Graded ends','r505 B | Layered release')
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
        $graphics.DrawString('Same native hair carrier. Turn view uses calibrated head-bone attachment.',$note,[Drawing.Brushes]::LightSteelBlue,16,$canvas.Height-44)
        $output=Join-Path $PSScriptRoot $File
        if(Test-Path -LiteralPath $output){throw "Already rendered $output"}
        $canvas.Save($output,[Drawing.Imaging.ImageFormat]::Png)
    }finally{
        $note.Dispose();$label.Dispose();$heading.Dispose();$graphics.Dispose();$canvas.Dispose()
    }
}
if($Early){
    New-Board @('rear','opposite') 'r505 | Ear-to-nape release' 'r0505-join-comparison.png'
}else{
    New-Board @('front','oblique') 'r505 | Front and three-quarter silhouette' 'r0505-head-comparison.png'
    New-Board @('profile','crown') 'r505 | Profile and crown' 'r0505-profile-comparison.png'
    New-Board @('turn','full-body') 'r505 | Held head turn and complete woman' 'r0505-body-comparison.png'
}
