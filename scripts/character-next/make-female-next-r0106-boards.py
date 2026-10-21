"""Show actual complete candidate separately from unsaved causal diagnostics."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0106-native-head-operation';B=E.parent/'r0105-native-head-skin-chart';font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
def main():
 a=json.loads((E/'a-view-controls.json').read_text('utf8'));b=json.loads((B/'a-view-controls.json').read_text('utf8'));bm={r['view']:r for r in b}
 for row in a[:2]:assert {k:v for k,v in row.items() if k!='file'}=={k:v for k,v in bm[row['view']].items() if k!='file'}
 im=Image.new('RGB',(1280,1376),(10,10,10));d=ImageDraw.Draw(im);d.text((12,12),'r105 working woman / retained local lip gain',font=font,fill='white');d.text((652,12),'r106 A / rejected native lid operation',font=font,fill='white')
 for i,view in enumerate(['face','body-face']):
  im.paste(Image.open(B/('matched-a-native-lip-chart-'+view+'.png')),(0,48+640*i));im.paste(Image.open(E/('matched-a-native-lid-operation-'+view+'.png')),(640,48+640*i))
 d.text((12,1342),'Neutral art/UV preserved. Actual blink input is suppressed; no complete appearance or operation gain.',font=font,fill='white');im.save(E/'r0106-head-and-body-ab.png')
 im=Image.new('RGB',(1920,736),(10,10,10));d=ImageDraw.Draw(im)
 for i,(tag,label) in enumerate([('','blink 0 / neutral'),('-half','blink 0.5 / actual skin move 0 m'),('-closed','blink 1 / actual skin move 0 m')]):
  d.text((i*640+12,12),label,font=font,fill='white');im.paste(Image.open(E/('matched-a-native-lid-operation'+tag+'-face.png')),(i*640,48))
 d.text((12,702),'Actual saved r106 A operation failure: delivered native keys change, displayed skin does not. Rejected.',font=font,fill='white');im.save(E/'r0106-actual-blink-failure.png')
 im=Image.new('RGB',(640,736),(10,10,10));d=ImageDraw.Draw(im);d.text((12,12),'UNSAVED CAUSAL TEST / modifiers disabled',font=font,fill='white');im.paste(Image.open(E/'matched-diagnostic-raw-native-closed-face.png'),(0,48));d.text((12,700),'Raw pose folds severely; rejected art, not adopted.',font=font,fill='white');im.save(E/'r0106-raw-pose-diagnostic-rejected.png');print('R106_ACTUAL_AND_DIAGNOSTIC_BOARDS_DONE')
if __name__=='__main__':main()
