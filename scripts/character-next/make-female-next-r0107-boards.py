"""Actual head/body, sampled pose motion and required r105/r106/r107 review."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0107-native-coarse-lid-cage';B=E.parent/'r0105-native-head-skin-chart';C=E.parent/'r0106-native-head-operation';font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
def image(path):return Image.open(path).convert('RGB')
def main():
 ref=json.loads((B/'a-view-controls.json').read_text('utf8'));base={r['view']:r for r in ref};rows=json.loads((E/'b-view-controls.json').read_text('utf8'))
 for row in rows[:2]:assert {k:v for k,v in row.items() if k!='file'}=={k:v for k,v in base[row['view']].items() if k!='file'}
 im=Image.new('RGB',(1280,1376),(10,10,10));d=ImageDraw.Draw(im);d.text((12,12),'r105 retained head/lip / static skin',font=font,fill='white');d.text((652,12),'r107 B / partial native lid operation / unaccepted',font=font,fill='white')
 for i,view in enumerate(['face','body-face']):im.paste(image(B/('matched-a-native-lip-chart-'+view+'.png')),(0,48+640*i));im.paste(image(E/('matched-b-pinned-lid-character-'+view+'.png')),(640,48+640*i))
 d.text((12,1342),'Neutral native head/body/lip retained. Actual lid response added; complete blink/contact/runtime unaccepted.',font=font,fill='white');im.save(E/'r0107-head-and-body-ab.png')
 im=Image.new('RGB',(1920,736),(10,10,10));d=ImageDraw.Draw(im);paths=[]
 for i,(suffix,title) in enumerate([('','neutral / blink 0'),('-half','half / blink 0.5'),('-closed','closed input 1 / closure incomplete')]):
  p=E/('matched-b-pinned-lid-character'+suffix+'-face.png');paths.append(p);d.text((i*640+12,12),title,font=font,fill='white');im.paste(image(p),(i*640,48))
 d.text((12,702),'Actual rendered slider poses. Incomplete optical occlusion; sampled sequence is not continuous natural motion.',font=font,fill='white');im.save(E/'r0107-actual-lid-poses.png');frames=[image(paths[i]) for i in [0,1,2,1,0]];frames[0].save(E/'r0107-sampled-lid-control.gif',save_all=True,append_images=frames[1:],duration=350,loop=0)
 im=Image.new('RGB',(1920,1376),(10,10,10));d=ImageDraw.Draw(im)
 versions=[('r105 retained local lip art',B,'matched-a-native-lip-chart-'),('r106 rejected native operation',C,'matched-a-native-lid-operation-'),('r107 B partial lid operation',E,'matched-b-pinned-lid-character-')]
 for col,(label,folder,prefix) in enumerate(versions):
  d.text((640*col+12,12),label,font=font,fill='white')
  for row,view in enumerate(['face','body-face']):im.paste(image(folder/(prefix+view+'.png')),(640*col,48+640*row))
 d.text((12,1342),'Whole-woman review r105/r106/r107: no adopted complete appearance gain; preserve local art and actual response only.',font=font,fill='white');im.save(E/'r0107-three-round-whole-woman.png');print('R107_ACTUAL_BOARDS_AND_SAMPLED_POSE_GIF_DONE')
if __name__=='__main__':main()
