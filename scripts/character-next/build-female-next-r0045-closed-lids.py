"""Closed-first finite eyelid tissue volumes with exact union into body.

Different topology from rejected angle/harmonic/ARAP and radial socket cups.
Explicit upper/lower tissue sections are authored already closed. Their
anterior crease, finite lip, posterior surface and body anchoring are separate.
Boolean removes buried interfaces; it is not permission to leave overlaps.
"""
import bpy,importlib.util,json,time,hashlib,sys
from pathlib import Path
import numpy as np
from mathutils import Vector
sp=importlib.util.spec_from_file_location('r43for45',Path(__file__).with_name('inspect-female-next-r0043-ocular-junction.py'));i=importlib.util.module_from_spec(sp);sp.loader.exec_module(i)
b=i.b;f=i.f;S=b.S;R=b.R;E=R/'Evidence/character-female-next/r0045-closed-lid-topology';E.mkdir(exist_ok=True)
SRC=S/'aevrynd-female-next-r0042-b-shadow-quality-review.blend';OUT=S/'aevrynd-female-next-r0045-a-closed-first-lid-study.blend'
exact=f.flowcheck.module('surface37r45','verify-female-next-r0037-eye-margin.py')
NATIVE='--native-pilot' in sys.argv
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def source_data(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh(preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get());m.calc_loop_triangles();P=np.empty(len(m.vertices)*3,dtype='f4');m.vertices.foreach_get('co',P);P=P.reshape(-1,3).astype('f8');mx=np.array(o.matrix_world);P=P@mx[:3,:3].T+mx[:3,3];T=np.array([t.vertices[:] for t in m.loop_triangles],dtype='i4');loops=np.array([t.loops[:] for t in m.loop_triangles],dtype='i4');fields={}
    for n in ['AFN32_RegisteredCC0UVW','AFN32_PigmentWeight','AFN32_Roughness']:
        a=m.attributes[n];k=3 if a.data_type=='FLOAT_VECTOR' else 1;ar=np.empty(len(a.data)*k,dtype='f4');a.data.foreach_get('vector' if k==3 else 'value',ar);fields[n]=(a.data_type,ar.reshape(-1,k))
    uv={}
    for layer in m.uv_layers:
        ar=np.empty(len(layer.data)*2,dtype='f4');layer.data.foreach_get('uv',ar);uv[layer.name]=ar.reshape(-1,2)[loops]
    ev.to_mesh_clear();return P,T,fields,uv
def bary(p,tri):
    e=np.column_stack((tri[1]-tri[0],tri[2]-tri[0]));co=np.linalg.lstsq(e,p-tri[0],rcond=None)[0];w=np.array((1-co.sum(),co[0],co[1]))
    if w.min()>=0:return w
    # Exact finite-triangle closest feature for the approximate skin map.
    # Do not use a float32 BVH hit as an infinite-plane barycentric sample.
    choices=[]
    for x,z in [(0,1),(1,2),(2,0)]:
        d=tri[z]-tri[x];t=float(np.clip((p-tri[x])@d/max(d@d,1e-30),0,1));ww=np.zeros(3);ww[x]=1-t;ww[z]=t;choices.append((np.linalg.norm(ww@tri-p),ww))
    return min(choices,key=lambda x:x[0])[1]
def make_lid(side,part,bt,et,body,V,T,fields,uv):
    c=np.array(i.i.FITS[side]['centerM']);xs=np.linspace(-1,1,81);front=[];back=[];rows=[];maps=[]
    # One vertex at each canthal end, 17 across-tissue samples per interior X.
    # Outer and seam paths share real endpoints, without zero-area grids.
    for k,xn in enumerate(xs):
        x=c[0]+.0120*xn;w=np.sqrt(max(0.,1-xn*xn));base=c[2]-.0012+.0005*xn;seam=base-.0023*w
        outer=base+(.0100*w if part=='upper' else -.0080*w);vs=[0.] if k in (0,len(xs)-1) else np.linspace(0,1,17);ring=[]
        for v in vs:
            z=seam*(1-v)+outer*v;bh=bt.ray_cast(Vector((x,-.25,z)),Vector((0,1,0)),.3)[0];eh=et.ray_cast(Vector((x,-.25,z)),Vector((0,1,0)),.3)[0]
            sourceY=float(bh.y) if bh is not None else c[1]-.005;globeY=float(eh.y) if eh is not None else None
            target=globeY-.00070 if globeY is not None else sourceY-.00015
            # Source fold at outer attachment; anterior tarsal bulge near seam.
            q=v*v*(3-2*v);y=(1-q)*target+q*sourceY
            if globeY is not None:y=min(y,globeY-.00040)
            # Upper lip advances in front of lower, leaving a shallow crease.
            lipAdvance=.00025*(1-v)**3*w if part=='upper' else 0.
            y-=lipAdvance
            # Back is finite but outside the fixed actual globe. At the outer
            # footprint it enters original skin so exact union welds tissue.
            by=y+.00075
            if globeY is not None:by=min(by,globeY-.00008)
            assert by-y>1e-5
            ring.append(len(front));front.append((x,y,z));back.append((x,by,z));rows.append({'u':float(xn),'v':float(v),'part':part})
        maps.append(ring)
    F=[]
    def quad(a,z,c,d):F.extend(((a,z,c),(a,c,d)))
    for A,B in zip(maps,maps[1:]):
        if len(A)==1:
            for j in range(len(B)-1):F.append((A[0],B[j],B[j+1]))
        elif len(B)==1:
            for j in range(len(A)-1):F.append((A[j],B[0],A[j+1]))
        else:
            for j in range(len(A)-1):quad(A[j],B[j],B[j+1],A[j+1])
    P=np.array(front+back);n=len(front);faces=list(F)+[tuple(n+j for j in tri[::-1]) for tri in F]
    # Boundary of the anterior sheet, then finite side walls.
    edge={}
    for tri in F:
        for x,z in zip(tri,(tri[1],tri[2],tri[0])):edge.setdefault(tuple(sorted((x,z))),[]).append((x,z))
    for es in edge.values():
        if len(es)==1:
            x,z=es[0];faces.extend(((z,x,x+n),(z,x+n,z+n)))
    faces=np.array(faces,dtype='i4');signed=np.sum(np.einsum('ij,ij->i',P[faces[:,0]],np.cross(P[faces[:,1]],P[faces[:,2]])))/6
    if signed<0:faces=faces[:,::-1]
    # Actual old skin closest triangle correspondence, explicitly approximate
    # new tissue parameterization; exact original UV outside union is checked.
    weights=[];anc=[]
    for p in P:
        hit,_,tid,_=bt.find_nearest(Vector(p));weights.append(bary(p,V[T[tid]]));anc.append(int(tid))
    W=np.array(weights);anc=np.array(anc,dtype='i4');local=(P-np.array(body.matrix_world)[:3,3])@np.linalg.inv(np.array(body.matrix_world)[:3,:3]).T
    mesh=bpy.data.meshes.new(f'AFN45_{side}_{part}_TissueVolume');mesh.from_pydata(local.tolist(),[],faces.tolist());mesh.update();obj=bpy.data.objects.new(mesh.name,mesh);bpy.context.scene.collection.objects.link(obj);obj.matrix_world=body.matrix_world.copy()
    for mat in body.data.materials:mesh.materials.append(mat)
    for poly in mesh.polygons:poly.use_smooth=True
    for name,(dtype,values) in fields.items():
        result=np.einsum('ni,nik->nk',W,values[T[anc]]);att=mesh.attributes.new(name,dtype,'POINT');att.data.foreach_set('vector' if dtype=='FLOAT_VECTOR' else 'value',result.astype('f4').ravel())
    for name,values in uv.items():
        pointUV=np.einsum('ni,nik->nk',W,values[anc]);layer=mesh.uv_layers.new(name=name);layer.data.foreach_set('uv',pointUV[faces].astype('f4').ravel())
    attr=mesh.attributes.new('AFN45_LidVolumeRegion','INT','POINT');attr.data.foreach_set('value',np.full(len(P),1 if part=='upper' else 2,dtype='i4'));obj['aevrynd_layer']='EDITABLE_CLOSED_FIRST_'+part.upper()+'_EYELID_VOLUME';obj['scope']='Own explicit anterior/back/seam/outer tissue sections, static closed-rest Boolean authoring operand; not an animation rig.'
    data={'object':obj.name,'side':side,'part':part,'vertices':len(P),'triangles':len(faces),'frontVertices':n,'controls':rows,'strips':maps,'sourceTriangle':anc.tolist(),'sourceBarycentric':W.tolist(),'sourceCorrespondence':'Nearest actual source skin triangle; approximate new-tissue UV/pigment map, not measured anatomical correspondence','minimumThicknessYM':float(np.min(np.array(back)[:,1]-np.array(front)[:,1]))};return obj,data
def self_pairs(V,T,mask):
    bt=i.i.tree(V,T);idx=np.flatnonzero(mask);pairs=bt.overlap(i.i.tree(V,T[idx]));bad=set()
    for x,y in pairs:
        z=int(idx[y]);x=int(x)
        if x!=z and set(T[x]).isdisjoint(T[z]) and exact.intersections(V[T[x]],V[T[z]]):bad.add(tuple(sorted((x,z))))
    return bt,bad
def main():
    start=time.time();assert b.sha(SRC)=='d62c180a5af61f6f8d800926b101738c89a8fbe7785fe1054fd655fd018824da';bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.render.threads_mode='FIXED';s.render.threads=4;body=bpy.data.objects[b.BODY]
    if NATIVE:body.modifiers[0].levels=0;bpy.context.view_layer.update()
    V,T,fields,uv=source_data(body);bt=i.i.tree(V,T);eyes={side:i.i.outer(side) for side in ('L','R')};records=[];operands=[]
    save('round-contract.json',{'revision':'female-next-r0045-a','previousGoalTurnClassification':'progress: three geometry pilots disproved before expansion; no visual gain, history pushed3a9df7f','source':str(SRC),'sourceSha256':b.sha(SRC),'majorDefects':['Staring unchanging eyes','Cap/sheet hair silhouette','Flat skin response'],'chosenDefect':'Credible closed lid rest and its source skin connection before expressive-eye rig','method':'Closed-first finite upper/lower anatomical tissue sections, finite lip depth and separate posterior/outer attachment controls. Exact Boolean union removes buried interfaces and creates actual body boundary, rather than leaving intersecting overlays or flattening inherited rim topology. No radial socket cup.','hypothesis':'A valid closed tissue structure can close real front eye aperture and preserve a plausible canthal silhouette before authoring open/half corrective states','cheapTest':'Native actual tissue-volume topology,body8optics,affected self and closed front aperture; no full sculpt/attachment/dynamic expansion if invalid','reject':['Actual body/optics or new self intersections','Bad union or changed unrelated source body region','Distorted canthus/obvious pad silhouette in complete views','Unreconstructable layers/skin data'],'candidateCount':1,'resources':{'startUTC':'2026-10-19 14:58:35 UTC','checkpointUTC':'2026-10-19 15:43:35 UTC','diagnosticInitialMinutes':10,'threads':4,'heavyJobsAtOnce':1},'scope':'First static CLOSED rest, not blink animation,continuous contact,engine or appearance-score acceptance','referenceUse':'Local verified CC0 DanUlrich animation topology inspected for edge-flow principles; it has no closed key, no head/identity transplant. Own lid volume construction.'})
    for side in eyes:
        et=i.i.tree(*eyes[side])
        for part in ('upper','lower'):
            o,record=make_lid(side,part,bt,et,body,V,T,fields,uv);operands.append(o);records.append(record)
    save('a-closed-lid-authoring.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'operands':records,'status':'AUTHORING_OPERANDS_NOT_ACCEPTED'})
    # Rebuild from current actual evaluated body to preserve source skin fields
    # and independently inspect the union. Original native source is retained.
    deps=bpy.context.evaluated_depsgraph_get();mesh=bpy.data.meshes.new_from_object(body.evaluated_get(deps),preserve_all_data_layers=True,depsgraph=deps);union=bpy.data.objects.new('AFN45_BodyWithClosedLids',mesh);s.collection.objects.link(union);union.matrix_world=body.matrix_world.copy()
    for o in operands:
        mod=union.modifiers.new('AFN45_Union_'+o.name,'BOOLEAN');mod.operation='UNION';mod.solver='EXACT';mod.object=o;mod.use_self=False;mod.use_hole_tolerant=True;o.hide_render=True;o.hide_set(True)
    bpy.context.view_layer.update();NV,NT=b.evaluated(union,True);cent=NV[NT].mean(1);changed=np.zeros(len(NT),bool)
    for side in eyes:
        cc=np.array(i.i.FITS[side]['centerM']);changed|=(abs(cent[:,0]-cc[0])<.014)&(abs(cent[:,2]-cc[2])<.013)&(cent[:,1]<-.092)
    ut,bad=self_pairs(NV,NT,changed);contacts={}
    for side in eyes:
        for part in ('Sclera','Cornea','Iris','Pupil'):
            name=f'AFN30_{side}_{part}';ev,et=b.evaluated(bpy.data.objects[name],True);contacts[name]=len(ut.overlap(i.i.tree(ev,et)))
    edges=np.sort(np.concatenate((NT[:,[0,1]],NT[:,[1,2]],NT[:,[2,0]])),axis=1);_,cnt=np.unique(edges,axis=0,return_counts=True);scan={side:i.i.aperture(ut,i.i.tree(*eyes[side]),np.array(i.i.FITS[side]['centerM']),np.linspace(-.0108,.0108,51)) for side in eyes};visible={side:sum(bool(x.get('visible')) for x in rows) for side,rows in scan.items()};good=not bad and not any(contacts.values()) and np.all(cnt==2) and not any(visible.values());label='native' if NATIVE else 'full'
    save(f'a-{label}-closed-feasibility.json',{'status':'PASS_TESTED_CLOSED_BODY_SCOPE_ATTACHMENTS_PENDING' if good else 'REJECT_CLOSED_BODY_GEOMETRY','source':str(SRC),'sourceSha256':b.sha(SRC),'nativePilot':NATIVE,'bodyVertices':len(NV),'bodyTriangles':len(NT),'actualAffectedSelfPairs':len(bad),'selfExamples':sorted(bad)[:25],'bodyOpticsTrianglePairs':contacts,'bodyBoundaryEdges':int((cnt==1).sum()),'bodyNonManifoldEdges':int((cnt>2).sum()),'closedVisibleEyeColumns':visible,'eyeApertureRows':scan,'seconds':time.time()-start,'limitations':['Exact closed static pose only','Source wet tissues/lashes have not been rebuilt','No whole body self/continuous motion/runtime acceptance'],'decision':'Proceed to visual integration only if complete closed structure is valid; otherwise stop this construction.'});print('R45_CLOSED_GATE',label,good,'self',len(bad),'optics',contacts,'visible',visible,'edges',int((cnt!=2).sum()),time.time()-start,flush=True)
    np.savez_compressed(E/f'a-{label}-closed-body.npz',positionsWorld=NV,triangles=NT)
    if not good:return
    if NATIVE:return
    # Preserve independent source and editable operands in diagnostic collection.
    body.hide_render=True;body.hide_set(True);union['AFN45_status']='CLOSED_BODY_ONLY_ATTACHMENTS_UNQUALIFIED';s['AFN45_status']='CLOSED_REST_INTEGRATION_CANDIDATE_UNVERIFIED';b.camera('face');s.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);save('a-build-summary.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'output':str(OUT),'outputSha256':b.sha(OUT),'status':'CLOSED_BODY_STATIC_ONLY_ATTACHMENTS_VISUAL_AND_ALL_LAYER_CONTACT_PENDING','seconds':time.time()-start})
    f.E=E;f.render('a-closed-body',('face','oblique','profile'));i.ch.review.extras('a-closed-body',E);i.i.E=E;i.i.closeup('a-closed-body')
if __name__=='__main__':main()
