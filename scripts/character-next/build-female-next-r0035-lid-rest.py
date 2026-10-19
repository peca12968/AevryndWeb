"""Native upper-lid rest: topological rim handles and harmonic tissue extension.

Targets slide on the actual fixed eye exterior, preserving source front depth
gap. Native inner-wall support constraints are solved against the actual eye
vertices. No globe shrink, global angular blink field, added cover or exclusion.
"""
import bpy,importlib.util,json,time,heapq,sys
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('i35',Path(__file__).with_name('inspect-female-next-r0035-lid-rest.py'));i=importlib.util.module_from_spec(spec);spec.loader.exec_module(i)
g=i.g;b=i.b;E=i.E;S=i.S;SRC=i.SRC;FIXED_SUPPORT='--fixed-support' in sys.argv;OUT=S/('aevrynd-female-next-r0035-b-native-lid-rest.blend' if FIXED_SUPPORT else 'aevrynd-female-next-r0035-a-native-lid-rest.blend')

def save(n,x):
    if FIXED_SUPPORT:n=('b-'+n[2:]) if n.startswith('a-') else ('b-'+n if n=='round-contract.json' else n)
    i.save(n,x)
def read(n):return json.loads((E/n).read_text(encoding='utf8'))
def smooth(x):x=float(np.clip(x,0,1));return x*x*(3-2*x)

def distances(V,adj,seeds):
    d=np.full(len(V),np.inf);heap=[]
    for s in seeds:d[s]=0;heapq.heappush(heap,(0.,s))
    while heap:
        value,p=heapq.heappop(heap)
        if value!=d[p] or value>.016:continue
        for q in adj[p]:
            cand=value+float(np.linalg.norm(V[p]-V[q]))
            if cand<d[q]:d[q]=cand;heapq.heappush(heap,(cand,q))
    return d

def rest_patch(V,polys,adj,side,inspection,globe,amplitude=.00090):
    center=np.array(i.FITS[side]['centerM']);ev,et=globe;tree=i.tree(ev,et)
    boundary=inspection['native'][side]['wallBoundaryVertices'];front=[x['id'] for x in boundary if V[x['id'],1]<-.108]
    handles={};records=[]
    for vi in front:
        p=V[vi];dx=p[0]-center[0];height=p[2]-center[2];w=max(0.,1-(dx/.0125)**2)**2*smooth((height-.00025)/.00125)
        if height<=.00025 or abs(dx)>.0118:w=0.
        dz=-amplitude*w;old=tree.ray_cast(Vector((p[0],-.25,p[2])),Vector((0,1,0)),.3)[0];new=tree.ray_cast(Vector((p[0],-.25,p[2]+dz)),Vector((0,1,0)),.3)[0]
        dy=float(new.y-old.y) if w>0 and old is not None and new is not None else 0.
        handles[int(vi)]=np.array((0.,dy,dz));records.append({'vertex':int(vi),'weight':w,'delta':[0.,dy,dz],'frontEyeRayAvailable':old is not None and new is not None,'sourceDepthGapYM':float(old.y-p[1]) if old is not None else None})
    moving=[vi for vi,d in handles.items() if np.linalg.norm(d)>1e-10];assert len(moving)>3
    d=distances(V,adj,moving)
    eligible=(d<.014)&(abs(V[:,0]-center[0])<.021)&(V[:,1]<-.095)&(V[:,1]>-.147)&(V[:,2]>center[2]+.00025)&(V[:,2]<center[2]+.018)
    domain=set(np.flatnonzero(eligible).tolist())|set(front);fixed={v for v in domain if any(x not in domain for x in adj[v])};fixed|={v for v in domain if not eligible[v]};fixed-=set(moving)
    prescribed={v:np.zeros(3) for v in fixed};prescribed.update(handles)
    unknown=sorted(domain-set(prescribed));index={v:j for j,v in enumerate(unknown)};A=np.zeros((len(unknown),len(unknown)));rhs=np.zeros((len(unknown),3))
    for vi,row in index.items():
        A[row,row]=len(adj[vi])
        for n in adj[vi]:
            if n in index:A[row,index[n]]-=1
            elif n in prescribed:rhs[row]+=prescribed[n]
    solution=np.linalg.solve(A,rhs) if len(unknown) else np.empty((0,3));delta=np.zeros_like(V)
    for vi,dv in prescribed.items():delta[vi]=dv
    for vi,dv in zip(unknown,solution):delta[vi]=dv
    return delta,{'side':side,'center':center.tolist(),'amplitudeM':amplitude,'upperMovingRimHandles':moving,'allFrontRimHandles':front,'handleTargets':records,'harmonicUnknowns':unknown,'fixedBoundaryVertices':sorted(fixed),'domainVertices':sorted(domain),'method':'Actual native front inner-wall boundary handles, unchanged lower/canthus rim; actual globe front-depth slide and uniform graph-harmonic displacement extension with zero orbital-patch boundary. Not an angular blink field.'}

