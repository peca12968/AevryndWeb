"""Matched complete A/B and actual150/151/152 window, original renders only."""
from pathlib import Path
import json,datetime,hashlib
from PIL import Image,ImageDraw,ImageFont
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0152-layered-groom';B=E.parent/'r0139-native-lid-follow';F=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
def sheet(name,cols,views):
 w=400;h=434;im=Image.new('RGB',(w*len(cols),h*len(views)+32),'#191919');d=ImageDraw.Draw(im)
 for y,v in enumerate(views):
  for x,(label,p,prefix) in enumerate(cols):
   src=Image.open(p/(prefix+v+'.png')).convert('RGB');assert src.size==(640,640);im.paste(src.resize((400,400),Image.Resampling.LANCZOS),(w*x,h*y+30));d.text((w*x+5,h*y+7),label+' / '+v,font=F,fill='white')
 d.text((5,h*len(views)+7),'Existing actual renders, matched controls. Original640px files retained; no appearance adoption.',font=F,fill='white');im.save(E/name)
def main():
 clean=lambda r:{k:v for k,v in r.items() if k not in ['file','capture']};old=json.loads((B/'a-view-controls.json').read_text());a=json.loads((E/'a-view-controls.json').read_text());b=json.loads((E/'b-view-controls.json').read_text());assert [clean(r) for r in old]==[clean(r) for r in a]==[clean(r) for r in b]
 cols=[('r139 working',B,'matched-a-native-lid-follow-'),('r152 A layered',E,'matched-a-layered-native-groom-'),('r152 B world frame',E,'matched-b-world-guide-frame-')]
 for n,views in [('r0152-complete-head-body-comparison.png',['face','body-face']),('r0152-profile-back-comparison.png',['profile','back']),('r0152-oblique-comparison.png',['oblique'])]:sheet(n,cols,views)
 whole=[('r150 hard-owner locks',E.parent/'r0150-authored-rooted-locks','matched-a-authored-rooted-locks-'),('r151 native neighbours',E.parent/'r0151-native-parent-groom','matched-a-native-neighbour-groom-'),('r152 A new layered',E,'matched-a-layered-native-groom-'),('r152 B frame test',E,'matched-b-world-guide-frame-')]
 for n,views in [('three-round-complete-head-body.png',['face','body-face']),('three-round-complete-profile-back.png',['profile','back'])]:sheet(n,whole,views)
 finish={tag:datetime.datetime.fromtimestamp(max((E/(prefix+v+'.png')).stat().st_mtime for v in ['face','body-face','profile','oblique','back']),datetime.timezone.utc).isoformat() for tag,prefix in [('a','matched-a-layered-native-groom-'),('b','matched-b-world-guide-frame-')]}
 (E/'matched-view-verification.json').write_text(json.dumps({'allActualViewControlsMatch139AndEachOther':True,'onlyExcludedMetadata':['file','capture'],'firstCompleteFiveViewUTC':finish['a'],'fullStateFiveViewUTC':finish,'original640pxRendersRetainedAndViewed':True,'reviewBoardsDownsampledForEvidenceBudgetNotSubstitutedGeometry':True,'baselineNotRerendered':True,'twoFullSavedStatesSameOriginalRoundNotRecounted':True,'naturalMotionContactRuntimeUnaccepted':True},indent=2)+'\n',encoding='utf-8');print('R152_MATCHED_COMPLETE_AND_ACTUAL150_151_152_BOARDS_READY')
if __name__=='__main__':main()
