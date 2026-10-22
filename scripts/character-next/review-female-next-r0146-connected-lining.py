"""Actual unchanged-source review boards; every image is a real saved render."""
from pathlib import Path
import json,datetime
from PIL import Image,ImageDraw,ImageFont
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0146-connected-palpebral-lining';B=E.parent/'r0139-native-lid-follow'
FONT=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
def sheet(name,rows,footer):
 im=Image.new('RGB',(640*len(rows[0]),688*len(rows)+48),'#191919');d=ImageDraw.Draw(im)
 for y,row in enumerate(rows):
  for x,(label,p) in enumerate(row):
   src=Image.open(p).convert('RGB');assert src.size==(640,640);im.paste(src,(640*x,688*y+48));d.text((640*x+10,688*y+12),label,font=FONT,fill='white')
 d.text((10,688*len(rows)+12),footer,font=FONT,fill='white');im.save(E/name)
def main():
 clean=lambda r:{k:v for k,v in r.items() if k not in ['file','capture']}
 old=json.loads((B/'a-view-controls.json').read_text('utf-8'));new=json.loads((E/'a-view-controls.json').read_text('utf-8'));assert [clean(r) for r in old]==[clean(r) for r in new]
 def row(v):return [('r139 working / '+v,B/('matched-a-native-lid-follow-'+v+'.png')),('r146 pending / '+v,E/('matched-a-connected-palpebral-lining-'+v+'.png'))]
 sheet('r0146-complete-head-body-comparison.png',[row('face'),row('body-face')],'Same camera/light/exposure/neutral pose. No new appearance adoption implied.')
 frames=[(1,'open'),(5,'half'),(9,'closed'),(13,'half'),(17,'restored')]
 def file(f,v):return E/('matched-a-connected-palpebral-lining-'+v+'.png') if f==1 else E/('matched-blink-%03d-'%f+v+'.png')
 sheet('r0146-actual-blink-key-poses.png',[[('f%02d '%f+label+' / '+v,file(f,v)) for f,label in frames] for v in ['face','body-face']],'Five actual rendered poses. No natural timing or contact pass implied.')
 motion=[]
 for f,label in frames:
  im=Image.new('RGB',(1280,736),'#191919');d=ImageDraw.Draw(im)
  for col,v in enumerate(['face','body-face']):im.paste(Image.open(file(f,v)).convert('RGB'),(col*640,48))
  d.text((10,12),'r146 unaccepted blink / frame %02d / '%f+label,font=FONT,fill='white');d.text((10,704),'Actual sampled poses; slowed review, not natural timing/contact acceptance.',font=FONT,fill='white');motion.append(im)
 motion[0].save(E/'r0146-sampled-blink-review.gif',save_all=True,append_images=motion[1:],duration=450,loop=0,optimize=False)
 cols=[('r144 A',E.parent/'r0144-current-skin-blink','matched-a-current-skin-blink-'),('r145 A ray fallback',E.parent/'r0145-aspherical-lid-wall','matched-a-aspherical-lid-wall-'),('r145 B native morph',E.parent/'r0145-aspherical-lid-wall','matched-b-native-lamellar-morph-'),('r146 connected lining',E,'matched-a-connected-palpebral-lining-')]
 for name,views in [('three-round-complete-head-body.png',['face','body-face']),('three-round-complete-profile-back.png',['profile','back'])]:sheet(name,[[(label+' / '+v,p/(prefix+v+'.png')) for label,p,prefix in cols] for v in views],'Actual full women, r144/r145/r146. Four saved states over three original rounds; no recount.')
 complete=max((E/('matched-a-connected-palpebral-lining-'+v+'.png')).stat().st_mtime for v in ['face','body-face','profile','oblique','back'])
 final=max(p.stat().st_mtime for p in E.glob('matched-*.png'))
 (E/'matched-view-verification.json').write_text(json.dumps({'allFiveNeutralViewControlsExactlyMatchWorkingR139':True,'onlyExcludedMetadata':['file','capture'],'baselineNotRerendered':True,'firstCompleteFiveViewUTC':datetime.datetime.fromtimestamp(complete,datetime.timezone.utc).isoformat(),'allExistingMotionPreviewCompleteUTC':datetime.datetime.fromtimestamp(final,datetime.timezone.utc).isoformat(),'actualMotionKeyframes':[f for f,l in frames],'gifOnlyActualSampledPosesNoFabricatedFrames':True,'naturalTimingOrContactAccepted':False},indent=2)+'\n',encoding='utf-8')
 print('R146_MATCHED_VIEWS_BLINK_AND_THREE_ROUND_WHOLE_REVIEW_BOARDS_READY')
if __name__=='__main__':main()
