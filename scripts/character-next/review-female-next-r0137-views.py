"""Matched current complete views and due whole review, all five actual candidates."""
from pathlib import Path
import json,datetime,importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0137-complete-studio-groom';PRE=E.parent/'r0126-individual-head-foundation'
sp=importlib.util.spec_from_file_location('r137sheets',Path(__file__).with_name('finalize-female-next-r0121.py'));d=importlib.util.module_from_spec(sp);sp.loader.exec_module(d);d.E=E
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def img(e,t,v):return e/('matched-'+t+'-'+v+'.png')
base={r['view']:r for r in read(PRE/'b-view-controls.json')};norm=lambda x:{k:v for k,v in x.items() if k not in ['file','capture']}
for tag in ['a','b']:
 rows=read(E/(tag+'-view-controls.json'));assert len(rows)==5 and all(norm(x)==norm(base[x['view']]) for x in rows)
bt='b-source-section-neck';tag='b-native-frontal-reconstruction'
d.sheet('r0137-head-and-body-comparison.png',[[(img(PRE,bt,'face'),'A / r126 retained complete woman'),(img(E,tag,'face'),'B / r137 rebuilt front: REJECTED')],[(img(PRE,bt,'body-face'),'A / complete working body'),(img(E,tag,'body-face'),'B / no adopted complete gain')]],'Front silhouette recovered, but seam/colour/flow discontinuity and artificial back remain. Keep same complete r126.')
d.sheet('r0137-profile-and-back-comparison.png',[[(img(PRE,bt,'profile'),'A / r126 retained profile'),(img(E,tag,'profile'),'B / sharp incompatible layer seam')],[(img(PRE,bt,'back'),'A / r126 retained back'),(img(E,tag,'back'),'B / articulated source: REJECTED')]],'Current-native front is a replacement construction; it does not make whole imported hair realistic or contact accepted.')
primary=[('r135 B',E.parent/'r0135-source-shape-fibres','b-source-reflectance-fibres'),('r136',E.parent/'r0136-native-curve-combing','a-native-combed-bob'),('r137 B',E,'b-native-frontal-reconstruction')]
alternate=[('r135 A',E.parent/'r0135-source-shape-fibres','a-source-shape-fibres'),('r137 A',E,'a-complete-articulated-groom')]
for label,rounds in [('primary',primary),('alternate',alternate)]:
 d.sheet('r0137-three-round-'+label+'-head-body.png',[[(img(e,t,'face'),name+' / actual head: REJECTED') for name,e,t in rounds],[(img(e,t,'body-face'),name+' / actual complete body') for name,e,t in rounds]],'Whole review135/136/137: all five complete candidate states, zero adopted appearance/complete operation. Same r126 retained.')
 d.sheet('r0137-three-round-'+label+'-profile-back.png',[[(img(e,t,'profile'),name+' / actual profile') for name,e,t in rounds],[(img(e,t,'back'),name+' / actual back') for name,e,t in rounds]],'All actual failures included; source-only previews and startup fixes are support/attempt cost, not extra production rounds.')
first={tag:datetime.datetime.fromtimestamp(max(img(E,at,v).stat().st_mtime for v in ['face','body-face','profile','oblique','back']),datetime.timezone.utc).isoformat() for tag,at in [('a','a-complete-articulated-groom'),('b','b-native-frontal-reconstruction')]}
(E/'matched-view-verification.json').write_text(json.dumps({'bothActualFiveViewSetsExactlyMatchR126':True,'ignoredMetadataOnly':['file','capture'],'firstCompleteFiveViewUTC':first,'dueWholeReviewActualWindow':['r135','r136','r137'],'allFiveActualCandidateStatesIncluded':['r135A','r135B','r136','r137A','r137B'],'visualJudgmentStoredSeparately':True},indent=2)+'\n');print('R137_MATCHED_COMPLETE_AND_ALL_FIVE_WHOLE_REVIEW_VIEW_SETS_READY',first)
