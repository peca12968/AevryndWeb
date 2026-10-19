"""C: explicit regional guide-edit strokes on the live complete character.
No density/radius/material/light changes. No shared exits or global wave field.
"""
import bpy,importlib.util,json,time
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('l38c',Path(__file__).with_name('build-female-next-r0038-live-groom.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
f=m.f;b=m.b;v=m.v;S=m.S;E=m.E
OUT=S/'aevrynd-female-next-r0038-c-regional-guide-sculpt.blend'
# side, chart a/u center, footprint a/u, independent control displacements mm.
# Control stations t=0,.2,.45,.7,.9,1.  These are separate intentional shape
# edits (lift / outward mass / S-bend / inward curl), not random noise.
STROKES=[
(-1,.28,.82,.55,.35,[(0,0,0),(-2,-1,3),(-8,-4,2),(-6,-9,1),(1,-6,5),(4,-3,9)]),
(-1,.55,.18,.40,.30,[(0,0,0),(-1,0,0),(-3,-1,0),(-1,3,1),(-4,1,3),(-2,4,7)]),
(-1,1.05,.78,.50,.35,[(0,0,0),(-3,0,2),(-11,-2,1),(-15,-1,0),(-6,4,4),(3,7,11)]),
(-1,1.55,.22,.40,.28,[(0,0,0),(-1,0,0),(-2,0,0),(-5,2,0),(-1,4,2),(2,3,6)]),
(-1,1.70,.83,.45,.32,[(0,0,0),(-3,1,3),(-10,4,1),(-12,7,0),(-5,10,4),(4,7,9)]),
(-1,2.25,.76,.48,.35,[(0,0,0),(-2,2,2),(-7,8,1),(-6,13,0),(1,8,4),(4,3,8)]),
(-1,2.85,.25,.48,.30,[(0,0,0),(-1,1,0),(-3,5,0),(-2,8,0),(2,3,3),(3,1,5)]),
(1,.30,.76,.48,.38,[(0,0,0),(2,-1,2),(8,-5,1),(12,-7,0),(6,0,4),(-1,5,10)]),
(1,.72,.18,.40,.29,[(0,0,0),(1,0,0),(3,-1,0),(2,2,1),(5,1,3),(1,5,7)]),
(1,1.12,.85,.45,.32,[(0,0,0),(3,0,3),(10,0,1),(8,5,0),(1,8,3),(-3,5,10)]),
(1,1.62,.25,.44,.28,[(0,0,0),(1,0,0),(3,2,0),(5,3,0),(2,5,3),(-1,2,6)]),
(1,1.80,.75,.48,.34,[(0,0,0),(3,1,2),(10,4,1),(13,7,0),(7,9,4),(-1,6,11)]),
(1,2.35,.84,.50,.33,[(0,0,0),(2,2,3),(6,9,1),(7,12,0),(0,6,3),(-4,2,8)]),
(1,2.85,.25,.48,.30,[(0,0,0),(1,1,0),(2,4,0),(1,8,0),(-3,4,2),(-2,1,6)]),
]
def cubic(K,count=128):
    q=np.array(K,dtype='f8')*.001;knots=np.array((0.,.2,.45,.7,.9,1.));out=[]
    # Local cubic Hermite through the declared stations, with zero root slope.
    tang=np.zeros_like(q);tang[1:-1]=(q[2:]-q[:-2])/(knots[2:]-knots[:-2])[:,None];tang[-1]=(q[-1]-q[-2])/(knots[-1]-knots[-2])
    for t in np.linspace(0,1,count):
        i=min(4,int(np.searchsorted(knots,t,side='right')-1));i=max(i,0);dt=knots[i+1]-knots[i];u=(t-knots[i])/dt
        out.append((2*u**3-3*u*u+1)*q[i]+(u**3-2*u*u+u)*dt*tang[i]+(-2*u**3+3*u*u)*q[i+1]+(u**3-u*u)*dt*tang[i+1])
    return np.array(out)
def main():
    start=time.time();proof=json.loads((E/'b-reopened-verification.json').read_text());assert proof['status']=='PASS_REOPENED_LIVE_AUTHORING_REST_EXACT_SCOPE'
    src=Path(proof['source']);assert b.sha(src)==proof['sourceSha256']
    f.save('c-round-contract.json',{'source':str(src),'sourceSha256':b.sha(src),'candidateCountThisRound':3,
      'primaryDefect':'Original complete hair remains a thin straight cap/curtain. A global field has one synchronized bulge/wave and is rejected.',
      'basisDifference':'Use verified live manual guide deltas with14independently specified left/right regional strokes, different inner/outer-layer control shapes; no common exit/terminal, random waveform, density or shader change.',
      'expectedVisibleChange':'Modest crown lift, deeper outer layer, distinct regional bends and curled/varied ends on the same full root set.',
      'smallTest':'256actual displayed physical guide-following fibres against actual body; then complete-head review before full12k contact expansion',
      'reject':['Guide/body failure','Inflated wings, coherent sheets, root detachment, or no clear full-head benefit'],
      'scope':'Static visual candidate; if retained, all affected full-fibre contacts still need independent qualification. Not dynamics or runtime.',
      'strokes':STROKES,'stations':[0,.2,.45,.7,.9,1.]})
    bpy.ops.wm.open_mainfile(filepath=str(src));s=bpy.context.scene;before=f.state();hair=bpy.data.objects[f.OLD];base,rr=m.eval_arrays(hair)
    bind=np.load(S/'aevrynd-female-next-r0038-b-live-guide-bindings.npz');ids=bind['guideRootIds']
    info=np.load(S/'aevrynd-female-next-r0033-c-bob-fibres.npz');params=info['scalpParams'][ids];parts=info['parts'][ids]
    guide=bpy.data.objects[m.GUIDE];P,R=v.hair_arrays(guide);deltas=np.zeros_like(P,dtype='f8')
    for side,a,u,ar,ur,K in STROKES:
        d=((params[:,0]-a)/ar)**2+((params[:,1]-u)/ur)**2
        w=np.where(parts==side,np.exp(-2*d),0.)
        deltas+=w[:,None,None]*cubic(K)[None,:,:]
    edited=(P.astype('f8')+deltas).astype('f4');edited[:,0]=P[:,0]
    guide.data.position_data.foreach_set('vector',edited.ravel());guide.data.update_tag()
    p,r=m.eval_arrays(hair);assert np.array_equal(p[:,0],base[:,0]) and np.array_equal(r,rr)
    assert f.state()==before
    mx=np.array(hair.matrix_world);world=p.astype('f8')@mx[:3,:3].T+mx[:3,3];rad=r.astype('f8')*np.linalg.norm(mx[:3,:3],ord=2)
    V,T=b.evaluated(bpy.data.objects[b.BODY],True);tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True)
    audit=f.flowcheck.check(world[ids],rad[ids],tree,V[T]);f.save('c-representative-body-contact.json',audit)
    f.render('c-after')
    b.camera('face');s.camera.data.lens=85;s['AFN38_status']='REGIONAL_GUIDE_EDIT_VISUAL_CANDIDATE_NOT_CONTACT_ACCEPTED'
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    np.savez_compressed(S/'aevrynd-female-next-r0038-c-guide-edits.npz',guidePositions=edited,guideRootIds=ids)
    f.save('c-build.json',{'output':str(OUT),'outputSha256':b.sha(OUT),'guideCache':str(S/'aevrynd-female-next-r0038-c-guide-edits.npz'),
       'sourceStateExactExceptGuideAuthoringPositions':True,'radiiRootsMaterialStageExact':True,
       'maximumGuideEditM':float(np.max(np.linalg.norm(deltas,axis=2))),'pilot':audit,
       'fibres':len(p),'pointsPerFibre':128,'fullChildrenContacts':'NOT_TESTED','self':'NOT_TESTED','dynamicRuntime':'NOT_IMPLEMENTED',
       'decision':'AWAIT_COMPLETE_HEAD_REVIEW' if audit['status']=='PASS_TESTED_STATIC_CAPSULES' else 'PILOT_CONTACT_FAILURE_NO_FURTHER_EXPANSION',
       'seconds':time.time()-start})
    print('R38_C_EDIT_DONE',audit['status'],time.time()-start,flush=True)
if __name__=='__main__':main()
