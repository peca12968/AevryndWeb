"""Resolve a ray-budget exhaustion using independently measured closed-solid winding."""
import json,copy,hashlib
from pathlib import Path
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0013-envelope-hair'
p=E/'b-saved-native-groom-verification.json';old=json.loads(p.read_text());diagnosis=E/'b-root-containment-diagnosis.json';diag=json.loads(diagnosis.read_text());assert len(old['poses'])==5
assert hashlib.sha256(Path(old['candidate']).read_bytes()).hexdigest()==old['candidateSha256']
all_body=[v for row in old['poses'].values() for v in row['body'].values()];assert all(v['unqualifiedSegments']==0 for v in all_body);assert sum(v['rootContainmentFailures'] for v in all_body)==1
assert all(v['status']=='PASS_SURFACE_SEPARATION' for row in old['poses'].values() for v in row['otherSurfaces'].values())
bad=diag['rootClassificationFailures'];assert len(bad)==1;bad=bad[0];assert diag['pose']=='turn-right' and bad['object']=='AFN13_SECONDARY_CLUMPS' and bad['state']=='unresolved' and abs(bad['rootWinding'])<1e-6 and bad['nearestRootSurfaceDistanceM']>.000001 and all(x['gapLowerBoundM']>0 for x in bad['firstSegments'])
now=copy.deepcopy(old);row=now['poses']['turn-right']['body'][bad['object']];assert row['rootContainmentFailures']==1;row['rootContainmentFailures']=0;row['status']='PASS_TESTED_BODY_CAPSULES';row['float64WindingFallbacks']=[{'curve':bad['curve'],'root':bad['root'],'winding':bad['rootWinding'],'resolved':'outside'}]
now['status']='PASS_TESTED_STATIC_SURFACE_SCOPE';now['resolution']={'originalEvidence':p.name,'originalEvidenceSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'diagnosis':diagnosis.name,'diagnosisSha256':hashlib.sha256(diagnosis.read_bytes()).hexdigest(),'reason':'Original classifier returned unresolved when a ray exceeded its 80-hit budget. Independent float64 closed-solid winding at the exact anomalous root is zero; first segment has positive complete-capsule clearance. No geometry or tolerance was changed. Original FAIL evidence preserved.','fullSegmentChecksReused':True}
(E/'b-resolved-static-verification.json').write_text(json.dumps(now,indent=2)+'\n');print('AFN13_RESOLVED_STATIC_SCOPE_PASS')
