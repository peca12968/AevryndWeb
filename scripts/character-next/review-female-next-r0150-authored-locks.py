"""Matched actual full-woman local-tress comparisons; no proxy improvement claims."""
from pathlib import Path
import json,datetime
from PIL import Image,ImageDraw,ImageFont
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0150-authored-rooted-locks';B=E.parent/'r0139-native-lid-follow';font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
def sheet(name,views):
 im=Image.new('RGB',(1280,688*len(views)+48),'#191919');d=ImageDraw.Draw(im)
 for y,v in enumerate(views):
  for x,(label,p) in enumerate([('r139 working / '+v,B/('matched-a-native-lid-follow-'+v+'.png')),('r150 authored locks / '+v,E/('matched-a-authored-rooted-locks-'+v+'.png'))]):
   src=Image.open(p).convert('RGB');assert src.size==(640,640);im.paste(src,(640*x,688*y+48));d.text((640*x+10,688*y+12),label,font=font,fill='white')
 d.text((10,688*len(views)+12),'Same complete woman/camera/light/exposure. Native strand count is not appearance acceptance.',font=font,fill='white');im.save(E/name)
def main():
 clean=lambda r:{k:v for k,v in r.items() if k not in ['file','capture']};old=json.loads((B/'a-view-controls.json').read_text('utf-8'));new=json.loads((E/'a-view-controls.json').read_text('utf-8'));assert [clean(r) for r in old]==[clean(r) for r in new]
 for name,views in [('r0150-complete-head-body-comparison.png',['face','body-face']),('r0150-profile-back-comparison.png',['profile','back']),('r0150-oblique-comparison.png',['oblique'])]:sheet(name,views)
 finish=max((E/('matched-a-authored-rooted-locks-'+v+'.png')).stat().st_mtime for v in ['face','body-face','profile','oblique','back'])
 (E/'matched-view-verification.json').write_text(json.dumps({'allFiveActualViewControlsExactlyMatchWorkingR139':True,'onlyExcludedMetadata':['file','capture'],'baselineNotRerendered':True,'firstCompleteFiveViewUTC':datetime.datetime.fromtimestamp(finish,datetime.timezone.utc).isoformat(),'noProxyGuideOnlyOrExternalSourceImageSubstitution':True,'motionNaturalTimingContactOrRuntimeNotAccepted':True},indent=2)+'\n',encoding='utf-8');print('R150_ACTUAL_MATCHED_COMPLETE_HEAD_BODY_PROFILE_BACK_OBLIQUE_BOARDS_READY')
if __name__=='__main__':main()
