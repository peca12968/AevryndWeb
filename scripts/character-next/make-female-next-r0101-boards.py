"""Actual matched complete characters and delivered sampled controls."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0101-articulated-eyelid-topology';OLD=E.parent/'r0099-continuous-head-neck';font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19)
def board(name,columns,views,foot):
 im=Image.new('RGB',(640*len(columns),48+640*len(views)+48),(12,12,12));draw=ImageDraw.Draw(im)
 for i,(label,folder,prefix) in enumerate(columns):
  draw.text((640*i+12,12),label,font=font,fill='white')
  for j,view in enumerate(views):
   src=Image.open(folder/(prefix+'-'+view+'.png')).convert('RGB');assert src.size==(640,640);im.paste(src,(640*i,48+640*j))
 draw.text((12,im.height-35),foot,font=font,fill='white');im.save(E/name)
def main():
 board('r0101-head-and-body-ab.png',[('r99 C retained / unaccepted',OLD,'matched-c-continuous-artist'),('r101 B2 local lid direction / unaccepted',E,'matched-b2-lid-uv-and-lashes')],['face','body-face'],'Same camera, pose, lighting and exposure. Whole acceptance, continuous contacts and runtime remain pending.')
 board('r0101-three-round-character-review.png',[('r99 C: continuous body / local gain',OLD,'matched-c-continuous-artist'),('r100 A2: rejected lining',E.parent/'r0100-native-eyelid-assembly','matched-a2-native-lids'),('r101 B2: local movable-lid direction',E,'matched-b2-lid-uv-and-lashes')],['face','body-face'],'Actual r99 / r100 / r101 window. Local retained direction does not reset whole-character appearance stagnation.')
 board('r0101-protected-reference-ab.png',[('r97 supported eye reference / unaccepted',E.parent/'r0097-scalp-ear-authored-controls','matched-neutral-bound-reference'),('r101 B2: same C complete woman',E,'matched-b2-lid-uv-and-lashes')],['face','body-face'],'Compare protected good features too. C outer body shape differs from r97 and stays unchanged through r101.')
 if (E/'matched-b2-independent-reopen-profile.png').exists():board('r0101-independent-profile-ab.png',[('r99 C',OLD,'matched-c-continuous-artist'),('r101 B2 independent saved file',E,'matched-b2-independent-reopen')],['profile'],'Actual saved-file profile; no generated reference or proxy replaces the character.')
 if (E/'matched-b2-second-light-oblique.png').exists():board('r0101-second-light-ab.png',[('r99 C alternate light',OLD,'matched-c-second-light'),('r101 B2 alternate light',E,'matched-b2-second-light')],['oblique'],'Same alternate lights and exposure. This is separate from primary matched evidence.')
 frames=[]
 for i,p in enumerate(sorted(E.glob('blink-control-*.png'))):
  src=Image.open(p).convert('RGB');im=Image.new('RGB',(320,368),(12,12,12));im.paste(src,(0,48));ImageDraw.Draw(im).text((8,12),'Actual saved blink sample '+str(i),font=font,fill='white');frames.append(im)
 if len(frames)==6:frames[0].save(E/'r0101-sampled-blink-control.gif',save_all=True,append_images=frames[1:],duration=[650,100,100,100,350,650],loop=0)
 print('R101_ACTUAL_MATCHED_BOARDS',len(frames),'sampled blink frames')
if __name__=='__main__':main()
