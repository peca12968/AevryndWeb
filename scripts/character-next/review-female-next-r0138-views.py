"""Arrange actual unmodified full renders and sampled native motion frames."""
from pathlib import Path
import json,hashlib,datetime
from PIL import Image,ImageDraw,ImageFont
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0138-native-current-gaze';BASE=E.parent/'r0126-individual-head-foundation'
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
def sheet(name,rows,footer):
 im=Image.new('RGB',(640*len(rows[0]),688*len(rows)+48),'#191919');d=ImageDraw.Draw(im)
 for y,row in enumerate(rows):
  for x,(label,p) in enumerate(row):
   with Image.open(p) as src:assert src.size==(640,640);im.paste(src.convert('RGB'),(x*640,y*688+48))
   d.text((x*640+12,y*688+12),label,font=font,fill='white')
 d.text((12,688*len(rows)+12),footer,font=font,fill='white');im.save(E/name)
def signature(row):return {k:v for k,v in row.items() if k not in ['file','capture']}
def main():
 b=json.loads((BASE/'b-view-controls.json').read_text('utf-8'));a=json.loads((E/'a-view-controls.json').read_text('utf-8'));bb=json.loads((E/'b-view-controls.json').read_text('utf-8'));assert len(b)==len(a)==len(bb)==5
 assert [signature(x) for x in b]==[signature(x) for x in a]==[signature(x) for x in bb]
 def row(view):return [('r126 retained baseline / '+view,BASE/('matched-b-source-section-neck-'+view+'.png')),('r138 A native gaze / '+view,E/('matched-a-native-current-gaze-'+view+'.png')),('r138 B rebuilt sockets / '+view,E/('matched-b-native-socket-walls-'+view+'.png'))]
 sheet('r0138-complete-head-body-comparison.png',[row('face'),row('body-face')],'Actual full renders; same camera/light/exposure/pose. Static appearance gain is not implied.')
 sheet('r0138-profile-oblique-comparison.png',[row('profile'),row('oblique')],'Actual complete head/body context; new cavity topology requires independent contact checks.')
 sheet('r0138-back-comparison.png',[row('back')],'Protected hairstyle/body retained; not hair motion or runtime acceptance.')
 poses=[(1,'neutral'),(9,'yaw -20'),(25,'yaw +20'),(37,'pitch +10'),(45,'pitch -10'),(49,'return neutral')]
 sheet('r0138-native-gaze-comparison.png',[[('A '+label,E/('actual-gaze-face-frame-%03d.png'%f)) for f,label in poses[:3]],[('B '+label,E/('b-gaze-face-frame-%03d.png'%f)) for f,label in poses[:3]],[('A '+label,E/('actual-gaze-face-frame-%03d.png'%f)) for f,label in poses[3:]],[('B '+label,E/('b-gaze-face-frame-%03d.png'%f)) for f,label in poses[3:]]],'Actual sampled native action frames; no motion synthesis, continuous/contact proof or static appearance adoption.')
 frames=[]
 for r in json.loads((E/'actual-gaze-motion-controls.json').read_text('utf-8')):
  im=Image.new('RGB',(640,688),'#191919');im.paste(Image.open(r['file']).convert('RGB'),(0,48));ImageDraw.Draw(im).text((10,12),'A native gaze / frame %d / actual sampled action'%r['frame'],font=font,fill='white');frames.append(im)
 frames[0].save(E/'r0138-a-actual-gaze.gif',save_all=True,append_images=frames[1:],duration=167,loop=0)
 first={tag:datetime.datetime.fromtimestamp(max((E/('matched-'+title+'-'+v+'.png')).stat().st_mtime for v in ['face','body-face','profile','oblique','back']),datetime.timezone.utc).isoformat() for tag,title in [('a','a-native-current-gaze'),('b','b-native-socket-walls')]}
 (E/'matched-view-verification.json').write_text(json.dumps({'allActualFiveViewSetsExactlyMatchR126':True,'onlyExcludedMetadata':['file','capture'],'baselineImagesReusedUnmodified':True,'firstCompleteFiveViewUTC':first,'sampledActionImageFramesNotContinuousMotionProof':True,'previewSheetsDoNotAlterScenePixels':True},indent=2)+'\n',encoding='utf-8')
 print('R138_ACTUAL_COMPLETE_VIEW_AND_SAMPLED_MOTION_SHEETS_READY',first,flush=True)
if __name__=='__main__':main()