def apply_world(body,V):
    inverse=body.matrix_world.inverted()
    for vi,p in enumerate(V):body.data.vertices[vi].co=inverse@Vector(p.tolist())
    body.data.update();bpy.context.view_layer.update()

def support_constraints(V,desired,polys,inspection,globe_data,patches):
    region_info=json.loads((b.R/'Evidence/character-female-next/r0029-native-eye-interface/coarse-feasibility.json').read_text())['regions'];touched=np.linalg.norm(desired-V,axis=1)>1e-10;constraints={};records=[];fixed_residual=0.
    # The actual eye support planes bound whole native wall faces, rather than
    # moving an eyeball or assuming a spherical collider. Only affected faces.
    allowed=set(v for p in patches.values() for v in p['domainVertices']);fixed=set(v for p in patches.values() for v in p['fixedBoundaryVertices']);fixed|=set(v for p in patches.values() for v in p['allFrontRimHandles'] if v not in p['upperMovingRimHandles'])
    for side,(ev,et) in globe_data.items():
        center=np.array(i.FITS[side]['centerM'])
        old_planes={row['polygon']:np.array(row['normal']) for row in region_info[i.FITS[side]['name']]['planes']}
        for pi in region_info[i.FITS[side]['name']]['inwardWallFaces']:
            ids=polys[pi]
            if not touched[ids].any():continue
            n=old_planes[pi].copy() if FIXED_SUPPORT else desired[ids].mean(0)-center;n/=np.linalg.norm(n);h=float(np.max(ev@n)+.00008)
            for vi in ids:
                if vi in allowed and vi not in fixed:constraints.setdefault(vi,[]).append((n,h))
                else:
                    residual=float(h-n@desired[vi]);fixed_residual=max(fixed_residual,residual)
                    if residual>1e-6:
                        save('a-support-infeasibility.json',{'status':'INFEASIBLE_FIXED_BOUNDARY','side':side,'polygon':pi,'vertex':vi,'supportResidualM':residual,'source':str(SRC),'sourceSha256':b.sha(SRC),'normalMode':'previous-r29-fixed' if FIXED_SUPPORT else 'updated-face-direction','numericalAllowanceM':1e-6,'note':'Optimization support conflict, not a measured true-surface penetration. No geometry saved or contact gate loosened.'})
                        raise RuntimeError(('Fixed wall boundary violates new support plane',side,pi,vi,residual))
            records.append({'side':side,'polygon':pi,'normal':n.tolist(),'support':h})
    solved=desired.copy();steps=[]
    for vi,cs in constraints.items():solved[vi],iterations=g.q.project(desired[vi],cs);steps.append(iterations)
    diff=np.linalg.norm(solved-desired,axis=1);assert diff.max()<.00065,('Large contact correction, reject instead of pushing',diff.max())
    return solved,{'planes':records,'constrainedVertices':sorted(constraints),'maximumCorrectionFromRestGoalM':float(diff.max()),'maximumDykstraSweeps':max(steps,default=0),'marginM':.00008,'fixedBoundaryMaximumSupportResidualM':fixed_residual,'supportNumericalAllowanceM':1e-6,'normalMode':'previous-r29-fixed-directions/current-actual-eye-support' if FIXED_SUPPORT else 'updated-face-directions','method':'Per-vertex least correction to simultaneous incident actual-eye support halfspaces; fixed lower/canthus/outer boundary cannot move. Native/full actual surface gates still require zero intersections.'}

