"""Unretouched actual Blender comparison and clearly scoped motion frames."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0097-scalp-ear-authored-controls';E96=E.parent/'r0096-artist-bob-foundation';font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
def board(name,columns,views,footer):
 out=Image.new('RGB',(640*len(columns),48+640*len(views)+64),(18,18,18));d=ImageDraw.Draw(out)
 for i,(label,paths) in enumerate(columns):
  d.text((i*640+10,12),label,font=font,fill='white')
  for j,view in enumerate(views):
   im=Image.open(paths(view)).convert('RGB');assert im.size==(640,640);out.paste(im,(i*640,48+j*640))
 d.text((12,out.height-44),footer,font=font,fill='white');out.save(E/name)
board('r0097-complete-character-comparison.png',[
 ('r96 input - unaccepted',lambda v:E96/('matched-a-artist-Bob-'+v+'.png')),
 ('r97 A outward sculpt - rejected',lambda v:E/('matched-a-scalp-ear-'+v+'.png')),
 ('r97 B ear tuck - rejected',lambda v:E/('matched-b-ear-tuck-'+v+'.png'))],['face','profile','back','body-face'],'Actual matched renders. Both appearances rejected. No adopted complete-character improvement.')
board('r0097-neutral-binding-reference-comparison.png',[
 ('r96 artist shape - unaccepted',lambda v:E96/('matched-a-artist-Bob-'+v+'.png')),
 ('r97 neutral binding data - unaccepted',lambda v:E/('matched-neutral-bound-reference-'+v+'.png'))],['face','back','body-face'],'Retained neutral shape and binding data only; contacts, natural motion and runtime remain unaccepted.')
frames=[];small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',13)
for i,angle in enumerate([0,12,0]):
 im=Image.open(E/('root-follow-%02d.png'%i)).convert('RGB');assert im.size==(320,320);out=Image.new('RGB',(320,368),(18,18,18));out.paste(im,(0,48));d=ImageDraw.Draw(out);d.text((8,5),'Actual scalp follow: head yaw %d deg'%angle,font=small,fill='white');d.text((8,25),'NOT natural hair physics / NO contact pass',font=small,fill='white');frames.append(out)
frames[0].save(E/'r0097-scalp-follow-only.gif',save_all=True,append_images=frames[1:],duration=[650,950,650],loop=0,disposal=2)
print('R97_ACTUAL_BOARDS_AND_SCOPED_MOTION_READY')
