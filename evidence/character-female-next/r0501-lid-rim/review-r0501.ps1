
$ErrorActionPreference='Stop'
$folder=$PWD.Path
$construction=Get-Content .\construction-receipt.json -Raw | ConvertFrom-Json -AsHashtable
$reopen=Get-Content .\reopen-verification.json -Raw | ConvertFrom-Json -AsHashtable
$preview=Get-Content .\preview-receipt.json -Raw | ConvertFrom-Json -AsHashtable
$contact=Get-Content .\facial-contact.json -Raw | ConvertFrom-Json -AsHashtable
$witness=Get-Content .\rim-witness.json -Raw | ConvertFrom-Json -AsHashtable
$failure=Get-Content .\failure-capture.json -Raw | ConvertFrom-Json -AsHashtable
function Check-Bytes($entry) {
 if((Get-FileHash -LiteralPath $entry.path -Algorithm SHA256).Hash -ne $entry.sha256){throw "Hash mismatch $($entry.path)"}
}
Check-Bytes $construction.source
Check-Bytes $construction.parent
if($preview.renders.Count -ne 20 -or $preview.baseline.Count -ne 10 -or $contact.states.Count -ne 10){throw 'Incomplete evidence'}
foreach($img in @($preview.renders.Values)+@($preview.baseline.Values)+@($failure.captures.Values)){Check-Bytes $img}
if($contact.previousReportedFrame37Pairs.rootPolygonPairs -ne 29 -or $contact.previousReportedFrame37Pairs.shaftPolygonPairs -ne 0){throw 'Witness changed'}
$env:TEMP=$folder
$env:TMP=$folder
Add-Type -AssemblyName System.Drawing
$canvas=[Drawing.Bitmap]::new(1272,385)
$g=[Drawing.Graphics]::FromImage($canvas)
$title=[Drawing.Font]::new('Segoe UI',23)
$label=[Drawing.Font]::new('Segoe UI',15)
$foot=[Drawing.Font]::new('Segoe UI',12)
$marker=[Drawing.Pen]::new([Drawing.Color]::FromArgb(224,221,67,51),2)
try{
 $g.Clear([Drawing.Color]::FromArgb(21,24,28))
 $g.SmoothingMode=[Drawing.Drawing2D.SmoothingMode]::AntiAlias
 $g.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
 $g.DrawString('r501 | Skin self-intersections at 75% blink',$title,[Drawing.Brushes]::WhiteSmoke,16,12)
 $g.DrawString('Frame 1. Same light, camera and geometry layers in all three panels.',$foot,[Drawing.Brushes]::LightSteelBlue,16,55)
 $modes=@('control','hermite','membrane')
 $labels=@('r500 B | 0 pairs','r501 A | 35 new pairs','r501 B | 2 new pairs')
 for($i=0;$i -lt $modes.Count;$i++){
  $x=16+$i*416
  $mode=$modes[$i]
  $img=[Drawing.Image]::FromFile($failure.captures[$mode].path)
  $height=[int](400*$img.Height/$img.Width)
  try{
   $g.DrawString($labels[$i],$label,[Drawing.Brushes]::WhiteSmoke,$x,91)
   $g.DrawImage($img,[Drawing.Rectangle]::new($x,126,400,$height))
   foreach($pt in $failure.captures[$mode].positionsNormalized){
    if($pt[0] -ge 0 -and $pt[0] -le 1 -and $pt[1] -ge 0 -and $pt[1] -le 1){
     $g.DrawEllipse($marker,[single]($x+400*$pt[0]-3),[single](126+$height*$pt[1]-3),[single]6,[single]6)
    }
   }
  }finally{$img.Dispose()}
 }
 $g.DrawString('Markers locate projected triangle-pair witnesses, which can be beneath the visible surface.',$foot,[Drawing.Brushes]::LightSteelBlue,16,330)
 $canvas.Save("$folder\r0501-failure-comparison.png",[Drawing.Imaging.ImageFormat]::Png)
}finally{$marker.Dispose();$foot.Dispose();$label.Dispose();$title.Dispose();$g.Dispose();$canvas.Dispose()}
$boards=[ordered]@{}
foreach($name in 'head','macro','turned','blink-body','failure'){
 $file=Get-Item -LiteralPath "r0501-$name-comparison.png"
 $boards[$name]=[ordered]@{path=$file.FullName;bytes=$file.Length;sha256=(Get-FileHash $file.FullName).Hash.ToLowerInvariant()}
}
$modes=[ordered]@{}
$frontal=[ordered]@{}
foreach($mode in 'control','hermite','membrane'){
 $frontal[$mode]=@($contact.fixedFrontalNormalSteps[$mode] | Where-Object {$_.pixel[1] -eq 342 -and $_.pixel[0] -in @(204,436)} | ForEach-Object {$_.angleDegrees})
}
foreach($mode in 'hermite','membrane'){
 $samples=@($contact.states.Values|ForEach-Object{$_[$mode]}|Where-Object{$_.skin})
 $min=[ordered]@{}
 foreach($layer in 'eye','cornea','meniscus'){
  $min[$layer]=@(foreach($state in $contact.states.GetEnumerator()){
   if($state.Value[$mode].signedSamples -and $null -ne $state.Value[$mode].signedSamples[$layer]){[ordered]@{pose=$state.Key;sample=$state.Value[$mode].signedSamples[$layer]}}
  }) | Sort-Object -Property {$_.sample.signedNearestMetres} | Select-Object -First 1
 }
 $modes[$mode]=[ordered]@{
  newSkinPairObservations=($samples|ForEach-Object{$_.skin.new.Count}|Measure-Object -Sum).Sum
  newOcularPairObservations=($samples|ForEach-Object{$_.ocular.Values}|ForEach-Object{$_.new.Count}|Measure-Object -Sum).Sum
  newExposedLashPairObservations=($samples|ForEach-Object{$_.exposed.new.Count}|Measure-Object -Sum).Sum
  newPlantedLashPairObservations=($samples|ForEach-Object{$_.planted.newCount}|Measure-Object -Sum).Sum
  reversedTriangleObservations=($samples|ForEach-Object{$_.winding.reversedTriangles}|Measure-Object -Sum).Sum
  firstWitness=$contact.states['1:0.75'][$mode].skin.new[0]
  frame1Blink075=[ordered]@{before=$contact.states['1:0.75'][$mode].skin.before;after=$contact.states['1:0.75'][$mode].skin.after}
  frame37Blink1=[ordered]@{before=$contact.states['37:1'][$mode].skin.before;after=$contact.states['37:1'][$mode].skin.after}
  minimumSignedVertexSamples=$min
 }
}
$review=[ordered]@{
 round='r0501'
 decision='REJECT_LID_RIM_KEEP_R500'
 source=$construction.source
 parent=$construction.parent
 preferredResearch='r0500 B'
 defaultVisibleVariant='hermite'
 productionAccepted=$false
 inspectedComparisonBoards=$boards
 matchedRenderedViews=10
 freshCandidateRenders=20
 failurePoseRenders=3
 visualAssessment='A slightly softens parts of the outer fold in close views but the hard closure line remains at head scale. B has even less visible improvement and part of the edge darkens. Neither provides a complete appearance gain.'
 methods='A fits anchored monotonic Hermite profiles. B minimizes second differences over the measured skin ribs. Both depth fields transport the outer envelope and adjoining return over the original skin topology, blend into tissue depth, and leave the planted rim vertices and live lash binding fixed.'
 construction=$construction.variants
 fixedLashAnchorVertices=$reopen.lashRimAnchors
 reopenedOperation=$reopen.operation
 inspectedBaselineAnchorPoses=$witness.poses.Count
 previousFrame37LashClassification=$contact.previousReportedFrame37Pairs
 contactScope=$contact.scope
 contactByVariant=$modes
 fixedFrontalNormalStepsDegrees=$frontal
 stats=$reopen.stats
 categoryReview=[ordered]@{
  anatomy='Whole body rest silhouette shown. No anatomical change evaluated.'
  face='Exterior change in the outer canthus visible in close crops, insufficient at normal head scale.'
  eyes='A introduces 40 cornea/sclera-layer polygon-pair observations. Both introduce skin self-contact at the rim band.'
  skin='Material and exposure controlled. Surface failure at closure.'
  hair='Same hair positions and apparent sheet-like clumps and gloss. Motion not evaluated.'
  clothing='Not evaluated.'
  motion='Ten held blink and head turn states. Continuous trajectory and body motion not evaluated.'
  collision='The original 29 r500 lash polygon pairs occur at the planted base. No added exposed lash pairs in this diagnostic. Both r501 skin candidates regress.'
  performance='Blender source reopened and operated. No engine measurements.'
 }
 scoreIncrease=$false
 resources=[ordered]@{
  startTaipei='2026-11-11T14:14:17+08:00';supportDeadlineTaipei='2026-11-11T14:24:17+08:00'
  firstPreviewDeadlineTaipei='2026-11-11T14:44:17+08:00';completePreviewTaipei='2026-11-11T14:22:52+08:00'
  resourceCheckpointTaipei='2026-11-11T14:59:17+08:00';workers=1;blenderThreads=4
  initialAuthorStatus='Failed before save because the evaluated Blender quad diagonals vary by pose. Probe now saves each pose tessellation and reuses only its corresponding frame.'
  probePeakPrivateBytes=1947914240;authorPeakPrivateBytes=2192769024;previewPeakPrivateBytes=3738603520;contactPeakPrivateBytes=2110328832;failureCapturePeakPrivateBytes=3414331392
  engineCPUSeconds=$null;engineGPUSeconds=$null;engineMemoryBytes=$null
 }
 nextAction='Use r500 B as the working woman. Retire projected single-axis canthus depth fitting. For the next closure construction, lay explicit upper and lower margin loops in eye-relative coordinates with their own inner return, retain the lash roots by remapping barycentric attachment, and verify finite skin and ocular intersections before rendering the full sweep. Keep the unresolved hair form as a separate visible defect.'
}
[IO.File]::WriteAllText("$folder\r0501-review.json",($review | ConvertTo-Json -Depth 13)+[char]10)
$readme=@'
# Female character r0501

