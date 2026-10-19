"""Actual-render boards/GIF and quantitative triangle-section diagnostic plot."""
from pathlib import Path
import json,hashlib,numpy as np,importlib.util
from PIL import Image,ImageDraw,ImageFont
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0060-ocular-assembly';PREV=E.parent/'r0059-authored-blink'
sp=importlib.util.spec_from_file_location('boards60',Path(__file__).with_name('finalize-female-next-r0057-evidence.py'));k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def main():
    clip=read(E/'b-blink-clip-renders.json');frames=[Image.open(x['path']).convert('RGB') for x in clip['frames']];assert len(frames)==48;palette=frames[0].quantize(colors=256,method=Image.Quantize.MEDIANCUT);frames=[x.quantize(palette=palette,dither=Image.Dither.FLOYDSTEINBERG) for x in frames];durations=[(round((i+1)*100/24)-round(i*100/24))*10 for i in range(48)];path=E/'b-actual-blink.gif';frames[0].save(path,save_all=True,append_images=frames[1:],duration=durations,loop=0,optimize=False,disposal=2);write(E/'b-blink-preview.json',{'file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'actualRenderedFrames':48,'durationMS':sum(durations),'scope':'Current saved3Dmodel, actual render frames. GIF256colour preview; not continuous contact or engine evidence.'})
    k.board(E/'r0060-head-body-comparison.png',[
        [(PREV/'a-neutral-face.png','r59: original static eye intersections'),(E/'b-neutral-face.png','r60 B: original outer face, rebuilt inner sockets')],
        [(PREV/'a-neutral-body-face.png','r59: same complete-body pose'),(E/'b-neutral-body-face.png','r60 B: same complete-body pose')]],
        'Actual same-camera/light/exposure renders. Local structural repair, not a new beauty score.\nSeven sampled ocular surface states pass; full self/fibre/continuous dynamics/runtime remain unaccepted.')
    k.board(E/'r0060-closed-multiangle.png',[
        [(E/'b-closed-face.png','r60 B: actual closed front'),(E/'b-closed-profile.png','r60 B: actual closed profile')],
        [(E/'b-closed-body-face.png','r60 B: actual closed full body'),(E/'b-neutral-alternate-oblique.png','r60 B: actual second-light oblique')]],
        'Native blink and facial curves retained. Eye/iris layers editable; anatomical sublayers still incomplete.\nNatural complete head hair, cloth/body rig, continuous collision and actual engine performance remain required.')
    a=read(E/'rendered-ocular-sections.json');b=read(E/'b-rendered-ocular-sections.json');assert a['planeXWorldM']==b['planeXWorldM'];C=np.array(a['centreWorldM']);im=Image.new('RGB',(1600,1520),'white');draw=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17);colors={'4':'#353535','3':'#248b46','0':'#d85a22','2':'#b4224d','7':'#1679c4'}
    for row,pose in enumerate(('neutral','closed')):
        for col,(data,label) in enumerate(((a,'Original r59'),(b,'Repaired r60 B'))):
            left=65+col*800;top=65+row*700;scale=12.;cx=left+300;cy=top+310
            draw.text((left,top-42),f'{label}: {pose}, actual rendered sagittal slice',font=font,fill='black')
            for v in range(-20,26,5):
                px=cx+v*scale;py=cy-v*scale;draw.line((px,top,px,top+600),fill='#dddddd');draw.line((left,py,left+640,py),fill='#dddddd');draw.text((px-12,top+608),str(v),font=small,fill='black')
            for role,segments in data['poses'][pose].items():
                if role not in colors:continue
                for segment in segments:
                    p=np.array(segment);q=np.column_stack((cx-(p[:,1]-C[1])*1000*scale,cy-(p[:,2]-C[2])*1000*scale));draw.line(tuple(q.ravel()),fill=colors[role],width=3)
            draw.text((left,top+642),'Forward -> (mm), vertical up = Z; identical scale and plane',font=small,fill='black')
    for i,(role,color) in enumerate(colors.items()):draw.text((65+i*300,1460),{'4':'Skin/socket lining','3':'Original eye outer shell','0':'Iris','2':'Pupil','7':'Wet/conjunctival lining'}[role],fill=color,font=small)
    im.save(E/'r0060-actual-section-comparison.png');write(E/'r0060-section-figure.json',{'sourceFiles':['rendered-ocular-sections.json','b-rendered-ocular-sections.json'],'actualEvaluatedTrianglePlaneIntersections':True,'characterRenderReplacement':False,'xPlaneWorldM':a['planeXWorldM'],'note':'Technical cross-section only, not a character beauty image or proof of global clearance by itself.'});print('R60_ACTUAL_EVIDENCE_ASSEMBLED',path.stat().st_size,flush=True)
if __name__=='__main__':main()
