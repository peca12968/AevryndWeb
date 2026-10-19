"""Own two-part scalp groom: actual scalp attachment then free 3D fall.

No old hairstyle geometry, projected free-length sheet, convex-hull routing,
nearest-CV pushes or third-party node code. Static feasibility precedes children.
"""
import bpy, importlib.util, json, math, sys, time, hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

def module(name, file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

q=module('q29','build-female-next-r0029-native-eye-interface.py');b=q.b
cap=module('cap12','verify-female-next-r0012-hair-segments.py')
E=b.R/'Evidence/character-female-next/r0033-parted-bob';E.mkdir(parents=True,exist_ok=True)
SRC=b.S/'aevrynd-female-next-r0032-b-chart-registered-skin.blend'
OUT=b.S/'aevrynd-female-next-r0033-a-parted-bob-guides.blend'
C=np.array((0.,-.015,1.490));AXES=np.array((.071,.09,.073))
AZ=np.array((.012,.20,.52,.94,1.35,1.77,2.20,2.65,3.129))
U=np.array((0.,.33,.67,1.))
N=96

def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def normalized(v):return v/max(np.linalg.norm(v),1e-20)
def smooth(x):return x*x*(3-2*x)

def signature(o):
    v,t=b.evaluated(o,True);h=hashlib.sha256();h.update(v.tobytes());h.update(t.tobytes())
    return {'vertices':len(v),'triangles':len(t),'worldSha256':h.hexdigest(),'native':b.mesh_signature(o.data)}

def theta_min(phi):
    c=math.cos(phi);return .42*max(c,0.)**2-.28*max(-c,0.)**2

def scalp(tree,tri,phi,theta):
    d=normalized(AXES*np.array((math.cos(theta)*math.sin(phi),-math.cos(theta)*math.cos(phi),math.sin(theta))))
    hit,n,tid,distance=tree.ray_cast(Vector(C+d*.30),Vector(-d),.40)
    if hit is None:raise ValueError(('no scalp ray',phi,theta))
    p=np.array(hit);normal=normalized(np.array(n))
    assert normal@d>.15,(phi,theta,p,normal)
    a,bb,c=tri[tid];vv=bb-a;w=c-a;delta=p-a
    A=np.array(((vv@vv,vv@w),(vv@w,w@w)));rhs=np.array((vv@delta,w@delta));xy=np.linalg.solve(A,rhs)
    bary=np.array((1-xy.sum(),xy[0],xy[1]));assert bary.min()>-2e-3
    return p,normal,int(tid),bary

def ellipse(phi,rx,rf,rb,z):return np.array((rx*math.sin(phi),C[1]-(rf if math.cos(phi)>0 else rb)*math.cos(phi),z))

def path(tree,tri,side,a,u):
    theta=theta_min(a)+(1.42-theta_min(a))*u;phi=side*a
    goal=a+.85*math.exp(-(a/.8)**2)-.06*math.sin(2*a)
    theta_end=min(theta,.07);lift=.0045+.002*(.5+.5*math.sin(2*a+4*u))
    P=[];root=None
    for t in np.linspace(0,1,65):
        f=smooth(t);p,n,tid,bary=scalp(tree,tri,side*(a+(goal-a)*f),theta+(theta_end-theta)*f)
        distance=.00018+lift*math.sin(math.pi*.5*t)**1.2
        P.append(p+n*distance)
        if root is None:root={'triangle':tid,'barycentric':bary.tolist(),'skinPoint':p.tolist(),'normal':n.tolist(),'standOffM':.00018,'part':int(side),'scalpParam':[a,u],'azimuth':phi,'elevation':theta}
    p0=P[-1];p1=ellipse(side*goal,.087,.105,.100,min(p0[2]-.020,1.474))
    p2=ellipse(side*goal,.082,.095,.085,min(p1[2]-.050,1.410))
    tip=ellipse(side*goal,.073,.085,.080,1.365+.008*math.sin(3*a+2.3*u))
    for t in np.linspace(0,1,65)[1:]:
        point=(1-t)**3*p0+3*(1-t)**2*t*p1+3*(1-t)*t*t*p2+t**3*tip
        # A small smooth authored curl has genuine spatial thickness, not a
        # shared clamped projection plane. Both endpoint positions stay fixed.
        phase=2*a+3*u;point+=.0018*math.sin(math.pi*t)**2*np.array((side*math.sin(phase+2*t),math.cos(phase+1.7*t),.3*math.sin(phase+t)))
        P.append(point)
    P=np.array(P);lengths=np.concatenate(([0.],np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))))
    samples=np.linspace(0,lengths[-1],N);P=np.column_stack([np.interp(samples,lengths,P[:,k]) for k in range(3)])
    return P,root

