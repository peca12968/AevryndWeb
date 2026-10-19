"""Own restrained eyebrow groom rooted on the new female's actual skin.

Bounded follicle attempts; actual source surface rays and triangle/UV bindings.
Contact-rejected finite-radius strands, then explicit closed triangle tubes.
No original head coordinates, texture stripe, opaque backing or eye edits.
"""
import bpy,importlib.util,json,math,time
import numpy as np
from pathlib import Path
from collections import defaultdict
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('optics30',Path(__file__).with_name('build-female-next-r0030-eye-optics.py'));a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
b=a.b;R=b.R;S=b.S;E=R/'Evidence/character-female-next/r0031-native-brows';E.mkdir(parents=True,exist_ok=True)
SRC=S/'aevrynd-female-next-r0030-b-linear-iris-optics.blend';OUT=S/'aevrynd-female-next-r0031-a-native-brows.blend';BIND=S/'aevrynd-female-next-r0031-brow-bindings.json'
STATIONS=10;SIDES=6;VERTICES=STATIONS*SIDES+2;MAX_ATTEMPTS=600;MAX_FIBRES=300
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def read(n):return json.loads((E/n).read_text(encoding='utf8'))
def scene_controls():
    # Hidden source globe world matrices are unevaluated when excluded; record
    # their raw local transforms instead of depending on that viewport cache.
    return {'meshes':{o.name:{'mesh':b.mesh_signature(o.data),'parent':o.parent.name if o.parent else None,'basis':b.matrix(o.matrix_basis),'parentInverse':b.matrix(o.matrix_parent_inverse),'materials':[m.name if m else None for m in o.data.materials]} for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith('AFN31_')},'render':b.config(bpy.context.scene),'lights':[(o.name,list(o.location),list(o.rotation_euler),list(o.scale),o.data.energy,list(o.data.color),o.data.size) for o in bpy.context.scene.objects if o.type=='LIGHT'],'images':[(i.name,bool(i.packed_file)) for i in bpy.data.images if i.source=='FILE']}
def closest_segment_distances(A,B,P,Q):
    d1=B-A;d2=Q-P;r=A-P;aa=float(d1@d1);ee=np.einsum('ij,ij->i',d2,d2);ff=np.einsum('ij,ij->i',d2,r);cc=r@d1;bb=d2@d1;den=aa*ee-bb*bb;s=np.zeros_like(den);mask=den>1e-24;s[mask]=np.clip((bb[mask]*ff[mask]-cc[mask]*ee[mask])/den[mask],0,1);t=(bb*s+ff)/ee;low=t<0;high=t>1;s[low]=np.clip(-cc[low]/aa,0,1);s[high]=np.clip((bb[high]-cc[high])/aa,0,1);t=np.clip(t,0,1);delta=r+s[:,None]*d1-t[:,None]*d2;return np.linalg.norm(delta,axis=1)
class CapsuleHash:
    def __init__(self):self.cell=.0007;self.grid=defaultdict(list);self.A=[];self.B=[];self.radius=[];self.owner=[]
    def cells(self,a,c,r):
        lo=np.floor((np.minimum(a,c)-r)/self.cell).astype(int);hi=np.floor((np.maximum(a,c)+r)/self.cell).astype(int)
        for x in range(lo[0],hi[0]+1):
            for y in range(lo[1],hi[1]+1):
                for z in range(lo[2],hi[2]+1):yield(x,y,z)
    def conflicts(self,p,r,ignore_owner=None):
        for i in range(len(p)-1):
            radius=max(r[i],r[i+1]);ids=set(j for cell in self.cells(p[i],p[i+1],radius+.000006) for j in self.grid.get(cell,()))
            if ignore_owner is not None:ids={j for j in ids if self.owner[j]!=ignore_owner}
            if not ids:continue
            ids=sorted(ids);d=closest_segment_distances(p[i],p[i+1],np.array([self.A[j] for j in ids]),np.array([self.B[j] for j in ids]));clearance=d-radius-np.array([self.radius[j] for j in ids])
            if np.min(clearance)<.000006:return True
        return False
    def add(self,p,r,owner):
        for i in range(len(p)-1):
            index=len(self.A);rad=float(max(r[i],r[i+1]));self.A.append(p[i].copy());self.B.append(p[i+1].copy());self.radius.append(rad);self.owner.append(owner)
            for cell in self.cells(p[i],p[i+1],rad):self.grid[cell].append(index)
def barycentric(point,tri):
    uv=np.linalg.lstsq(np.column_stack((tri[1]-tri[0],tri[2]-tri[0])),point-tri[0],rcond=None)[0];bc=np.array([1-uv.sum(),uv[0],uv[1]])
    if bc.min()<-.00002 or bc.max()>1.00002:return None
    bc=np.maximum(0,bc);return bc/bc.sum()
