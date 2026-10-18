"""Trim existing POLY prefixes and feather their radii; no new spatial route."""
import bpy, hashlib, importlib.util, json, math, sys, time
from pathlib import Path
import numpy as np
from mathutils import Vector

R=Path(r'D:\Download\Aevrynd'); S=R/'engine/assets/characters/female-next/source'
E=R/'Evidence/character-female-next/r0016-feathered-tips'; E.mkdir(parents=True,exist_ok=True)
SRC=S/'aevrynd-female-next-r0014-c-review.blend'
DST=S/'aevrynd-female-next-r0016-a-feathered-tips-study.blend'
spec=importlib.util.spec_from_file_location('v14',Path(__file__).with_name('verify-female-next-r0014-scalp-flow.py'))
v14=importlib.util.module_from_spec(spec);spec.loader.exec_module(v14)
NAMES=('PRIMARY_MASS','SECONDARY_CLUMPS','HAIRLINE_FINE','FLYAWAYS')

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,data): (E/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def arrays(o):
    p=np.empty((len(o.data.points),3),np.float32);o.data.position_data.foreach_get('vector',p.ravel())
    r=np.empty(len(p),np.float32);o.data.attributes['radius'].data.foreach_get('value',r)
    off=np.array([c.first_point_index for c in o.data.curves]+[len(p)],np.int64)
    return p,r,off
def signature(o):
    sig=v14.strand_signature(o);sig.pop('radiiSha256');return sig
def snapshot():
    result=v14.original()
    result['hairMaterialGraphs']={m.name: [(n.name,n.bl_idname,[(i.name,str(getattr(i,'default_value',None))) for i in n.inputs]) for n in m.node_tree.nodes] for m in bpy.data.materials if m.use_nodes and m.name.startswith('AFN13_')}
    return result

def build():
    start=time.time()
    prior=R/'Evidence/character-female-next/r0014-scalp-flow'
    review=json.loads((prior/'review-delivery-verification.json').read_text())
    proof=json.loads((prior/'c-saved-scalp-flow-verification.json').read_text())
    assert sha(SRC)==review['outputSha256']
    assert proof['status']=='PASS_TESTED_STATIC_SURFACE_SCOPE' and len(proof['poses'])==5
    assert sha(review['source'])==proof['candidateSha256']==review['sourceSha256']
    assert all(review['checks'].values())
    save('iteration-contract.json',{
        'previousGoalTurnClassification':'progress: v4 execution rules saved and GitHub remote verified; prompt maintenance, no model improvement claimed',
        'source':str(SRC),'sourceSha256':sha(SRC),'stage':'B_COMPLETE_HEAD_IN_PROGRESS',
        'primaryDefect':'Hard continuous bob-tip edge and a sawtooth silhouette, visible in complete-head views.',
        'hypothesis':'Coherent per-lock graduation and longer strand-radius feathering soften the bob silhouette without moving roots, changing shading or adding hair.',
        'expectedVisibleChange':'Airier, separated, graduated ends rather than one abrupt band; face and crown remain exact controls.',
        'reference':'https://www.sidefx.com/tutorials/grooming-and-rendering-realistic-hair/',
        'referenceUse':'Study guide cutting versus individual strand variation only; no copied assets/code and no Houdini dependency.',
        'rejectIf':['No discernible whole-head improvement at the same camera/light/exposure.','Tips become visibly patchy, overly wispy or staircase-like.','Any changed head, material, light, root or parent state.','Any new segment outside the exact original POLY prefix.'],
        'resourceBudget':{'threads':4,'candidates':1,'pilotPixels':700,'finalViews':3,'curves':21086,'newDynamics':False},
        'collisionScope':'Exact prefix/radius contraction inherits ONLY the five static body and component surface proofs; no self or motion acceptance.'})
    bpy.ops.wm.open_mainfile(filepath=str(SRC));before=snapshot();rows=[];kept=[]
    for li,name in enumerate(NAMES):
        o=bpy.data.objects['AFN14_'+name];P,rad,off=arrays(o);Q=P.copy();rr=rad.copy();cuts=[];changes=[]
        sig=signature(o)
        for ci,(a,b) in enumerate(zip(off[:-1],off[1:])):
            p=P[a:b].astype(np.float64);r=rad[a:b];arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
            if li==2: cuts.append(len(p)-1);changes.append(0.);continue
            root=p[0];side=0 if root[0]<0 else 16;band=int(np.clip((root[1]+.12)/.022,0,7));cid=side+band*2+int(root[2]<1.525)
            # A continuous spatial phase gives coherent locks without a random saw edge.
            coherent=.5+.5*math.sin(68*root[1]+22*abs(root[0])+cid*.21)
            individual=.5+.5*math.sin(ci*2.399963229728653+li*1.3)
            trim=(.003+.018*coherent+.004*individual)*(0.65 if li==3 else 1.)
            trim=min(trim,arc[-1]*.12)
            k=max(3,int(np.searchsorted(arc,arc[-1]-trim,side='right')-1))
            Q[a+k+1:b]=P[a+k]
            remain=np.maximum(arc[k]-arc,0)
            feather=.025+.014*coherent
            f=np.clip(remain/feather,0,1);f=f*f*(3-2*f)
            rr[a:b]=np.maximum(np.float32(1.e-8),r*(.025+.975*f)).astype(np.float32)
            # A collapsed suffix cannot be wider than the retained endpoint cap.
            rr[a+k:b]=np.minimum(rr[a+k:b],rad[a+k])
            cuts.append(k);changes.append(float(arc[-1]-arc[k]))
        o.data.position_data.foreach_set('vector',Q.ravel());o.data.attributes['radius'].data.foreach_set('value',rr)
        assert signature(o)==sig
        kept.append((o.name,P,rad,off,np.array(cuts,np.int32),Q,rr,sig))
        rows.append({'object':o.name,'curves':len(off)-1,'points':len(P),'trimmed':sum(x>0 for x in changes),'meanRemovedArcM':float(np.mean(changes)),'maxRemovedArcM':float(max(changes))})
    assert snapshot()==before
    bpy.context.scene['aevrynd_revision']='female-next-r0016-a'
    bpy.context.scene['aevrynd_release_state']='FEATHERED_TIPS_VISUAL_STUDY_NOT_RUNTIME'
    bpy.context.scene['aevrynd_groom_descriptor']='r0016 trimmed child paths; r0014 roots/guides retained; not the unmodified r0014 child cache'
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(DST));bpy.ops.wm.open_mainfile(filepath=str(DST))
    assert snapshot()==before
    cache={};checks=[]
    for name,P,rad,off,cuts,Q,rr,sig in kept:
        o=bpy.data.objects[name];actual,ar,ao=arrays(o)
        assert np.array_equal(actual,Q) and np.array_equal(ar,rr) and np.array_equal(ao,off) and signature(o)==sig
        assert np.isfinite(actual).all() and np.isfinite(ar).all() and (ar>0).all() and (ar<=rad).all()
        for ci,(a,b) in enumerate(zip(off[:-1],off[1:])):
            k=cuts[ci]
            assert np.array_equal(actual[a:a+k+1],P[a:a+k+1])
            assert np.all(actual[a+k:b]==P[a+k])
            assert float(ar[a+k:b].max())<=float(rad[a+k])
        assert np.array_equal(actual[off[:-1]],P[off[:-1]])
        key=name.removeprefix('AFN14_');cache[key+'_positions']=actual;cache[key+'_radii']=ar;cache[key+'_offsets']=ao;cache[key+'_lastRetainedPoint']=cuts
        checks.append({'object':name,'allCurvesExactOldPrefix':True,'collapsedSuffixAtExactOldCV':True,'allRadiiNonIncreasing':True,'rootPositionsUnchanged':True,'countParentMaterialsSplineTypeUnchanged':True})
    assert not bpy.data.libraries and all(i.packed_file for i in bpy.data.images if i.source=='FILE')
    np.savez_compressed(S/'aevrynd-female-next-r0016-a-hair-data.npz',**cache)
    save('saved-prefix-verification.json',{'status':'PASS_EXACT_POLY_PREFIX_RADIUS_CONTRACTION','source':str(SRC),'sourceSha256':sha(SRC),'output':str(DST),'outputSha256':sha(DST),'checks':checks,'headMaterialsLightsRigUVWeightsUnchanged':True,'referenceEvidence':{'review':{'path':str(prior/'review-delivery-verification.json'),'sha256':sha(prior/'review-delivery-verification.json')},'collision':{'path':str(prior/'c-saved-scalp-flow-verification.json'),'sha256':sha(prior/'c-saved-scalp-flow-verification.json')}},'inheritedStaticPoses':list(proof['poses']),'proof':'Each retained POLY segment is bitwise the original; shortened suffix consists only of exact original endpoint copies. Every new radius is no larger than the original; suffix caps are no larger than the original retained endpoint cap. Original capsule union therefore contains all candidate capsules under the unchanged rigid bone transform. Existing full original head/surface proof is inherited, not recomputed. No spline smoothing is introduced.','limits':['Only the five previously verified static body and optical/brow/lash surface cases.','No hair/hair self separation, movement, natural-motion calibration or runtime proof.','Root/guide authoring bindings remain r0014, but child lengths/radii require the r0016 cache; do not load the old child cache for this candidate.'],'layers':rows,'wallSeconds':time.time()-start,'fileBytes':DST.stat().st_size})
    print('R0016_BUILD_REOPEN_PREFIX_PASS',flush=True)

