"""Actual full character comparisons; diagnostics remain separately labelled."""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0105-native-head-skin-chart';B=E.parent/'r0104-native-artist-ocular-foundation';font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
def board(name,left,right,footer):
 im=Image.new('RGB',(1280,48+640*len(left)+48),(10,10,10));d=ImageDraw.Draw(im);d.text((12,12),'r104 B2 / static native-head reference',font=font,fill='white');d.text((652,12),'r105 A / native lip chart / unaccepted character',font=font,fill='white')
 for row,(a,b) in enumerate(zip(left,right)):
  for col,p in enumerate([a,b]):im.paste(Image.open(p).convert('RGB'),(col*640,48+row*640))
 d.text((12,im.height-34),footer,font=font,fill='white');im.save(E/name)
def main():
 a=json.loads((E/'a-view-controls.json').read_text());b=json.loads((B/'b2-view-controls.json').read_text());bm={x['view']:x for x in b}
 for x in a:assert {k:v for k,v in x.items() if k!='file'}=={k:v for k,v in bm[x['view']].items() if k!='file'}
 board('r0105-head-and-body-ab.png',[B/'matched-b2-native-head-material-repair-face.png',B/'matched-b2-native-head-material-repair-body-face.png'],[E/'matched-a-native-lip-chart-face.png',E/'matched-a-native-lip-chart-body-face.png'],'Local lip shading repair; geometry unchanged. Static skin/contact/runtime remain unaccepted.')
 board('r0105-profile-ab.png',[B/'matched-b2-native-head-material-repair-profile.png'],[E/'matched-a-native-lip-chart-profile.png'],'Actual profile: original native head shape, hair and body preserved.')
 board('r0105-related-lighting-ab.png',[E/'matched-baseline-related-oblique.png',E/'matched-baseline-second-lighting-face.png'],[E/'matched-a-related-oblique.png',E/'matched-a-second-lighting-face.png'],'Same declared light rotation in each column; original exposure and shader parameters unchanged.')
 print('R105_MATCHED_BOARDS_DONE')
if __name__=='__main__':main()