Rejected offline Blender study. The working comparison remains r0500 B.

Open the Blender file and select AFN138_ACTUAL_CURRENT_GAZE_RIG. Set R501_Lid_Rim to 0 for the r500 B control, 1 for the Hermite ribs, or 2 for the membrane ribs. R448_Blink sets the held blink. The source opens on variant A with the eyes open. Frame 1 at 0.75 reproduces the new self-intersections.

Both variants use cross sections sampled from the actual skin above the upper lash rim. A fits a constrained Hermite curve. B minimizes bending across each measured section. Both transport the outer skin and adjoining return along the same depth field while preserving the existing mesh connectivity and exact live lash anchors.

The 10-state diagnostic locates 35 new skin self-intersection pairs in A and two in B at frame 1, blink 0.75. Across all 10 poses there are 68 new self-pair observations in A and 13 in B. A also introduced 40 polygon-pair observations against the cornea/sclera layer. Neither produced a sufficient visible gain.

The earlier 29 frame-37 lash/skin pairs belong to the planted root segment. The exposed shaft has zero pairs in that witness and the scoped test. No continuous clearance or engine performance was verified. The evaluation uses a pose-specific tessellation because Blender may choose different quad diagonals as the mesh deforms.

The evidence folder contains the native build and diagnostic scripts, 20 newly rendered comparison frames, three failure images and the projected witness board, and the compressed evaluated geometry bank for the probe. The older control images and prerequisite data are traceable through the r500 and inherited receipts. The inherited attribution and license notices apply.
'@
[IO.File]::WriteAllText("$folder\README-r0501.md",($readme -replace '\r','')+[char]10)
$review.contactByVariant | ConvertTo-Json -Depth 6
