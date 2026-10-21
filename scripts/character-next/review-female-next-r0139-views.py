"""Actual whole-character, matched native gaze poses; no cropped component proof."""
from pathlib import Path
import json,datetime,importlib.util
from PIL import Image,ImageDraw,ImageFont
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0139-native-lid-follow';BASE=E.parent/'r0138-native-current-gaze';FONT=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
def sheet(n,rows,footer):
 im=Image.new('RGB',(640*len(rows[0]),688*len(rows)+48),'#191919');d=ImageDraw.Draw(im)
 for y,row in enumerate(rows):
  for x,(label,p) in enumerate(row):
   src=Image.open(p).convert('RGB');assert src.size==(640,640);im.paste(src,(x*640,y*688+48));d.text((x*640+10,y*688+12),label,font=FONT,fill='white')
 d.text((10,688*len(rows)+12),footer,font=FONT,fill='white');im.save(E/n)
def main():
 old=json.loads((BASE/'b-view-controls.json').read_text('utf-8'));new=json.loads((E/'a-view-controls.json').read_text('utf-8'));clean=lambda r:{k:v for k,v in r.items() if k not in ['file','capture']};assert [clean(r) for r in old]==[clean(r) for r in new]
 def row(v):return [('r138 B unaccepted baseline / '+v,BASE/('matched-b-native-socket-walls-'+v+'.png')),('r139 actual lid follow / '+v,E/('matched-a-native-lid-follow-'+v+'.png'))]
 sheet('r0139-complete-head-body-comparison.png',[row('face'),row('body-face')],'Same actual complete woman, camera/light/exposure/neutral pose; no automatic realism score gain.')
 sheet('r0139-profile-oblique-comparison.png',[row('profile'),row('oblique')],'Original raw topology/UV/materials retained; actual skin/lash/wet-line deformation now requires retest.')
 sheet('r0139-back-comparison.png',[row('back')],'Protected complete body/hairstyle unchanged, not hair dynamics or runtime qualification.')
 poses=[(1,'neutral'),(9,'yaw -20'),(25,'yaw +20'),(37,'pitch +10'),(45,'pitch -10'),(49,'return neutral')]
 sheet('r0139-gaze-comparison.png',[[('r138 '+label,BASE/('b-gaze-face-frame-%03d.png'%f)),('r139 '+label,E/('actual-lid-gaze-face-frame-%03d.png'%f))] for f,label in poses],'Actual matched sampled poses, not interpolated video or finite/continuous-contact proof.')
 first=datetime.datetime.fromtimestamp(max((E/('matched-a-native-lid-follow-'+v+'.png')).stat().st_mtime for v in ['face','body-face','profile','oblique','back']),datetime.timezone.utc).isoformat()
 (E/'matched-view-verification.json').write_text(json.dumps({'allActualFiveViewControlsExactlyMatchR138B':True,'onlyExcludedMetadata':['file','capture'],'baselineNotRerendered':True,'firstCompleteFiveViewUTC':first,'matchedActionPoseFrames':[f for f,l in poses],'actualFullHeadBodyViews':True},indent=2)+'\n',encoding='utf-8');print('R139_ACTUAL_MATCHED_COMPLETE_VIEWS_READY',first)
if __name__=='__main__':main()
