"""Pin actual brow-support skin, feather by surface distance, retain r19 lid warp."""
import bpy, json, importlib.util, heapq, math, time
import numpy as np
from pathlib import Path
spec=importlib.util.spec_from_file_location('angular',Path(__file__).with_name('build-female-next-r0019-angular-blink.py'));c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
a=c.a;R,S,solid=c.R,c.S,c.solid
E=R/'Evidence/character-female-next/r0020-pinned-blink';E.mkdir(exist_ok=True)
SRC=c.SRC;PREFIX='a';DST=S/'aevrynd-female-next-r0020-a-pinned-angular-blink-study.blend'
sha=a.sha
def save(name,obj):(E/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def support_mask(body,P,T,tree,bindings,width=.003):
    seeds=set(v for rec in bindings for v in rec['bodyVertices'])
    # Keep the supporting skin under the ENTIRE existing brow fibre footprint,
    # not merely its root. The fibre and its actual support stay together.
    for o in bpy.data.objects:
        if o.type=='MESH' and o.name.startswith('AFN11_'):
            for point in solid.data(o)[0]:
                hit,n,face,d=tree.find_nearest(point)
                if face is not None:seeds.update(T[face])
    graph=[[] for _ in P]
    for edge in body.data.edges:
        i,j=edge.vertices;length=float(np.linalg.norm(P[i]-P[j]));graph[i].append((j,length));graph[j].append((i,length))
    dist=np.full(len(P),np.inf);todo=[]
    for i in seeds:dist[i]=0.;heapq.heappush(todo,(0.,int(i)))
    while todo:
        d,i=heapq.heappop(todo)
        if d!=dist[i]:continue
        for j,length in graph[i]:
            candidate=d+length
            if candidate<width and candidate<dist[j]:dist[j]=candidate;heapq.heappush(todo,(candidate,int(j)))
    mask=c.smooth(dist/width)
    assert all(mask[i]==0 for i in seeds)
    return mask,{'pinnedVertices':len(seeds),'featheredVertices':int(((mask>0)&(mask<1)).sum()),'surfaceDistanceFeatherWidthM':width,'method':'Dijkstra edge-length distance from every root triangle and all nearest body triangles under the full existing brow geometry; smoothstep to unchanged lid field.'}

def main():
    started=time.time();bpy.ops.wm.open_mainfile(filepath=str(SRC));rig=bpy.data.objects['AFN_R0005_Rig'];solid.stage.set_pose(rig,'neutral');before=a.prior.controls();body=bpy.data.objects['AFN_R0008_Body'];P=a.positions(body).astype(np.float64);V,T,tree=solid.data(body);fits=solid.stage.eyes.helper_centres()
    brows=json.loads((S/'aevrynd-female-next-r0018-c-brow-bindings.json').read_text());mask,pin=support_mask(body,P,T,tree,brows);fields={};rims={};statistics=[]
    save('iteration-contract.json',{'source':str(SRC),'sourceSha256':sha(SRC),'stage':'B_COMPLETE_HEAD','previousGoalTurn':'Prompt maintenance updated execution rules; no model improvement claimed. r19 interrupted production has completed artifacts, no Blender process remains live.','hypothesis':'The r19 angular blink moves skin beneath dense brows, and independent triangle-frame transports cause fibre crossings. Pin the actual supporting skin beneath the entire brow footprint, feather over surface distance, and keep brow fibres on their unchanged actual support.','expectedVisibleChange':'Preserve neutral full head and brow appearance throughout blink; retain functional lid/lash movement.','smallestTest':'Build one candidate, verify exact fixed support, then actual affected surfaces before additional rendering.','rejectIf':['Any affected body self, body/eye, attachment/body, attachment self or cross attachment intersection at required samples.','Neutral appearance or scalp roots change.','Visible lid folding or unacceptable lid shape.'],'resources':{'threads':4,'candidates':1,'samples':'five synchronized plus asymmetric/midpoint states if initial samples pass','noFullHairResimulation':True},'knownSeparateIssue':'r19 C eye-ID render exposes canthus slivers. Pinning does not assert full closure; actual visible geometry must be tested separately.'})
    # Create both input properties before any ray query evaluates a driver.
    # Otherwise adding the second property can leave earlier driver relations stale.
    for side in ('L','R'):
        rig['AFN19_Blink_'+side]=0.;rig.id_properties_ui('AFN19_Blink_'+side).update(min=0.,max=1.,soft_min=0.,soft_max=1.)
    rig.update_tag();bpy.context.view_layer.update()
    for side,sign in (('L',1),('R',-1)):
        centre=np.array(fits[side]['centre']);rim=c.trace(tree,centre,sign);rims[side]=rim;fields[side]=[(P+(c.warp(P,centre,rim,j/4)-P)*mask[:,None]).astype(np.float32) for j in range(1,5)];rig['AFN19_Blink_'+side]=0.;rig.id_properties_ui('AFN19_Blink_'+side).update(min=0.,max=1.,soft_min=0.,soft_max=1.)
        for j,Q in enumerate(fields[side],1):c.add_driver(a.add_key(body,f'AFN20_Phase{j}_{side}',Q),rig,side,j)
        maxRoot=max(float(np.linalg.norm((Q-P)[rec['bodyVertices']]).max()) for Q in fields[side] for rec in brows);assert maxRoot==0.,maxRoot
        statistics.append({'side':side,'maximumBrowSupportingTriangleVertexMoveM':maxRoot,'closedChangedVertices':int(np.any(fields[side][-1]!=P.astype(np.float32),axis=1).sum()),'maximumMoveM':float(np.linalg.norm(fields[side][-1]-P,axis=1).max())})
    # Brows have unchanged geometry AND unchanged actual supporting skin.
    # Only lashes are transported; preserving their real root offsets at keys.
    records=json.loads((R/'Evidence/character-female-next/r0010-eye-rim/c-spaced-lashes-lash-bindings.json').read_text());transport=[]
    for name in sorted({r['object'] for r in records}):
        bindings=[r for r in records if r['object']==name];o=bpy.data.objects[name];rest=a.positions(o);M=np.array(o.matrix_world);inv=np.linalg.inv(M);W=rest.astype(np.float64)@M[:3,:3].T+M[:3,3]
        for side in ('L','R'):
            centre=np.array(fits[side]['centre']);targets=[]
            for j,Q in enumerate(fields[side],1):
                Q=Q.astype(np.float64);roots=[];angles=[]
                for rec in bindings:
                    ids=np.array(rec['bodyVertices']);bc=np.array(rec['barycentric']);rot=a.frame(Q[ids])@a.frame(P[ids]).T;anchor0=bc@P[ids];anchor1=bc@Q[ids];root0=W[rec['firstVertex']:rec['firstVertex']+6].mean(axis=0);root1=anchor1+rot@(root0-anchor0);roots.append((root0,root1));angles.append(math.atan2(root0[2]-centre[2],-(root0[1]-centre[1]))-math.atan2(root1[2]-centre[2],-(root1[1]-centre[1])))
                theta=float(np.median(angles));co,si=math.cos(theta),math.sin(theta);hinge=np.array(((1.,0.,0.),(0.,co,-si),(0.,si,co)));target=W.copy()
                for rec,(r0,r1) in zip(bindings,roots):
                    start=rec['firstVertex'];end=start+rec['vertices'];target[start:end]=(W[start:end]-r0)@hinge.T+r1
                local=(target@inv[:3,:3].T+inv[:3,3]).astype(np.float32);targets.append(local);transport.append({'object':name,'side':side,'phase':j,'maximumMoveM':float(np.linalg.norm(local-rest,axis=1).max()),'hingeDegrees':math.degrees(theta)})
            if any(np.any(Q!=rest) for Q in targets):
                for j,Q in enumerate(targets,1):c.add_driver(a.add_key(o,f'AFN20_Phase{j}_{side}',Q),rig,side,j)
    roots=json.loads((S/'aevrynd-female-next-r0014-root-bindings.json').read_text());scalp=[]
    for side in ('L','R'):
        delta=fields[side][-1]-P;maximum=max(float(np.linalg.norm(delta[r['bodyVertices']]).max()) for r in roots);assert maximum==0.;scalp.append({'side':side,'rootBindings':len(roots),'maximumSupportingTriangleVertexMoveM':maximum})
    cache=S/f'aevrynd-female-next-r0020-{PREFIX}-pinned-blink-data.npz';np.savez_compressed(cache,neutral=P.astype(np.float32),supportMask=mask.astype(np.float32),**{f'phase{j}{side}':Q for side,phases in fields.items() for j,Q in enumerate(phases,1)})
    # Rebuild driver relations after authoring all channels, including any that
    # were evaluated during the actual-geometry rim tracing pass.
    for o in bpy.data.objects:
        if o.type=='MESH' and o.data.shape_keys and o.data.shape_keys.animation_data:
            for f in o.data.shape_keys.animation_data.drivers:f.driver.expression=str(f.driver.expression)
    bpy.context.view_layer.update()
    tests=[]
    for left,right in ((0.,0.),(.125,.125),(.5,.5),(1.,1.),(1.,0.),(0.,1.)):
        a.set_blink(left,right);expected=P.copy()
        for side,w in (('L',left),('R',right)):
            for j,Q in enumerate(fields[side],1):expected+=max(0.,1-abs(4*w-j))*(Q-P)
        err=float(np.linalg.norm(np.array(solid.data(body)[0])-expected,axis=1).max());assert err<5.e-7,{'left':left,'right':right,'errorM':err,'keyValues':[(k.name,k.value) for k in body.data.shape_keys.key_blocks]};tests.append({'left':left,'right':right,'maximumEvaluatorErrorM':err})
    a.set_blink(0.,0.);assert a.prior.controls()==before;scene=bpy.context.scene;scene['aevrynd_revision']='female-next-r0020-a';scene['aevrynd_release_state']='PINNED_BROW_BLINK_RESEARCH_CONTACT_AND_CLOSURE_PENDING';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(DST));bpy.ops.wm.open_mainfile(filepath=str(DST));a.set_blink(0.,0.);assert a.prior.controls()==before
    save('a-build-verification.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(DST),'outputSha256':sha(DST),'neutralControlStateExact':True,'browSupportingSkinAndFibresFixed':True,'pinning':pin,'fields':statistics,'scalpRoots':scalp,'transport':transport,'driverChecks':tests,'cache':str(cache),'cacheSha256':sha(cache),'wallSeconds':time.time()-started,'status':'REOPEN_AND_CONTROL_PASS_CONTACT_CLOSURE_PENDING','limits':['Pinning and linear blending do not prove discrete surface validity or continuous contacts.','Lash roots follow triangle frames at authored phases; intermediate binding accuracy remains to be measured.','Canthus closure remains unresolved until new visibility evidence.']});print('R0020_BUILD_PASS',flush=True)
if __name__=='__main__':main()