def tube(p,r,normals):
    vertices=[];faces=[];oldaxis=None
    for i in range(STATIONS):
        tangent=p[min(i+1,STATIONS-1)]-p[max(0,i-1)];tangent/=np.linalg.norm(tangent);u=np.cross(tangent,normals[i]);u/=np.linalg.norm(u)
        if oldaxis is not None and oldaxis@u<0:u=-u
        oldaxis=u;v=np.cross(tangent,u)
        for j in range(SIDES):angle=math.tau*j/SIDES;vertices.append(p[i]+r[i]*(math.cos(angle)*u+math.sin(angle)*v))
    for i in range(STATIONS-1):
        for j in range(SIDES):
            k=(j+1)%SIDES;a=i*SIDES+j;c=i*SIDES+k;d=(i+1)*SIDES+k;e=(i+1)*SIDES+j;faces.extend(((a,c,d),(a,d,e)))
    first=len(vertices);vertices.append(p[0]);last=len(vertices);vertices.append(p[-1])
    for j in range(SIDES):
        k=(j+1)%SIDES;faces.extend(((first,k,j),(last,(STATIONS-1)*SIDES+j,(STATIONS-1)*SIDES+k)))
    return np.array(vertices),faces
def eyebrow_material():
    m,p=a.material('AFN31_NaturalBrownBrow',(.045,.022,.010),.46);p.inputs['Specular IOR Level'].default_value=.28;attr=m.node_tree.nodes.new('ShaderNodeAttribute');attr.attribute_name='AFN31_FibreColor';m.node_tree.links.new(attr.outputs['Color'],p.inputs['Base Color']);return m
def brow_center(t,sign):
    pts=np.array(((.0142,1.4774),(.0290,1.4888),(.0470,1.4880),(.0595,1.4739)))
    x,z=(1-t)**3*pts[0]+3*(1-t)**2*t*pts[1]+3*(1-t)*t*t*pts[2]+t**3*pts[3]
    if sign<0:z-=.00045+.00025*math.sin(math.pi*t);x+=.00015*math.sin(math.pi*t)
    return sign*x,z
