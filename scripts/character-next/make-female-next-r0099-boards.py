"""Actual complete character views, with failed constructions kept visible."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0099-continuous-head-neck';OLD=E.parent/'r0098-whole-head-foundation';font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
def board(name,columns,views,footer):
 out=Image.new('RGB',(640*len(columns),48+640*len(views)+66),(18,18,18));d=ImageDraw.Draw(out)
 for i,(label,path) in enumerate(columns):
  d.text((i*640+12,12),label,font=font,fill='white')
  for j,view in enumerate(views):
   im=Image.open(path(view)).convert('RGB');assert im.size==(640,640);out.paste(im,(640*i,48+640*j))
 d.text((12,out.height-48),footer,font=font,fill='white');out.save(E/name)
def main():
 base=lambda view:OLD/('matched-b-native-head-'+view+'.png')
 a=lambda view:E/('matched-a2-material-repair-'+view+'.png')
 b=lambda view:E/('matched-b-anatomical-neck-'+view+'.png')
 c=lambda view:E/('matched-c-continuous-artist-'+view+'.png')
 retained=lambda view:E.parent/'r0097-scalp-ear-authored-controls'/('matched-neutral-bound-reference-'+view+'.png')
 board('r0099-all-constructions.png',[('r97 retained neutral - unaccepted',retained),('r98 input - rejected neck',base),('r99 A repaired materials - neck fails',a),('r99 B rebuilt annulus - folds fail',b),('r99 C continuous artist body',c)],['face','profile','body-face'],'Same views/light/exposure. Includes retained r97 to avoid comparing only against introduced defects. Full acceptance pending.')
 board('r0099-head-and-body-ab.png',[('r97 retained neutral - unaccepted',retained),('r99 C continuous source - unaccepted',c)],['face','body-face'],'Compare retained working reference too. C changes body shape; its wide/dead-eyed appearance still fails. No complete adoption.')
 board('r0099-head-and-body-source-ab.png',[('r98 direct input - rejected neck',base),('r99 C continuous source - unaccepted',c)],['face','body-face'],'Neck repair relative to failed r98 input is a retained local gain, not automatic complete-character realism improvement.')
 out=Image.new('RGB',(960,208),(18,18,18));d=ImageDraw.Draw(out)
 for i,(label,path) in enumerate([('r98 actual neck',base('face')),('r99 C actual neck',c('face'))]):
  im=Image.open(path).convert('RGB');out.paste(im.crop((80,400,560,560)),(480*i,48));d.text((480*i+10,12),label,font=font,fill='white')
 out.save(E/'r0099-neck-detail-ab.png')
 if (E/'delivered-control-02.png').exists():
  board('r0099-second-light-ab.png',[('r99 A2 welded collar - fails',lambda view:E/'matched-a2-second-light-oblique.png'),('r99 C continuous source - unaccepted',lambda view:E/'matched-c-second-light-oblique.png')],['oblique'],'Paired second illumination. Local neck construction comparison; complete appearance/contact/runtime remain unaccepted.')
  frames=[];small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',12)
  states=[('neutral','affected-motion-00.png'),('head yaw12deg','affected-motion-01.png'),('evaluated blink1 - incomplete closure','delivered-control-01.png'),('evaluated jaw.35 - unaccepted','delivered-control-02.png'),('neutral restore','affected-motion-04.png')]
  for label,name in states:
   im=Image.open(E/name).convert('RGB');assert im.size==(320,320);frame=Image.new('RGB',(320,368),(18,18,18));frame.paste(im,(0,48));draw=ImageDraw.Draw(frame);draw.text((7,5),'r99 C sampled control: '+label,font=small,fill='white');draw.text((7,25),'NOT natural hair physics / NO contact pass',font=small,fill='white');frames.append(frame)
  frames[0].save(E/'r0099-affected-controls-only.gif',save_all=True,append_images=frames[1:],duration=[600,850,850,850,600],loop=0,disposal=2)
 print('R99_ACTUAL_COMPLETE_BOARDS_READY')
if __name__=='__main__':main()