def check(paths,radii,tree,tri,roots=True):
    methods={};bad=[];minimum=math.inf;cvmin=math.inf;inside=[];segments=0
    for ci,(P,rr) in enumerate(zip(paths,radii)):
        ds=[tree.find_nearest(Vector(p))[3] for p in P];cvmin=min(cvmin,float(np.min(np.array(ds)-rr)))
        if roots:
            state=cap.solid.classify(tree,tri,Vector(P[0]))
            if state!='outside':inside.append({'curve':ci,'state':state,'root':P[0].tolist()})
        for j in range(len(P)-1):
            gap,method=cap.segment_test(P[j],P[j+1],ds[j],ds[j+1],float(max(rr[j],rr[j+1])),tree,tri)
            minimum=min(minimum,gap);methods[method]=methods.get(method,0)+1;segments+=1
            if gap<=0:bad.append({'curve':ci,'segment':j,'method':method,'gapLowerBoundM':gap,'a':P[j].tolist(),'b':P[j+1].tolist()})
        if ci%1000==0:print('R33_CONTACT',ci,len(paths),len(bad),flush=True)
    return {'status':'PASS_TESTED_STATIC_CAPSULES' if not bad and not inside else 'FAIL_OR_UNRESOLVED','curves':len(paths),'segments':segments,'unqualifiedSegments':len(bad),'rootFailures':inside,'minimumCertifiedClearanceLowerBoundM':minimum,'minimumSampledCVSurfaceGapM':cvmin,'methods':methods,'failureSamples':bad[:120],'numericalAllowanceM':1e-6,'scope':'Actual full POLY segment capsules with max endpoint radius against actual evaluated body; static neutral only. No child/self/motion or runtime inference.'}

def material():
    m=bpy.data.materials.new('AFN33_ChestnutFibre_EEVEE');m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(.038,.016,.008,1);p.inputs['Roughness'].default_value=.43;p.inputs['Specular IOR Level'].default_value=.28
    if 'Anisotropic IOR Level' in p.inputs:p.inputs['Anisotropic IOR Level'].default_value=.5
    m.diffuse_color=(.038,.016,.008,1);return m

def guides(paths,body,mat):
    d=bpy.data.curves.new('AFN33_EDITABLE_PARTED_GUIDES','CURVE');d.dimensions='3D';d.bevel_depth=.00008;d.bevel_resolution=0;d.resolution_u=1;d.use_fill_caps=True;d.materials.append(mat)
    for P in paths:
        s=d.splines.new('POLY');s.points.add(len(P)-1);s.points.foreach_set('co',np.column_stack((P,np.ones(len(P)))).astype('f4').ravel())
        s.points.foreach_set('radius',np.linspace(1.,.08,len(P)).astype('f4'))
    o=bpy.data.objects.new(d.name,d);bpy.context.scene.collection.objects.link(o);o.parent=body;o.matrix_world=Matrix.Identity(4)
    o['aevrynd_layer']='EDITABLE_SCALP_GUIDES';o['scope']='Static coarse hairstyle feasibility, not complete human hair';return o

def scalp_domains(tree,tri,body):
    for side in (-1,1):
        vertices=[];faces=[];uv=[];az=np.linspace(.004,math.pi-.004,25);us=np.linspace(0,1,13)
        for u in us:
            for a in az:
                p,n,tid,bary=scalp(tree,tri,side*a,theta_min(a)+(1.54-theta_min(a))*u);vertices.append(p.tolist());uv.append((a/math.pi,u))
        for j in range(len(us)-1):
            for k in range(len(az)-1):
                x=j*len(az)+k;faces.append((x,x+1,x+1+len(az),x+len(az)))
        m=bpy.data.meshes.new('AFN33_SCALP_DOMAIN_'+('L' if side<0 else 'R'));m.from_pydata(vertices,[],faces);m.update();layer=m.uv_layers.new(name='AFN33_ScalpUV')
        for loop in m.loops:layer.data[loop.index].uv=uv[loop.vertex_index]
        o=bpy.data.objects.new(m.name,m);bpy.context.scene.collection.objects.link(o);o.hide_render=True;o.hide_viewport=True;o.parent=body;o.matrix_world=Matrix.Identity(4)
        o['aevrynd_layer']='AUTHORING_SCALP_DOMAIN';o['scope']='Own sampled chart domain; coarse chords are not certified skin/contact proxies. Exact roots bind actual evaluated body triangles.'