def main():
    start=time.time();assert b.sha(SRC)=='7e0137afbac302c3233e2558fcf450453723b0e2d7ed11bb75abf87543678bf6'
    save('round-contract.json',{'previousGoalTurn':'progress: separated static optics and correct iris texture encoding retained; eye region remains doll-like.','source':str(SRC),'sourceSha256':b.sha(SRC),'defect':'New head has no brows and lacks natural fibre-based facial framing.','hypothesis':'Restrained actual brown fibres, feathered borders and upright-to-outward flow on the new supraorbital skin add credible facial framing without a painted stripe or solid underlay.','candidateCount':1,'limits':{'maximumAttemptsPerSide':MAX_ATTEMPTS,'maximumFibresPerSide':MAX_FIBRES,'curveStations':STATIONS,'tubeSides':SIDES,'threads':4,'checkpointMinutes':45},'reject':['No discernible complete-head improvement or coarse/combed/solid brows.','Full actual fibre/body/eye/self crossing or unresolved connected-strand containment.','Invalid source triangle/UV bindings or changed original body/eye/skin/stage.'],'scope':'Neutral static brow structure/appearance. Root metadata authored on actual evaluated skin; deformation/runtime evaluation not implemented.','reference':'Own earlier r18 triangle-fibre lessons only; no old head coordinates or third-party groom/code imported.'})
    bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;b.E=E;a.q.b.E=E;b.setup(s,b.config(s));before=scene_controls();a.q.render('before');a.E=E;a.closeup('before')
    body=bpy.data.objects[b.BODY];V,T=b.evaluated(body,True);bodytree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True,epsilon=0.0);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();mesh.calc_loop_triangles();loop=np.empty(len(mesh.loop_triangles)*3,dtype='i4');mesh.loop_triangles.foreach_get('loops',loop);loop=loop.reshape(-1,3);uv=np.empty(len(mesh.uv_layers.active.data)*2,dtype='f4');mesh.uv_layers.active.data.foreach_get('uv',uv);uv=uv.reshape(-1,2);ev.to_mesh_clear()
    col=bpy.data.collections.new('AFN31_BROWS');s.collection.children.link(col);mat=eyebrow_material();rng=np.random.default_rng(3131);all_bindings=[];summaries=[];paths=[];radii=[];hash=CapsuleHash()
    for side,sign in (('L',1),('R',-1)):
        vertices=[];faces=[];colors=[];accepted=0;rejects={'density':0,'ray':0,'capsule':0};attempts=0
        for attempt in range(MAX_ATTEMPTS):
            attempts=attempt+1
            if accepted>=MAX_FIBRES:break
            t=.015+.97*rng.beta(1.25,1.5);band=float(np.clip(rng.normal(0,.52),-1,1))
            if rng.random()>(1-band*band)**.5:rejects['density']+=1;continue
            x,z=brow_center(t,sign);width=(.0003+.00205*math.sin(math.pi*t)**.65)*(1-.25*t);z+=band*width;length=(.0037-.0010*t)*rng.uniform(.72,1.25);theta=math.radians(72*(1-t)**1.5+9-.18*band*35+rng.normal(0,6));bend=.28;root_radius=rng.uniform(.000020,.000030);lift=rng.uniform(.00010,.00024);u=np.linspace(0,1,STATIONS);rr=.000002+(root_radius-.000002)*(1-u)**.8;P=[];N=[];root=None;valid=True
            for j,progress in enumerate(u):
                xx=x+sign*length*(math.sin(theta)-math.sin(theta-bend*progress))/bend;zz=z+length*(math.cos(theta-bend*progress)-math.cos(theta))/bend;hit,normal,ti,d=bodytree.ray_cast(Vector((xx,-.35,zz)),Vector((0,1,0)),.5)
                if hit is None or normal.y>-.25:valid=False;break
                ids=T[ti];bc=barycentric(np.array(hit,dtype='f8'),V[ids])
                if bc is None:valid=False;break
                surface=bc@V[ids];n=np.array(normal,dtype='f8');n/=np.linalg.norm(n);gap=root_radius+.000045+lift*math.sin(math.pi*progress);P.append(surface+n*gap);N.append(n)
                if j==0:root={'bodyTriangle':int(ti),'bodyVertices':ids.tolist(),'barycentric':bc.tolist(),'surfacePointM':surface.tolist(),'normal':n.tolist(),'rootNormalOffsetM':gap,'surfaceUV':(bc@uv[loop[ti]]).tolist()}
            if not valid:rejects['ray']+=1;continue
            P=np.array(P);N=np.array(N)
            if hash.conflicts(P,rr):rejects['capsule']+=1;continue
            points,triangles=tube(P,rr,N);offset=len(vertices);vertices.extend(points.tolist());faces.extend(tuple(offset+i for i in f) for f in triangles);shade=float(rng.uniform(.72,1.28));base=np.array((.045,.022,.010))*shade
            for j in range(STATIONS):colors.extend([(*base*(.82+.18*j/(STATIONS-1)),1)]*SIDES)
            colors.extend([(*base*.82,1),(*base,1)]);name=f'AFN31_{side}_BrowFibres';record={'object':name,'fibre':accepted,'firstVertex':offset,'vertices':VERTICES,'root':root,'pathIndex':len(paths),'curvePointsM':P.tolist(),'radiiM':rr.tolist(),'lengthInputM':float(length),'growthAngleRadians':float(theta),'fieldParameter':float(t),'rootBand':band};all_bindings.append(record);paths.append(P);radii.append(rr);hash.add(P,rr,len(paths)-1);accepted+=1
        assert accepted>=120,(side,accepted)
        name=f'AFN31_{side}_BrowFibres';m=bpy.data.meshes.new(name);m.from_pydata(vertices,[],faces);m.update();o=bpy.data.objects.new(name,m);col.objects.link(o);o.parent=body;o.matrix_world=Matrix.Identity(4);m.materials.append(mat);attr=m.color_attributes.new(name='AFN31_FibreColor',type='FLOAT_COLOR',domain='POINT');attr.data.foreach_set('color',np.array(colors,dtype='f4').ravel())
        for p in m.polygons:p.use_smooth=True
        o['AFN31_root_bindings']=BIND.name;o['AFN31_static_authoring_only']=True;row={'object':name,'fibres':accepted,'vertices':len(vertices),'triangles':len(faces),'attempts':attempts,'rejections':rejects};summaries.append(row);print('R0031_BROW',json.dumps(row),flush=True)
    assert scene_controls()==before;BIND.write_text(json.dumps({'sourceBodySha256':b.sha(SRC),'bodyObject':b.BODY,'evaluatedLevel':3,'trianglesSha256':__import__('hashlib').sha256(T.tobytes()).hexdigest(),'coordinateSpace':'World metres in recorded neutral source; parent matrix and skin source must be unchanged.','scope':'Actual triangle/barycentric/UV follicle data, not an implemented deforming attachment solver.','fibres':all_bindings},separators=(',',':'))+'\n',encoding='utf8');np.savez_compressed(S/'aevrynd-female-next-r0031-brow-curves.npz',positions=np.array(paths),radii=np.array(radii));b.camera('face');s['AFN31_status']='NATIVE_TRIANGLE_BOUND_BROW_STATIC_REVIEW';bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save('build-verification.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'output':str(OUT),'outputSha256':b.sha(OUT),'bindings':str(BIND),'bindingsSha256':b.sha(BIND),'curveCache':str(S/'aevrynd-female-next-r0031-brow-curves.npz'),'originalControls':before,'originalBodyEyesSkinStageExact':True,'brows':summaries,'radiusM':[.000002,.000030],'minimumInterstrandCapsuleGapDesignM':.000006,'method':'Bounded native-skin follicle field, own explicit triangle tubes, actual conservative finite-segment capsule rejection.','seconds':time.time()-start,'limits':['Static new brow only; body has no facial rig.','Bindings are authoring data, not tested deformation or runtime execution.','Appearance and saved complete triangle/containment verification pending.']});a.q.render('after');a.closeup('after');print('R0031_BUILD_DONE',flush=True)
if __name__=='__main__':main()
