"""Matched full-character views and clearly labelled sampled blink review."""
from pathlib import Path
import json, datetime
from PIL import Image, ImageDraw, ImageFont
R=Path('D:/Download/Aevrynd'); E=R/'Evidence/character-female-next/r0144-current-skin-blink'; B=E.parent/'r0139-native-lid-follow'
FONT=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)

def sheet(name,rows,footer):
    im=Image.new('RGB',(640*len(rows[0]),688*len(rows)+48),'#191919'); d=ImageDraw.Draw(im)
    for y,row in enumerate(rows):
        for x,(label,p) in enumerate(row):
            src=Image.open(p).convert('RGB'); assert src.size==(640,640)
            im.paste(src,(x*640,y*688+48));d.text((x*640+10,y*688+12),label,font=FONT,fill='white')
    d.text((10,688*len(rows)+12),footer,font=FONT,fill='white');im.save(E/name)
    return im

def main():
    old=json.loads((B/'a-view-controls.json').read_text('utf-8')); new=json.loads((E/'a-view-controls.json').read_text('utf-8'))
    clean=lambda r:{k:v for k,v in r.items() if k not in ['file','capture']}
    assert [clean(r) for r in old]==[clean(r) for r in new]
    def row(v):return [('r139 working baseline / '+v,B/('matched-a-native-lid-follow-'+v+'.png')),('r144 pending native blink / '+v,E/('matched-a-current-skin-blink-'+v+'.png'))]
    sheet('r0144-complete-head-body-comparison.png',[row('face'),row('body-face')],'Same camera/light/exposure/neutral pose; no neutral appearance adoption implied.')
    sheet('r0144-profile-back-comparison.png',[row('profile'),row('back')],'Original hairstyle and body retained; natural hair and complete avatar remain unaccepted.')
    sheet('r0144-oblique-comparison.png',[row('oblique')],'Actual full head. Current eyelid construction requires independent function/contact judgment.')
    frames=[(1,'open'),(5,'half'),(9,'closed'),(13,'half'),(17,'restored')]
    def file(f,v):return E/('matched-a-current-skin-blink-'+v+'.png') if f==1 else E/('matched-blink-%03d-'%f+v+'.png')
    sheet('r0144-actual-blink-key-poses.png',[[('f%02d '%f+label+' / '+v,file(f,v)) for f,label in frames] for v in ['face','body-face']],'Five actual rendered key poses. No interpolated frames, natural timing or collision pass implied.')
    motion=[]
    for f,label in frames:
        im=Image.new('RGB',(1280,736),'#191919');d=ImageDraw.Draw(im)
        for col,v in enumerate(['face','body-face']):im.paste(Image.open(file(f,v)).convert('RGB'),(col*640,48))
        d.text((10,12),'r144 pending blink / actual frame %02d / '%f+label,font=FONT,fill='white')
        d.text((10,704),'Five sampled poses, slowed review; not natural timing or contact acceptance.',font=FONT,fill='white');motion.append(im)
    motion[0].save(E/'r0144-sampled-blink-review.gif',save_all=True,append_images=motion[1:],duration=450,loop=0,optimize=False)
    controls=json.loads((E/'actual-blink-motion-controls.json').read_text('utf-8'))
    assert all(r['actualBlink']=={'L':{5:.5,9:1.,13:.5,17:0.}[r['frame']],'R':{5:.5,9:1.,13:.5,17:0.}[r['frame']]} for r in controls)
    final=max((E/('matched-a-current-skin-blink-'+v+'.png')).stat().st_mtime for v in ['face','body-face','profile','oblique','back'])
    (E/'matched-view-verification.json').write_text(json.dumps({'allFiveNeutralViewControlsExactlyMatchWorkingR139':True,'onlyExcludedMetadata':['file','capture'],'baselineNotRerendered':True,'firstCompleteFiveViewUTC':datetime.datetime.fromtimestamp(final,datetime.timezone.utc).isoformat(),'actualMotionKeyframes':[f for f,l in frames],'gifOnlyActualSampledPosesNoFabricatedIntermediateFrames':True,'naturalTimingOrContactAccepted':False},indent=2)+'\n',encoding='utf-8')
    print('R144_ACTUAL_MATCHED_COMPLETE_HEAD_BODY_AND_SAMPLED_BLINK_REVIEW_READY')
if __name__=='__main__':main()