def render():
    base='--baseline' in sys.argv;pilot='--pilot' in sys.argv;src=SRC if base else DST
    bpy.ops.wm.open_mainfile(filepath=str(src));v14.solid.stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],'neutral')
    s=bpy.context.scene;s.render.threads_mode='FIXED';s.render.threads=4
    head=1.5624730926266572*.91
    views={'face':((0.,-.90,head+.015),(0.,-.02,head)),'oblique':((.36,-.84,head+.02),(0.,-.02,head)),'profile':((.9,-.03,head+.015),(0.,-.02,head))}
    rows=[]
    for view in (('oblique',) if pilot else ('face','oblique','profile')):
        c=s.camera;c.location,target=views[view];c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=100
        s.render.resolution_x=s.render.resolution_y=700 if pilot else 1100;s.render.resolution_percentage=100
        label=('baseline' if base else globals().get('RENDER_LABEL','candidate-a'))+('-pilot' if pilot else '')
        dest=E/f'{label}-{view}.png';s.render.filepath=str(dest);bpy.ops.render.render(write_still=True)
        rows.append({'path':str(dest),'view':view,'cameraMatrix':[x for row in c.matrix_world for x in row],'lens':c.data.lens,'resolution':[s.render.resolution_x,s.render.resolution_y],'engine':s.render.engine,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma})
    save(label+'-renders.json',{'source':str(src),'sourceSha256':sha(src),'renders':rows})
    print('R0016_RENDER_DONE',flush=True)

if __name__=='__main__':
    if '--render' in sys.argv:render()
    else:build()