def main():
    start=time.time();assert b.sha(SRC)=='9f2502d4833088cf0dd625201b6e4f2727dfcf632de62f2b5dadb61ce21e6903';inspection=read('aperture-topology-inspection.json')
    save('round-contract.json',{'previousGoalTurnClassification':'progress: r34 width-fidelity correction retained and suspended fixed-exit groom rejected under two renderers; no appearance score increase','source':str(SRC),'sourceSha256':b.sha(SRC),'primaryDefect':'Neutral upper aperture exposes almost the whole iris, creating a staring eye expression','hypothesis':'A modest native upper-lid margin rest change, with natural iris occlusion and preserved actual-eye clearance, relaxes the whole-face eye expression','candidateCount':1,'target':'About0.9mm maximum native upper-rim lowering, tapering to fixed canthi/lower lid; current central aperture upper is5.08/5.20mm above eye center, not a universal face prescription','nativeMethod':'Topological front wall boundary, actual-eye front-depth preserving targets, harmonic tissue extension and actual-eye wall support constraints','smallTest':'Native-level body/8optical surface contacts and changed-region self before full Multires candidate expansion','reject':['Any unresolved coarse contact/changed self','Fixed canthus/boundary support infeasible or contact correction over0.65mm','Full sculpt contact/self regression, distorted folds, sleepy/kinked rest shape or no visible whole-head benefit'],'unchanged':'Fixed eye mesh/pose/optics, skin/UV/named fields, hair points/radii, STRIP/subdivision0, lights/exposure; not a blink/gaze/rig implementation','resources':{'threads':4,'checkpointMinutes':45,'diagnosticInitialMinutes':10,'maximumNativeRimAmplitudeM':.0009},'reference':'https://www.uclahealth.org/sites/default/files/documents/1_11_12_tajudeen_bleph_ch176.pdf','referenceUse':'Adult lid/limbus rest relationship as anatomical modeling reference; subject proportions vary, engineering target is an inference not a medical judgment.'})
    bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;b.E=E;body=bpy.data.objects[b.BODY];mod=body.modifiers[0];cfg=b.config(s);original_state={o.name:g.signature(o) for o in s.objects if o.type=='MESH' and not o.hide_render};hair=next(o for o in s.objects if o.type=='CURVES' and not o.hide_render);hpos=np.empty(len(hair.data.points)*3,dtype='f4');hair.data.position_data.foreach_get('vector',hpos);hair_hash=__import__('hashlib').sha256(hpos.tobytes()).hexdigest();assert s.render.hair_type=='STRIP' and s.render.hair_subdiv==0
    # Match the retained85mm complete-head camera throughout this round.
    original_camera=b.camera
    def camera(view):original_camera(view);s.camera.data.lens=85 if not view.startswith('body') else s.camera.data.lens
    b.camera=camera
    if '--skip-before' not in sys.argv:g.q.render('before');i.closeup('before')
    high_before,high_tri=b.evaluated(body,True);mod.levels=0;bpy.context.view_layer.update();V,T=b.evaluated(body,True);polys=[list(p.vertices) for p in body.data.polygons];adj={v:set() for v in range(len(V))}
    for e in body.data.edges:x,y=map(int,e.vertices);adj[x].add(y);adj[y].add(x)
    original_native=np.array([list(v.co) for v in body.data.vertices]);desired=V.copy();patches={};globe_data={side:i.outer(side) for side in ('L','R')}
    for side in ('L','R'):
        delta,patch=rest_patch(V,polys,adj,side,inspection,globe_data[side]);desired+=delta;patches[side]=patch
    save('a-rest-patch-targets.json',patches)
    solved,support=support_constraints(V,desired,polys,inspection,globe_data,patches);save('a-wall-support.json',support)
    # Write only actual changed native vertices, preserving every other float.
    changed=np.flatnonzero(np.linalg.norm(solved-V,axis=1)>1e-10);inverse=body.matrix_world.inverted()
    for vi in changed:body.data.vertices[int(vi)].co=inverse@Vector(solved[vi].tolist())
    body.data.update();bpy.context.view_layer.update();cv,ct=b.evaluated(body,True);full=i.tree(cv,ct);contacts={}
    for side in ('L','R'):
        for part in ('Sclera','Cornea','Iris','Pupil'):
            name=f'AFN30_{side}_{part}';v,t=b.evaluated(bpy.data.objects[name],True);pairs=full.overlap(i.tree(v,t));contacts[name]={'bodyOpticalTrianglePairs':len(pairs),'examples':[[int(x),int(y)] for x,y in pairs[:12]]}
    v29=g.module('v29r35','verify-female-next-r0029-native-eye-interface.py');coarse_changed=np.any(cv!=V,axis=1);self_report,self_pairs=v29.changed_self(cv,ct,coarse_changed,full)
    coarse_clean=not any(x['bodyOpticalTrianglePairs'] for x in contacts.values()) and self_report['nonAdjacentTrianglePairs']==0
    save('a-coarse-feasibility.json',{'status':'PASS_NATIVE_REST_CONTACT' if coarse_clean else 'REJECT_NATIVE_REST_CONTACT','contacts':contacts,'changedRegionSelf':self_report,'nativeChangedVertices':changed.tolist(),'nativeMaximumDisplacementM':float(np.linalg.norm(cv-V,axis=1).max()),'support':support,'scope':'Native cage feasibility only; not full Multires or blink/gaze proof'})
    mod.levels=mod.render_levels=mod.sculpt_levels=3;bpy.context.view_layer.update();hv,ht=b.evaluated(body,True);assert np.array_equal(ht,high_tri);high_delta=np.linalg.norm(hv-high_before,axis=1);moved=np.flatnonzero(high_delta>1e-10)
    np.savez_compressed(S/'aevrynd-female-next-r0035-a-native-lid-delta.npz',nativeBeforeLocal=original_native,nativeAfterLocal=np.array([list(v.co) for v in body.data.vertices]),changedNativeVertices=changed,changedEvaluatedVertices=moved,evaluatedDisplacement=hv[moved]-high_before[moved])
    for name,expected in original_state.items():
        if name!=b.BODY:assert g.signature(bpy.data.objects[name])==expected
    assert b.mesh_signature(body.data)['uv']==original_state[b.BODY]['native']['uv'];assert b.config(s)==cfg and s.render.hair_type=='STRIP' and s.render.hair_subdiv==0
    b.camera('face');s['AFN35_status']='NATIVE_NEUTRAL_LID_REST_CANDIDATE_UNVERIFIED' if coarse_clean else 'REJECTED_COARSE_NATIVE_LID_REST';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save('a-build-verification.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'output':str(OUT),'outputSha256':b.sha(OUT),'originalVisibleMeshState':original_state,'originalConfig':cfg,'nativeChangedVertices':changed.tolist(),'nativeMovementMaximumM':float(np.linalg.norm(cv-V,axis=1).max()),'fullChangedVertices':len(moved),'fullMovementMaximumM':float(high_delta.max()),'changedBoundsM':{'min':hv[moved].min(0).tolist(),'max':hv[moved].max(0).tolist()},'nativeTopologyUVAndSourceFieldsPreserved':True,'eyeMeshesAndTransformsExact':True,'hairPositionSha256':hair_hash,'coarsePassed':coarse_clean,'seconds':time.time()-start,'scope':'New neutral lid rest only; source eye/skin material, hair/root width/pose/light state unchanged. Full contact/self/hair validation and visual review still required.'})
    label='b-after' if FIXED_SUPPORT else 'after';g.q.render(label);i.closeup(label);print('R35_BUILD_DONE',coarse_clean,len(changed),len(moved),flush=True)
if __name__=='__main__':main()
