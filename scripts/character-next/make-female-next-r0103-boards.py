"""Matched actual full-character images; no proxy or generated reference."""
from pathlib import Path
import importlib.util
from PIL import Image,ImageDraw,ImageFont
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0103-anatomical-front-lid-bands';OLD=E.parent/'r0102-facet-aware-lid-surface'
sp=importlib.util.spec_from_file_location('r103boards',Path(__file__).with_name('make-female-next-r0101-boards.py'));b=importlib.util.module_from_spec(sp);sp.loader.exec_module(b);b.E=E
def main():
 b.board('r0103-head-and-body-ab.png',[('r102 retained finite lining / unaccepted',OLD,'matched-a-facet-lining'),('r103 A front anatomy / unaccepted',E,'matched-a-anatomical-bands')],['face','body-face'],'Actual complete woman, same view/light/exposure. New bands remain unaccepted; inspect actual shape and affected contact evidence.')
 b.board('r0103-profile-ab.png',[('r102 complete source',OLD,'matched-a-facet-lining'),('r103 A',E,'matched-a-anatomical-bands')],['profile'],'Original body, grooming and exposure retained. Inspect saved-source motion/contact results separately.')
 frames=[]
 for label in ['','-half','-closed','-half','']:
  src=Image.open(E/('matched-a-anatomical-bands'+label+'-face.png')).convert('RGB');im=Image.new('RGB',(640,688),(12,12,12));im.paste(src,(0,48));ImageDraw.Draw(im).text((12,12),'Actual control sample: '+(label.strip('-') or 'neutral')+' / unaccepted',font=b.font,fill='white');frames.append(im)
 frames[0].save(E/'r0103-first-blink-samples.gif',save_all=True,append_images=frames[1:],duration=[650,200,350,200,650],loop=0)
 verified=[]
 for i,p in enumerate(sorted(E.glob('blink-control-*.png'))):
  src=Image.open(p).convert('RGB');im=Image.new('RGB',(320,368),(12,12,12));im.paste(src,(0,48));ImageDraw.Draw(im).text((8,12),'Actual saved blink sample '+str(i),font=b.font,fill='white');verified.append(im)
 if len(verified)==6:verified[0].save(E/'r0103-verified-blink-samples.gif',save_all=True,append_images=verified[1:],duration=[650,100,100,100,350,650],loop=0)
 print('R103_MATCHED_COMPLETE_BOARDS_DONE')
if __name__=='__main__':main()
