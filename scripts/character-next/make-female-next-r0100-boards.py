"""Unaltered matched pixels: rejected native-lining art, not a beauty result."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0100-native-eyelid-assembly';OLD=E.parent/'r0099-continuous-head-neck';font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19)
def board(name,columns,views):
 im=Image.new('RGB',(640*len(columns),48+640*len(views)+48),(12,12,12));d=ImageDraw.Draw(im)
 for i,(label,folder,prefix) in enumerate(columns):
  d.text((640*i+12,12),label,font=font,fill='white')
  for j,view in enumerate(views):
   p=folder/(prefix+'-'+view+'.png');src=Image.open(p).convert('RGB');assert src.size==(640,640);im.paste(src,(640*i,48+640*j))
 d.text((12,im.height-35),'Both r100 trials rejected. No whole appearance, full operation, finite contact or runtime adoption.',font=font,fill='white');im.save(E/name)
def main():
 board('r0100-head-and-body-ab.png',[('r99 C retained / unaccepted',OLD,'matched-c-continuous-artist'),('r100 A2 / REJECTED',E,'matched-a2-native-lids')],['face','body-face'])
 board('r0100-art-trials.png',[('r99 C retained',OLD,'matched-c-continuous-artist'),('r100 A / REJECTED',E,'matched-a-native-lids'),('r100 A2 / REJECTED',E,'matched-a2-native-lids')],['face','profile','body-face'])
 board('r0100-protected-reference-ab.png',[('r97 protected reference / unaccepted',E.parent/'r0097-scalp-ear-authored-controls','matched-neutral-bound-reference'),('r100 A2 / REJECTED',E,'matched-a2-native-lids')],['face','body-face'])
 frames=[]
 for state,label in [('a2-native-lids','Neutral / rejected internal-eye shape'),('a2-native-lids-closed','Assigned blink1 / not accepted closure')]:
  im=Image.new('RGB',(640,688),(12,12,12));im.paste(Image.open(E/('matched-'+state+'-face.png')).convert('RGB'),(0,48));ImageDraw.Draw(im).text((12,12),label,font=font,fill='white');frames.append(im)
 frames[0].save(E/'r0100-rejected-blink-endpoints-only.gif',save_all=True,append_images=frames[1:],duration=[1000,1000],loop=0)
 print('R100_ACTUAL_COMPLETE_AB_AND_REJECTED_ENDPOINTS_WRITTEN')
if __name__=='__main__':main()
