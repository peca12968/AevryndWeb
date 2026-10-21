from pathlib import Path
import json,importlib.util,datetime
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0136-native-curve-combing';PRE=E.parent/'r0126-individual-head-foundation'
sp=importlib.util.spec_from_file_location('r136sheet',Path(__file__).with_name('finalize-female-next-r0121.py'));d=importlib.util.module_from_spec(sp);sp.loader.exec_module(d);d.E=E
def read(p):return json.loads(Path(p).read_text('utf-8'))
base={x['view']:x for x in read(PRE/'b-view-controls.json')};views=read(E/'a-view-controls.json');norm=lambda x:{k:v for k,v in x.items() if k not in ['file','capture']};assert len(views)==5 and all(norm(x)==norm(base[x['view']]) for x in views)
def image(e,t,v):return e/('matched-'+t+'-'+v+'.png')
bt='b-source-section-neck';at='a-native-combed-bob'
d.sheet('r0136-head-and-body-comparison.png',[[(image(PRE,bt,'face'),'A / r126 retained working woman'),(image(E,at,'face'),'B / r136 original native brush geometry')],[(image(PRE,bt,'body-face'),'A / actual complete working body'),(image(E,at,'body-face'),'B / same body, native groom candidate')]],'Matched camera/light/exposure; all original brush geometry retained. No natural motion/contact/runtime acceptance.')
d.sheet('r0136-profile-and-back-comparison.png',[[(image(PRE,bt,'profile'),'A / r126 working profile'),(image(E,at,'profile'),'B / actual native comb candidate')],[(image(PRE,bt,'back'),'A / r126 working back'),(image(E,at,'back'),'B / actual native comb candidate')]],'Native Add / Comb event strokes; known extra-curve side effects retained. Actual appearance must be judged.')
first=max(image(E,at,v).stat().st_mtime for v in ['face','body-face','profile','oblique','back']);result={'allFiveActualViewControlsExactlyMatchR126':True,'onlyIgnoredMetadata':['file','capture'],'actualCompleteViews':[v['file'] for v in views],'firstCompleteFiveViewUTC':datetime.datetime.fromtimestamp(first,datetime.timezone.utc).isoformat(),'actualVisualJudgmentNotMadeByThisScript':True};(E/'matched-view-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
