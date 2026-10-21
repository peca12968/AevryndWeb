"""Actual complete comparisons and sampled motion, before the adoption decision."""
from pathlib import Path
import json,importlib.util
from PIL import Image,ImageDraw,ImageFont
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0115-native-continuous-neck';PRE=E.parent/'r0113-coherent-head-foundation'
sp=importlib.util.spec_from_file_location('r115sheets',Path(__file__).with_name('finalize-female-next-r0111.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);m.E=E
img=lambda p,t,v:p/('matched-'+t+'-'+v+'.png');a='b-coherent-native-character';b='b-continuous-native-neutral'
m.sheet('r0115-head-and-body-ab.png',[[(img(PRE,a,'face'),'A / r113 B working woman'),(img(E,b,'face'),'B / r115 continuous native skin')],[(img(PRE,a,'body-face'),'A / old body and cut/loft neck'),(img(E,b,'body-face'),'B / continuous source body; rest arms changed')]],'Same camera/light/exposure/input; body foundation/rest geometry changed. No runtime or whole-contact pass.')
m.sheet('r0115-neck-profile-back-ab.png',[[(img(PRE,a,'profile'),'A / posterior tab and neck crease'),(img(E,b,'profile'),'B / original connected neck/shoulder')],[(img(PRE,a,'back'),'A / broad horizontal collar ledge'),(img(E,b,'back'),'B / collar removed; hair defects remain')]],'Whole textured woman. One native continuous surface replaces the failed cuts and interpolated collar.')
m.sheet('r0115-sampled-blink-ab.png',[[(img(PRE,a+tag,'face'),'r113 B / '+label),(img(E,b+tag,'face'),'r115 B / '+label)] for tag,label in [('-half','half'),('-closed','closed'),('-restored','restored')]],'Own native neutral/half/closed/restore retained. Sampled frames are not natural or continuous finite contact proof.')
m.sheet('r0115-matched-second-light-ab.png',[[(E/'second-light-baseline-face.png','A / r113 B, second light'),(E/'second-light-candidate-face.png','B / r115 B, same second light')]],'Identical second light, camera85mm, exposure/render settings. Native body material mapping changed.')
m.sheet('r0115-failed-basis-repair.png',[[(img(E,'a-continuous-native-woman','face'),'r115 A / wrong closed Basis at neutral0'),(img(E,b,'face'),'r115 B / original actual neutral restored')]],'Preserve failed A source/images. This is source-state repair of the same construction, not a new neck method.')
frames=[];font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
for tag,label in [('', 'neutral'),('-half','half'),('-closed','closed'),('-half','half'),('-restored','restored')]:
    out=Image.new('RGB',(640,688),(12,12,12));out.paste(Image.open(img(E,b+tag,'face')).convert('RGB'),(0,48));ImageDraw.Draw(out).text((12,12),'r115 B / '+label+' / contact unaccepted',font=font,fill='white');frames.append(out)
frames[0].save(E/'r0115-sampled-native-blink.gif',save_all=True,append_images=frames[1:],duration=[700,450,1000,450,700],loop=0)
print('R115_ACTUAL_COMPLETE_COMPARISONS_READY')
