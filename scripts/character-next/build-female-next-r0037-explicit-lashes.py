"""Final candidate: exact original-vertex skin weld and explicit lash solids.

Boundary edge midpoints from A/B rounded below the source plane by<0.1um;
remove those virtual boundary nodes rather than relaxing seam tolerances.
Source r10 follicle-row offsets are transferred relative to its recorded rim,
not averaged/clamped to a new row. All220shapes retained. Native controls stay
editable and hidden; the displayed closed triangle tubes are tested directly.
"""
import bpy,importlib.util,json,time,math,copy,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
g=module('g37','build-female-next-r0037-eye-margin.py');f=module('f36','solve-female-next-r0036-brow-contacts.py');t=module('t37','build-female-next-r0037-retained-lashes.py');b=g.b;v=g.v;E=g.E;S=g.S;OUT=S/'aevrynd-female-next-r0037-c-explicit-eye-margin.blend'
EXACT='--exact-display' in sys.argv
if EXACT:OUT=S/'aevrynd-female-next-r0037-c-exact-display-eye-margin.blend'
def resolve(P,R,N,floor):
    rest=P.copy();fixed=P[:,0].copy();flat=P.reshape(-1,3);size=P.shape[1];n=size-1;norm=N.reshape(-1,3);floor=floor.reshape(-1,3);history=[]
    for iteration in range(24):
        ids,gap,ss,tt=f.contacts(P,R,8e-6);different=ids[:,0]//n!=ids[:,1]//n;ids=ids[different];gap=gap[different];active=ids[gap<4e-6];history.append({'iteration':iteration,'interstrandBelow1um':int((gap<=1e-6).sum()),'below4umDesign':len(active),'minimumTestedGapM':float(gap.min()) if len(gap) else None})
        if not len(active):break
        for i,j in active:
            ia=i//n*size+i%n;ib=j//n*size+j%n;dist,s,u=f.distances(flat[ia:ia+1],flat[ia+1:ia+2],flat[ib:ib+1],flat[ib+1:ib+2]);d=float(dist[0]);s=float(s[0]);u=float(u[0]);radius=max(R.ravel()[ia],R.ravel()[ia+1])+max(R.ravel()[ib],R.ravel()[ib+1]);need=max(0.,radius+4.5e-6-d)
            if need==0:continue
            direction=((1-s)*flat[ia]+s*flat[ia+1]-(1-u)*flat[ib]-u*flat[ib+1])/max(d,1e-12);ma=ia%size!=0;mb=ib%size!=0;den=ma*(1-s)**2+s*s+mb*(1-u)**2+u*u;step=need/max(den,1e-12)
            for k,w,sign,movable in [(ia,1-s,1,ma),(ia+1,s,1,True),(ib,1-u,-1,mb),(ib+1,u,-1,True)]:flat[k]+=direction*(step*w*sign*movable)
        depth=np.einsum('ij,ij->i',flat-floor,norm);flat+=norm*np.maximum(R.ravel()+25e-6-depth,0)[:,None];P[:,0]=fixed
        if np.linalg.norm(P-rest,axis=2).max()>.00010:break
    return P,{'history':history,'maximumDisplacementM':float(np.linalg.norm(P-rest,axis=2).max()),'allRootsExact':bool(np.array_equal(P[:,0],fixed)),'maximumAllowedDisplacementM':.00010,'scope':'Different-strand capsules only. Locally neighboring same-shaft capsule envelopes may overlap by construction; actual same-shaft closed displayed triangle surfaces are independently checked.'}
def tube(P,R):
    vertices=[];faces=[];radial=8
    for j,p in enumerate(P):
        tangent=P[min(j+1,len(P)-1)]-P[max(0,j-1)];tangent/=np.linalg.norm(tangent);axis=np.array((1.,0.,0.)) if abs(tangent[0])<.9 else np.array((0.,0.,1.));u=np.cross(tangent,axis);u/=np.linalg.norm(u);w=np.cross(tangent,u)
        for k in range(radial):a=k*math.tau/radial;vertices.append(p+R[j]*(math.cos(a)*u+math.sin(a)*w))
    for j in range(len(P)-1):
        for k in range(radial):z=(k+1)%radial;a=j*radial+k;bb=j*radial+z;c=(j+1)*radial+z;d=(j+1)*radial+k;faces.extend(((a,bb,c),(a,c,d)))
    first=len(vertices);vertices.append(P[0]);last=len(vertices);vertices.append(P[-1])
    for k in range(radial):z=(k+1)%radial;faces.extend(((first,z,k),(last,(len(P)-1)*radial+k,(len(P)-1)*radial+z)))
    return np.array(vertices),np.array(faces,dtype='i4')
