"""Changed full finite-radius hair segments and unchanged-state inheritance."""
import bpy,importlib.util,json,time,sys
from pathlib import Path
import numpy as np
spec=importlib.util.spec_from_file_location('b27',Path(__file__).with_name('build-female-next-r0027-swept-fringe.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
def main():
    report=json.loads((b.E/(b.LABEL+'-build-verification.json')).read_text(encoding='utf8'));assert b.old.base.sha(b.DST)==report['outputSha256'] and b.old.base.sha(b.CACHE)==report['cacheSha256'];bpy.ops.wm.open_mainfile(filepath=str(b.SRC));b.old.solid.stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],'neutral');control=b.old.base.snapshot();original={name:b.old.base.arrays(bpy.data.objects['AFN14_'+name]) for name in b.old.base.NAMES};signature={name:b.old.v14.strand_signature(bpy.data.objects['AFN14_'+name]) for name in b.old.base.NAMES};bpy.ops.wm.open_mainfile(filepath=str(b.DST));assert b.old.base.snapshot()==control;cache=np.load(b.CACHE);changed={tuple(row) for row in cache['changedCurves'].tolist()};parts=[bpy.data.objects['AFN14_'+name] for name in b.old.base.NAMES];inherited=[]
    for li,(name,o) in enumerate(zip(b.old.base.NAMES,parts)):
        P,R,off=b.old.base.arrays(o);OP,OR,OO=original[name];assert np.array_equal(R,OR) and np.array_equal(off,OO) and b.old.v14.strand_signature(o)==signature[name]
        untouched=[]
        for ci,(a,z) in enumerate(zip(off[:-1],off[1:])):
            if (li,ci) in changed:assert np.array_equal(P[a:a+4],OP[a:a+4])
            else:assert np.array_equal(P[a:z],OP[a:z]);untouched.append(ci)
        inherited.append({'object':o.name,'exactUnchangedCurves':len(untouched),'changedCurves':len(off)-1-len(untouched),'sourceRadiiMaterialCountsRootPrefixesExact':True})
    rows=[];rig=bpy.data.objects['AFN_R0005_Rig'];poses=('neutral',) if '--neutral-only' in sys.argv else ('neutral','gaze-left','gaze-right','turn-left','turn-right')
    for pose in poses:
        start=time.time();b.old.solid.stage.set_pose(rig,pose);V,T,tree=b.old.solid.data(bpy.data.objects['AFN_R0008_Body']);v=np.array(V,np.float64);tri=v[np.array(T)];body_rows=[];allP=[];allR=[]
        for li,o in enumerate(parts):
            paths,radii=b.old.v14.prior.native_paths(o);ids=[ci for ci in range(len(paths)) if (li,ci) in changed]
            if not ids:continue
            pp=[paths[i] for i in ids];rr=[radii[i] for i in ids];allP.extend(pp);allR.extend(rr);audit=b.old.route.check_paths(pp,rr,tree,tri);body_rows.append({'object':o.name,'curveIds':ids,'bodyCapsules':audit})
        components=b.old.v14.prior.secondary_surfaces(allP,allR,[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('AFN6_','AFN10_','AFN11_'))]);good=all(r['bodyCapsules']['status']=='PASS_TESTED_BODY_CAPSULES' for r in body_rows) and all(r['status']=='PASS_SURFACE_SEPARATION' for r in components.values());rows.append({'pose':pose,'body':body_rows,'otherComponents':components,'pass':good,'wallSeconds':time.time()-start})
        b.save(b.LABEL+'-saved-static-verification.json',{'asset':str(b.DST),'assetSha256':b.old.base.sha(b.DST),'sourceSha256':report['sourceSha256'],'exactUnchangedState':inherited,'sourceControlsExact':True,'poses':rows,'status':'PASS_CHANGED_FRINGE_TESTED_STATIC_SCOPE' if all(r['pass'] for r in rows) else 'FAIL_OR_UNRESOLVED','inheritedEvidence':'Original unchanged strands: r17 complete static capsules, r18 changed-brow evidence and r23 changed-lip region. Only exact unchanged geometries/assumptions inherited; changed fringe independently checked here.','scope':'Changed actual full POLY capsules vs body/eye/brow/lash surfaces. Listed static poses only. No hair/hair self, hair dynamics, continuous transitions or runtime acceptance.'});print('R0027_STATIC',b.LABEL,pose,'PASS',good,flush=True)
        if not good:break
    b.old.solid.stage.set_pose(rig,'neutral')
if __name__=='__main__':main()
