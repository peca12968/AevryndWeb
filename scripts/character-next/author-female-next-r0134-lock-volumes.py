"""Direct three-dimensional bob section authoring on current woman proportions.
These are new native closed control volumes, not converted hair cards or Eve.
"""
from pathlib import Path
import json,datetime
E=Path('D:/Download/Aevrynd/Evidence/character-female-next/r0134-volumetric-bob')
def main():
 assert not (E/'authored-lock-sections.json').exists()
 # Right front, side, ear-back, occipital and nape; mirrored with deliberately
 # different left tip turns. Start section is attached to actual scalp exits.
 profiles=[
  ('front',[[.080,-.063,1.505],[.109,-.071,1.490],[.118,-.067,1.446],[.107,-.055,1.391],[.080,-.065,1.370]],[.014,.015,.015,.013,.007],[.006,.008,.008,.007,.004]),
  ('side',[[.086,-.009,1.492],[.118,-.014,1.480],[.131,.008,1.433],[.120,.025,1.377],[.094,.005,1.362]],[.015,.018,.019,.016,.008],[.007,.010,.011,.010,.005]),
  ('ear_back',[[.078,.034,1.472],[.109,.050,1.466],[.123,.078,1.416],[.108,.080,1.370],[.083,.059,1.360]],[.014,.017,.018,.016,.008],[.007,.010,.011,.009,.005]),
  ('occipital',[[.049,.062,1.450],[.069,.092,1.448],[.080,.119,1.410],[.065,.125,1.366],[.036,.104,1.350]],[.013,.017,.018,.015,.008],[.007,.010,.011,.009,.005]),
  ('nape',[[.017,.066,1.446],[.029,.093,1.435],[.041,.116,1.394],[.024,.121,1.357],[.005,.104,1.350]],[.013,.015,.017,.015,.007],[.007,.009,.010,.008,.004])]
 rows=[]
 for side,sign in [('R',1),('L',-1)]:
  for j,(name,centers,width,depth) in enumerate(profiles):
   points=[[sign*x,y,z] for x,y,z in centers]
   if sign<0:points[-1][1]+=.004;points[-1][2]+=.005;points[-2][0]-=.002
   rows.append({'name':side+'_'+name,'side':side,'zone':j,'centersWorld':points,'halfWidthM':width,'halfDepthM':depth,'semanticExitAngle':sign*([.36,.50,.64,.79,.94][j])*3.141592653589793})
 out={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Author ten native three-dimensional bob lock section volumes and current-scalp canopy direction.','reference':'Actual complete retained r126 Angelica silhouette, cheek-side curl and ear/back turn. Original artist DarkNik / NikZava284 CC-BY4.0 credit retained; new Aevrynd section coordinates and geometry.','profiles':rows,'closedCrossSection':'Four corners per ring, five nonzero width/depth rings, closed side/cap faces. Fibres sample interior elliptical cross-section coordinates, never render the control cages as hair.','canopy':'Actual current native scalp harmonic chart, own new root sampling and surface combing to distributed side/back boundary exits. No source Eve paths, card rails or previous S-wave guide formula.','engineeringInitialChoice':'One fixed 24000 fibres x41 knots, source-native scalp root locations, 35um initial root radius with taper. Not a biological density/calibration or finite-contact proof.','scope':'Direct authoring. Complete appearance, editability, natural dynamics and contacts remain unaccepted.'}
 (E/'authored-lock-sections.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print('R134_TEN_NATIVE_THICK_LOCK_PROFILES_AUTHORED',flush=True)
if __name__=='__main__':main()
