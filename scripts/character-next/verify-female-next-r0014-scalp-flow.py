"""Independent saved-data checks, same-camera renders, and resumable static scope."""
import bpy,json,importlib.util,sys,time
import numpy as np
from pathlib import Path
spec=importlib.util.spec_from_file_location('prior',Path(__file__).with_name('verify-female-next-r0013-native-groom.py'));prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
spec=importlib.util.spec_from_file_location('flow',Path(__file__).with_name('build-female-next-r0014-scalp-flow.py'));flow=importlib.util.module_from_spec(spec);spec.loader.exec_module(flow)
S,E,solid=flow.S,flow.E,flow.solid

def original():
    state=prior.original_state();state['meshes']={k:v for k,v in state['meshes'].items() if not k.startswith('AFN14_')};return state

def strand_signature(o):
    d=o.data;radius=np.empty(len(d.points),dtype=np.float32);d.attributes['radius'].data.foreach_get('value',radius)
    import hashlib
    return {'curves':len(d.curves),'sizes':[c.points_length for c in d.curves],'radiiSha256':hashlib.sha256(radius.tobytes()).hexdigest(),'materials':[m.name for m in d.materials],'materialIndices':[a.value for a in d.attributes['material_index'].data],'parent':(o.parent.name,o.parent_type,o.parent_bone),'parentInverse':[v for row in o.matrix_parent_inverse for v in row],'basis':[v for row in o.matrix_basis for v in row]}

def main():
    clumped='--clumped' in sys.argv;prefix='c-' if clumped else '';build=json.loads((E/('c-clump-volume-build.json' if clumped else 'scalp-flow-build.json')).read_text());dest=Path(build['output']);assert flow.route.sha(dest)==build['outputSha256'];src=flow.SRC
    bpy.ops.wm.open_mainfile(filepath=str(src));before=original();sig={o.name.replace('AFN13_',''):strand_signature(o) for o in bpy.data.objects if o.type=='CURVES' and o.name.startswith('AFN13_')}
    bpy.ops.wm.open_mainfile(filepath=str(dest));after=original();checks={k:before[k]==after[k] for k in before};assert all(checks.values()),checks
    parts=sorted((o for o in bpy.data.objects if o.type=='CURVES' and o.name.startswith('AFN14_')),key=lambda o:o.name);same={o.name:strand_signature(o)==sig[o.name.replace('AFN14_','')] for o in parts};assert all(same.values()),same
    assert not bpy.data.libraries and all(i.packed_file for i in bpy.data.images if i.source=='FILE')
    output=E/(prefix+'saved-scalp-flow-verification.json');rows={}
    if '--resume' in sys.argv and output.exists():
        previous=json.loads(output.read_text());assert previous['candidateSha256']==flow.route.sha(dest) and previous['sourceSha256']==flow.route.sha(src);rows=previous['poses']
    rig=bpy.data.objects['AFN_R0005_Rig'];body=bpy.data.objects['AFN_R0008_Body'];poses=('neutral',) if '--neutral-only' in sys.argv else ('neutral','gaze-left','gaze-right','turn-left','turn-right')
    for pose in poses:
        if pose in rows:continue
        started=time.time();solid.stage.set_pose(rig,pose);V,T,tree=solid.data(body);V=np.array(V,dtype=np.float64);tri=V[np.array(T,dtype=np.int32)];body_rows={};allP=[];allR=[]
        for o in parts:
            P,rr=prior.native_paths(o);allP.extend(P);allR.extend(rr);audit=flow.route.check_paths(P,rr,tree,tri);body_rows[o.name]=audit;print('AFN14_SAVED='+json.dumps({'pose':pose,'object':o.name,'badSegments':audit['unqualifiedSegments'],'badRoots':audit['rootContainmentFailures']}),flush=True)
        extra=prior.secondary_surfaces(allP,allR,[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('AFN6_','AFN10_','AFN11_'))]);rows[pose]={'body':body_rows,'otherSurfaces':extra,'wallSeconds':time.time()-started}
        status='PASS_TESTED_STATIC_SURFACE_SCOPE' if all(r['status']=='PASS_TESTED_BODY_CAPSULES' for row in rows.values() for r in row['body'].values()) and all(r['status']=='PASS_SURFACE_SEPARATION' for row in rows.values() for r in row['otherSurfaces'].values()) else 'FAIL_OR_UNRESOLVED'
        result={'candidate':str(dest),'candidateSha256':flow.route.sha(dest),'source':str(src),'sourceSha256':flow.route.sha(src),'originalStateEquality':checks,'countsRadiiMaterialsParentingEquality':same,'poses':rows,'status':status,'scopeLimits':['Complete saved POLY capsules versus body and listed component surfaces; conservative lower bounds after 1 um allowance.','Static poses only; no wind, inertia, root deformation binding or continuous simulation.','No hair/hair self separation or runtime acceptance.'],'overallCharacterScore':None}
        output.write_text(json.dumps(result,indent=2)+'\n')
        if status!='PASS_TESTED_STATIC_SURFACE_SCOPE':break
    if '--render' in sys.argv:
        solid.stage.set_pose(rig,'neutral');solid.stage.eyes.E=E;fits=solid.stage.eyes.helper_centres();images=[solid.stage.eyes.render('c-clump-volume' if clumped else 'a-scalp-flow',v,fits,'neutral') for v in ('face','oblique','profile')];(E/(prefix+'renders.json')).write_text(json.dumps({'renders':images,'engine':bpy.context.scene.render.engine,'sameBaselineMaterialRadiiCountsLightingExposure':True},indent=2)+'\n')
    print('AFN14_SAVED_DONE',flush=True)

if __name__=='__main__':main()