def main():
    start=time.time();assert b.sha(SRC)=='7b8b110dd50db95a722797113d8abe2a1682d347e8e1874412999c70c21c1a20';cap.math_controls()
    save('round-contract.json',{'previousGoalTurnClassification':'progress: user-requested goal v7 rewritten, mirrored and pushed fe393cd; no model improvement claimed','source':str(SRC),'sourceSha256':b.sha(SRC),'type':'COMPLETE_HAIRSTYLE_FEASIBILITY_ON_RETAINED_HEAD','primaryDefect':'Bald full-head silhouette; no new native-scalp hairstyle yet','hypothesis':'Actual scalp two-part root charts with surface-following crown paths and separately authored free Bezier fall can produce an editable bob without the old convex-hull cap or fringe sheet routing','candidateCount':1,'pilot':{'guides':72,'pointsPerGuide':N,'radiusM':.00008,'fullBodyCapsules':True},'reject':['Any unresolved actual guide/body capsule or root containment','Detached scalp, cap/sheet silhouette, severe part/ear routing artifacts in complete-head views'],'nextExpansion':'Only after guide feasibility and whole-head preview; children require their own contact test','timeCheckpointMinutes':45,'threads':4,'integrationTarget':str(SRC),'preserve':'All original visible evaluated meshes, skin/optical materials and stage; add separate editable scalp/hair layers only','reference':'https://docs.blender.org/manual/en/5.1/modeling/geometry_nodes/hair/generation/interpolate_hair_curves.html','referenceUse':'Guide/surface chart/parting workflow only; own geometry and code, no third-party hairstyle or node implementation imported'})
    bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene;b.E=E
    body=bpy.data.objects[b.BODY];cfg=b.config(scene);b.setup(scene,cfg)
    original={o.name:signature(o) for o in scene.objects if o.type=='MESH' and not o.hide_render}
    save('baseline-state.json',{'visibleEvaluatedMeshes':original,'config':cfg})
    if '--skip-before' not in sys.argv:q.render('before')
    V,T=b.evaluated(body,True);tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);tri=V[T]
    paths=[];bindings=[]
    for side in (-1,1):
        for u in U:
            for a in AZ:
                p,root=path(tree,tri,side,float(a),float(u));paths.append(p);bindings.append(root)
    paths=np.array(paths);radii=np.broadcast_to(np.linspace(.00008,.0000064,N),(len(paths),N)).copy()
    audit=check(paths,radii,tree,tri);save('a-guide-contact.json',audit)
    mat=material();o=guides(paths,body,mat);scalp_domains(tree,tri,body);bpy.context.view_layer.update()
    actual=np.array([[tuple(o.matrix_world@Vector(p.co[:3])) for p in spline.points] for spline in o.data.splines])
    roundtrip_error=float(np.max(np.linalg.norm(actual-paths,axis=2)))
    # Float32 saved positions are independently tested, not assumed identical.
    actual_radii=np.array([[point.radius*o.data.bevel_depth for point in spline.points] for spline in o.data.splines])
    actual_audit=check(actual,actual_radii,tree,tri);save('a-saved-precision-guide-contact.json',actual_audit)
    np.savez_compressed(b.S/'aevrynd-female-next-r0033-a-parted-bob-guides.npz',positions=actual.astype('f4'),radii=actual_radii.astype('f4'),scalpParams=np.array([x['scalpParam'] for x in bindings]),parts=np.array([x['part'] for x in bindings],dtype='i4'),rootTriangles=np.array([x['triangle'] for x in bindings],dtype='i4'),rootBarycentric=np.array([x['barycentric'] for x in bindings]))
    save('a-root-bindings.json',{'roots':bindings,'skinTriangleSource':original[b.BODY],'parting':'Separate left/right chart indices; no interpolation across center part','generation':'Actual scalp rays only for rooted crown; free lengths are authored 3D controls, not projected or body-pushed'})
    current={n:signature(bpy.data.objects[n]) for n in original};assert current==original;assert b.config(scene)==cfg
    b.camera('face');scene['AFN33_status']='GUIDE_FEASIBILITY_NOT_FINISHED_HAIR';scene['AFN33_source_sha256']=b.sha(SRC)
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save('a-build-verification.json',{'output':str(OUT),'outputSha256':b.sha(OUT),'source':str(SRC),'sourceSha256':b.sha(SRC),'preservedVisibleMeshes':current,'stageConfigExact':True,'guideContact':actual_audit,'positionRoundtripMaximumM':roundtrip_error,'expansionAllowed':actual_audit['status']=='PASS_TESTED_STATIC_CAPSULES','seconds':time.time()-start,'scope':'72 actual editable guides + two hidden scalp domains integrated on retained r32 head. Not dense hairstyle, self collision, dynamics or runtime.'})
    q.render('a-guides');print('R0033_GUIDES_DONE',actual_audit['status'],flush=True)

if __name__=='__main__':main()
