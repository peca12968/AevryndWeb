"""Label actual unchanged Blender pixels; no generated or retouched imagery."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0096-artist-bob-foundation';E94=E.parent/'r0094-authored-growth-routing';font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
def board(name,columns,views,footer):
 w=640*len(columns);out=Image.new('RGB',(w,48+640*len(views)+64),(18,18,18));d=ImageDraw.Draw(out)
 for i,(label,paths) in enumerate(columns):
  d.text((i*640+12,12),label,font=font,fill='white')
  for j,view in enumerate(views):
   im=Image.open(paths(view)).convert('RGB');assert im.size==(640,640);out.paste(im,(i*640,48+j*640))
 d.text((12,out.height-48),footer,font=font,fill='white');out.save(E/name)
board('r0096-complete-character-comparison.png',[
 ('r94 B input - unaccepted',lambda v:E94/('matched-b-source-width-'+v+'.png')),
 ('r96 A artist Bob - direction only',lambda v:E/('matched-a-artist-Bob-'+v+'.png'))],['face','back','body-face'],'Actual matched renders. No adopted complete gain; contacts / motion / runtime unaccepted.')
board('r0096-affected-views-comparison.png',[
 ('r94 B input - unaccepted',lambda v:E/('matched-baseline-'+v+'.png')),
 ('r96 A artist Bob - unaccepted',lambda v:E/('matched-a-artist-Bob-'+v+'.png'))],['profile','second-light-oblique'],'Matched profile and second illumination. No contact or natural-motion acceptance.')
board('r0096-original-artist-source-reference.png',[
 ('Original canonical Bob: front / profile',lambda v:E/('matched-source-canonical-Bob-'+{'face':'face','back':'profile'}[v]+'.png')),
 ('Original source: back / whole body',lambda v:E/('matched-source-canonical-Bob-'+{'face':'back','back':'body-face'}[v]+'.png'))],['face','back'],'Original canonical clay-body reference only; not the target woman or a new improvement.')
print('R96_ACTUAL_PIXEL_BOARDS_READY')
