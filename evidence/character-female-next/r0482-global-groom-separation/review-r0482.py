from pathlib import Path
from runpy import run_path
import json
import numpy as np
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parent
r=run_path(str(ROOT.parent/'r0477-hair-shader-isolation'/'review-r0477.py'))
read,sha=r['read'],r['sha']
TAGS=('base','A','B');VIEWS=('posterior-detail','rear-oblique')


def main():
    source=read(ROOT/'final-source-receipt.json'); surface=read(ROOT/'surface-receipt.json'); global_proof=read(ROOT/'global-receipt.json')
    binding=read(ROOT/'binding-receipt.json'); coverage=read(ROOT/'coverage-interior-receipt.json')
    exported=read(ROOT/'portable-export-check'/'export-receipt.json')
    assert sha(source['source']['path'])==source['source']['sha256']==exported['source']['sha256']
    assert not source['externalDependencies']
    assert sha(ROOT/'binding-receipt.json')==source['bindingReceiptSha256']
    assert sha(ROOT/'surface-receipt.json')==source['surfaceReceiptSha256']
    contacts={}
    for tag in TAGS:
        mode=exported['modes'][tag]; expected=source['branches'][tag]
        assert mode['geometrySha256']==expected['positionHash'] and mode['radiusSha256']==expected['radiusHash']
        assert mode['curveIDsSha256']==expected['curveIdHash'] and mode['pointIDsSha256']==expected['pointIdHash']
        actual=read(ROOT/'portable-export-check'/tag/'rest-result.json')
        wanted=(global_proof['baseline']['NearAxis'],global_proof['baseline']['finiteOverlapWitnesses']) if tag=='base' else (surface['variants'][tag]['nearAxis'],surface['variants'][tag]['finite'])
        assert (actual['NearAxis'],actual['finiteOverlapWitnesses'])==wanted
        audit=read(ROOT/'portable-export-check'/tag/'self-contact-audit.json')
        assert audit['firstSegment']==0 and audit['syntheticTestsPassed']
        contacts[tag]=dict(nearAxis=actual['NearAxis'],finite=actual['finiteOverlapWitnesses'],minSignedWitnessMm=actual['MinSignedM']*1000.)
    with np.load(ROOT.parent/'r0481-motion-conditioned-clearance'/'root-separation-control.npz',allow_pickle=False) as f:
        roots=f['roots'].astype('f4')
    for tag in ('A','B'):
        q=np.memmap(ROOT/'portable-export-check'/tag/'rest.f32',mode='r',dtype='<f4',shape=(len(roots),80,3))
        assert np.array_equal(q[:,0],roots)
    canvas=Image.new('RGB',(1384,1090),'#15181c');draw=ImageDraw.Draw(canvas)
    fonts={size:ImageFont.truetype(r['FONT'],size) for size in (18,21,28)}
    draw.text((20,14),'r482 | Complete neutral groom separation',font=fonts[28],fill='#f2f3f5')
    draw.text((20,55),'Owned keratin shader. Shared diagnostic lights and neutral skin. Fixed cameras.',font=fonts[18],fill='#c3ccd4')
    labels=('r480 B | Control','A | Global separation, 0.45 mm cap','B | Global separation, 0.95 mm cap')
    metrics={}
    for j,view in enumerate(VIEWS):
        pictures={}
        for i,tag in enumerate(TAGS):
            entry=source['renders'][f'{tag}:{view}'];assert sha(entry['file'])==entry['sha256']
            baseline=source['renders'][f'base:{view}'];assert all(entry[k]==baseline[k] for k in ('camera','lens','exposure'))
            photo=Image.open(entry['file']).convert('RGB').crop(r['CROPS'][view]);pictures[tag]=np.asarray(photo,dtype='i2')
            x=20+458*i
            if j==0:draw.text((x,91),labels[i],font=fonts[21],fill='#f2f3f5')
            canvas.paste(photo.resize((430,430),Image.Resampling.LANCZOS),(x,122+443*j))
            if j==1:
                draw.text((x,1014),f"Near-axis {contacts[tag]['nearAxis']:,} | Radius overlaps {contacts[tag]['finite']:,}",font=fonts[18],fill='#edf2f8')
        metrics[view]={tag:float(abs(pictures[tag]-pictures['base']).mean()) for tag in ('A','B')}
    draw.text((20,1052),'Both studies remain rejected. Hair self-contact persists. This source is a neutral, unrigged study.',font=fonts[18],fill='#c3ccd4')
    image=ROOT/'r0482-global-comparison.png';canvas.save(image,optimize=True)
    record=dict(decision='REJECT_BOTH_FOR_CHARACTER_ADOPTION',
        appearance='Microscopic strand separation changes while the rounded canopy and heavy lower band remain. No complete-character appearance gain is accepted.',
        source=source,comparison=dict(file=str(image),sha256=sha(image)),cropMeanAbsRgbDelta=metrics,
        globalSeparation=global_proof,surfaceCorrection=surface,scalpBinding=binding,portableExport=exported,portableHairAudit=contacts,
        skinGapInterpretation='The positive complete-span bound already subtracts a 0.010 mm numerical guard. It certifies only this neutral mesh against the archived neutral skin.',
        scalpCoverage=coverage,rootSpacing='Final exported root positions are bit-identical to the verified r481 root-spacing control. That control and its float32 export have zero root-sphere overlaps.',
        supersededBindings='The global and surface intermediate NPZs retained triangle IDs from a different source ordering. Only bound-A/B.npz and the final credited Blender source contain bindings reconstructed on this skin mesh.',
        inheritedSourceScope='The standalone fixture includes the archived complete neutral skin and complete hair. Rig, facial shapes, eyeballs, clothing and runtime verification remain in the original character pipeline.',
        motionStatus='Not evaluated. Inherited yaw caps in the data are not certified for the rebuilt full groom.',
        strictScoreChanged=False,engineIntegrated=False,engineTiming=None,websiteChanged=False,
        historyStatus='Archive transport is recorded separately after validation. Earlier unpushed rounds are outside the r482 package.',
        schema=binding['schema'],scriptSha256={f.name:sha(f) for f in sorted(ROOT.glob('*r0482.py'))})
    with (ROOT/'r0482-review.json').open('x',encoding='utf8') as stream:json.dump(record,stream,indent=2)
    print(json.dumps({'image':str(image),'contacts':contacts,'metrics':metrics,'bytes':source['source']['bytes']},indent=2))


if __name__=='__main__':
    main()