def main():
    start=time.time();report=g.read('b-build.json');proof=g.read('b-saved-verification.json');assert proof['status']=='FAIL_OR_UNRESOLVED_ATTACHED_EYE_MARGIN';assert b.sha(Path(report['output']))==report['outputSha256'];template=np.load(S/'aevrynd-female-next-r0037-retained-lash-templates.npz');old_bind=g.read('b-lash-bindings.json');records=old_bind['roots'];legacy_rim=json.loads((b.R/'Evidence/character-female-next/r0010-eye-rim/b-organic-lashes-traced-rims.json').read_text());bpy.ops.wm.open_mainfile(filepath=report['output']);s=bpy.context.scene;original=g.state();body=bpy.data.objects[b.BODY];V,T=b.evaluated(body,True);bt=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True,epsilon=0.);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();local=np.array([list(q.co) for q in me.vertices]);normal=np.array([list(q.vector) for q in me.vertex_normals]);normal=normal@np.linalg.inv(np.array(body.matrix_world)[:3,:3]);normal/=np.linalg.norm(normal,axis=1)[:,None];fields={}
    for name in ('AFN32_RegisteredCC0UVW','AFN32_PigmentWeight','AFN32_Roughness'):
        attr=me.attributes[name];n=3 if attr.data_type=='FLOAT_VECTOR' else 1;values=np.empty(len(attr.data)*n,dtype='f4');attr.data.foreach_get('vector' if n==3 else 'value',values);fields[name]=values.reshape(-1,3) if n==3 else values
    ev.to_mesh_clear();patches=[]
    for old in g.read('a-tissue-bindings.json')['patches']:
        o=bpy.data.objects[old['object']];w=np.array([a.value for a in o.data.attributes['AFN37_WetWeight'].data]);factor=.9 if 'Caruncle' in o.name else .75;override={tuple(sorted(zip(n['indices'],n['weights']))):float(w[old['topVertices'][j]]/factor) for j,n in enumerate(old['nodes'])};mat=o.data.materials[0];bpy.data.objects.remove(o,do_unlink=True);patches.append(g.attached_patch(old['object'],body,V,T,local,normal,fields,np.array(old['sourceBodyTriangleIds'],dtype='i4'),lambda p:np.zeros(len(p)),old['maximumHeightM'],mat,exact_boundary=True,weights_override=override))
    data=g.read('a-tissue-bindings.json');data.update({'patches':patches,'exactBoundaryOriginalBodyVerticesOnly':True,'correction':'Removed virtual midpoint nodes on shared boundary edges. Original source-body boundary vertices are reused exactly; same1um interface tolerance, no broad exclusion or margin change.'});g.save('c-tissue-bindings.json',data)
    P=[];R=[];new_roots=[];groups=[];u32=np.linspace(0,1,32)
    # Template archive follows old retained binding ordering. B records are
    # grouped; match through source object/hair identity rather than row index.
    old_records=json.loads((b.R/'Evidence/character-female-next/r0010-eye-rim/c-spaced-lashes-lash-bindings.json').read_text());lookup={(r['object'],r['hair']):j for j,r in enumerate(old_records)}
    for name in report['lashes']:
        rows=[r for r in records if r['object']==name];side=rows[0]['side'];part=rows[0]['part'];sign=1 if side=='L' else -1;zsign=1 if part=='upper' else -1;legacy=legacy_rim[side][part];xlegacy=np.array([r['x'] for r in legacy]);zlegacy=np.array([r['point'][2] for r in legacy]);offsets=[]
        for row in rows:
            k=lookup[(row['sourceObject'],row['sourceHair'])];p=template['positions'][k];radius=template['radii'][k,0];surface=p[0]-template['normals'][k]*(radius+.000025);offsets.append(zsign*(surface[2]-np.interp(abs(surface[0]),xlegacy,zlegacy)))
        offsets=np.array(offsets);centre=np.array(v.i.FITS[side]['centerM']);eye=BVHTree.FromPolygons(*[a.tolist() for a in g.i.outer(side)],all_triangles=True);scan=v.i.aperture(bt,eye,centre,np.linspace(-.0104,.0104,151));scan=sorted([r for r in scan if r.get('visible') and r['visibleSampleRuns']==1],key=lambda r:sign*r['x'])[8:-8];start_index=len(P)
        for row,offset in zip(rows,offsets):
            k=lookup[(row['sourceObject'],row['sourceHair'])];oldp=template['positions'][k];oldr=template['radii'][k];parameter=row['parameter'];x=float(np.interp(parameter,np.linspace(0,1,len(scan)),[r['x'] for r in scan]));band=.00055+float(offset-np.median(offsets));z=float(np.interp(parameter,np.linspace(0,1,len(scan)),[r[part+'Z'] for r in scan])+zsign*band);skin,n,tid,bc=g.c.sample(bt,V,T,x,z);root=skin+n*(oldr[0]+.000025);delta=(oldp-oldp[0])@t.frame(template['normals'][k],sign)@t.frame(n,sign).T*row['scale'];path=root+delta;arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(path,axis=0),axis=1))];samples=u32*arc[-1];P.append(np.column_stack([np.interp(samples,arc,path[:,j]) for j in range(3)]));R.append(np.interp(samples,arc,oldr));r=dict(row);r.update({'bodyTriangle':int(tid),'bodyVertices':T[tid].tolist(),'barycentric':bc.tolist(),'surfaceM':skin.tolist(),'normal':n.tolist(),'standOffM':float(oldr[0]+.000025),'follicleOffsetFromActualApertureM':band});new_roots.append(r)
        groups.append({'object':name,'firstCurve':start_index,'curves':len(rows),'legacyActualRowOffsetRangeM':[float(offsets.min()),float(offsets.max())],'newAnteriorBaselineM':.00055})
    P=np.array(P);R=np.array(R)
    if EXACT:
        body_proof=v.g.check(P,R,bt,V[T]);g.save('c-authored-source-body-capsules.json',body_proof);assert body_proof['status']=='PASS_TESTED_STATIC_CAPSULES','Source paths need a real body correction before exact-mesh refinement'
        relax={'maximumDisplacementM':0.,'allRootsExact':True,'maximumAllowedDisplacementM':.00010,'method':'Actual authored paths pass complete body capsules. Preserve them unchanged; conservative interstrand capsule overlaps are unresolved until the complete displayed closed meshes plus containment anchors are tested. Do not push shapes to repair bounding-volume false positives.'}
    else:
        near=[bt.find_nearest(Vector(p)) for p in P.reshape(-1,3)];floor=np.array([list(h[0]) for h in near]).reshape(P.shape);N=np.array([list(h[1]) for h in near]).reshape(P.shape);N/=np.linalg.norm(N,axis=2)[...,None];P,relax=resolve(P,R,N,floor)
    g.save('c-exact-authoring.json' if EXACT else 'c-interstrand-authoring.json',relax)
    mesh_records=[];inverse=np.linalg.inv(np.array(body.matrix_world));controls=[]
    for group in groups:
        name=group['object'];o=bpy.data.objects[name];mat=o.data.materials[0];mx=np.array(o.matrix_world);inv=np.linalg.inv(mx[:3,:3]);a=group['firstCurve'];z=a+group['curves'];o.name=name.replace('Lashes','LashControls');controls.append(o.name);o.hide_render=True;o.hide_set(True);o.data.position_data.foreach_set('vector',((P[a:z]-mx[:3,3])@inv.T).astype('f4').ravel());o.data.attributes['radius'].data.foreach_set('value',(R[a:z]/np.linalg.norm(mx[:3,:3],ord=2)).astype('f4').ravel());verts=[];faces=[]
        for pp,rr in zip(P[a:z],R[a:z]):
            vv,tt=tube(pp,rr);offset=len(verts);verts.extend(vv);faces.extend(tt+offset)
        world=np.array(verts);localp=((world-np.array(body.matrix_world)[:3,3])@inverse[:3,:3].T).astype('f4');me=bpy.data.meshes.new(name+'_SolidGeometry');me.from_pydata(localp,[],faces);me.update();me.materials.append(mat);ob=bpy.data.objects.new(name,me);bpy.data.collections['AFN37_EYE_MARGIN'].objects.link(ob);ob.parent=body;ob.matrix_parent_inverse=Matrix.Identity(4);ob.matrix_basis=Matrix.Identity(4);ob['aevrynd_layer']='EYELASH_SOLIDS';ob['AFN37_source_controls']=o.name
        for polygon in me.polygons:polygon.use_smooth=True
        mesh_records.append({**group,'verticesPerCurve':258,'trianglesPerCurve':512,'rootCenterVertexOffset':256,'tipCenterVertexOffset':257,'rings':32,'sides':8})
    bpy.context.view_layer.update();assert g.state()==original;cache=S/('aevrynd-female-next-r0037-c-exact-lashes.npz' if EXACT else 'aevrynd-female-next-r0037-c-lashes.npz');np.savez_compressed(cache,positionsWorld=P,radiiWorld=R);g.save('c-exact-lash-bindings.json' if EXACT else 'c-lash-bindings.json',{'objects':report['lashes'],'roots':new_roots,'meshRecords':mesh_records,'controls':controls,'cache':str(cache),'cacheSha256':b.sha(cache),'representation':'Displayed closed triangle tubes with hidden native editable controls. Same-shaft actual triangle self contact verified; interstrand capsule bounds separately checked.','retainedSource':old_bind['retainedSource'],'retainedSourceSha256':old_bind['retainedSourceSha256'],'correction':'Actual legacy follicle row offsets from original traced lid, transferred to new actual aperture anterior0.55mm band. Not mean-neighbor height clamping, not greedy follicle deletion. All220shapes/radii retained.'});s['AFN37_status']='EXPLICIT_ATTACHED_EYE_MARGIN_PENDING_REOPENED_VERIFICATION';g.c.camera('face');bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);new=copy.deepcopy(report);new.update({'output':str(OUT),'outputSha256':b.sha(OUT),'representation':'CLOSED_TRIANGLE_TUBES','authoringControls':controls,'candidateBasis':'C fixes actual shared-boundary representation and source follicle-row transfer, then uses explicit closed displayed lash meshes. Same optical surface data/materials asB, no shader/density/tolerance changes.','contactRelaxation':relax,'seconds':time.time()-start});g.save('c-exact-build.json' if EXACT else 'c-build.json',new);g.render('c-after');g.closeup('c-after');print('R37_C_DONE',time.time()-start,flush=True)
if __name__=='__main__':main()
