"""Unretouched complete source comparisons, no generated image substitutes."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0098-whole-head-foundation';P=E.parent
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19)
def board(name,columns,views,footer):
 out=Image.new('RGB',(640*len(columns),48+640*len(views)+66),(18,18,18));d=ImageDraw.Draw(out)
 for i,(label,path) in enumerate(columns):
  d.text((i*640+12,12),label,font=font,fill='white')
  for j,view in enumerate(views):
   im=Image.open(path(view)).convert('RGB');assert im.size==(640,640);out.paste(im,(640*i,48+640*j))
 d.text((12,out.height-48),footer,font=font,fill='white');out.save(E/name)
base=lambda v:P/'r0097-scalp-ear-authored-controls'/('matched-neutral-bound-reference-'+v+'.png')
a=lambda v:E/('matched-a-whole-head-'+v+'.png')
b=lambda v:E/('matched-b-native-head-'+v+'.png')
board('r0098-complete-character-comparison.png',[('r97 neutral input - unaccepted',base),('r98 A projected head - rejected',a),('r98 B native head - rejected',b)],['face','profile','body-face'],'Actual complete renders. A face/teeth warp; B eyelid and neck failure. NO adopted complete gain.')
board('r0098-head-and-body-ab.png',[('r97 neutral input',base),('r98 B native head - unaccepted',b)],['face','body-face'],'Same views/lighting/exposure. Native source shape retained as reference only; visible neck/eye failures.')
board('r0098-three-round-whole-woman.png',[
 ('r96 artist Bob - direction only',lambda v:P/'r0096-artist-bob-foundation'/('matched-a-artist-Bob-'+v+'.png')),
 ('r97 A failed outward art',lambda v:P/'r0097-scalp-ear-authored-controls'/('matched-a-scalp-ear-'+v+'.png')),
 ('r97 B failed ear tuck',lambda v:P/'r0097-scalp-ear-authored-controls'/('matched-b-ear-tuck-'+v+'.png')),
 ('r98 A failed projected head',a),('r98 B failed native head',b)],['face','body-face'],'r96/r97/r98 includes failed trials. No complete adoption; all natural dynamics, finite contacts and runtime unaccepted.')
print('R98_ACTUAL_COMPLETE_AB_AND_THREE_ROUND_BOARD_READY')
