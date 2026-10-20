"""Small actual 61-shaft packed-bundle method trial on the complete woman.

Hexagonal ordering, explicit finite radii and smooth root-to-free contraction
replace random convergence. No prior Bob paths, spherical comb field, template
clump shell or proxy hair geometry is used. Static feasibility precedes motion.
"""
from pathlib import Path
import bpy,numpy as np,json,math,time,hashlib,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0062-packed-bundle';E.mkdir(parents=True,exist_ok=True)
S=R/'engine/assets/characters/female-next/source';SRC=S/'aevrynd-female-next-r0060-b-limit-surface-assembly-study.blend';OUT=S/'aevrynd-female-next-r0062-a-packed-bundle-study.blend';NAME='AFN62_ACTUAL_PACKED_SHAFTS';N=128
def module(name,file):
    sp=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
g=module('base62','build-female-next-r0061-surface-flow-groom.py');pair=module('pairs62','hair-female-next-r0062-finite-pairs.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,obj):(E/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def unit(x):return x/max(np.linalg.norm(x),1e-20)

def frames(C,first=None):
    tangent=np.diff(C,axis=0);tangent=np.vstack((tangent,tangent[-1]));tangent/=np.linalg.norm(tangent,axis=1)[:,None];normal=np.empty_like(C);normal[0]=unit(np.array((1.,0,0))-tangent[0]*tangent[0,0]) if first is None else first
    for j in range(1,len(C)):
        axis=np.cross(tangent[j-1],tangent[j]);ss=np.linalg.norm(axis);cc=np.clip(tangent[j-1]@tangent[j],-1,1);nn=normal[j-1]
        if ss>1e-12:
            aa=axis/ss;nn=nn*cc+np.cross(aa,nn)*ss+aa*(aa@nn)*(1-cc)
        normal[j]=unit(nn-tangent[j]*(nn@tangent[j]))
    return normal,np.cross(tangent,normal)

def display(C,hexXY,rootOffsets,firstNormal,rootPoints):
    nn,bb=frames(C,firstNormal);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(C,axis=0),axis=1))];pitch=.00018+(.00065-.00018)*np.exp(-arc/.015)
    Q=C[None]+pitch[None,:,None]*(hexXY[:,0,None,None]*nn[None]+hexXY[:,1,None,None]*bb[None])
    Q+=rootOffsets[:,None]*np.exp(-arc/.005)[None,:,None];Q[:,0]=rootPoints
    return Q.astype('f4')

def main():
    tick=time.time();assert not OUT.exists();assert sha(SRC)==g.SOURCE_SHA
    save('round-contract.json',{'previousGoalTurnClassification':'progress: r61produced actual complete ponytail, exact native root data, full3.74mshaft/body checks and real self-falsification; rejected and GitHub2c7a5a2verified.','sixLines':['Use verified r60B complete woman, preserve qualified anatomy; no live Blender job or r62output at start.','Main defect: unstructured finite fibres intersect and lack usable clump mechanics; appearance still inadequate.','Deliver61actual ordered finite shafts on the same complete character, then a playable constrained wind-response trial if static structure passes. This is not a full hairstyle.','XPBD compliant length/bend principles and guide/follow separation; own hex packing and rotation-minimizing frames, real skin rest follicles.','All actual static finite capsule/body/self checks first. Reject loss of spacing, root/body crossing or explosive motion before scaling.','One method/candidate,4threads,one heavy job; diagnostic10min and45min checkpoint; no radius/density/angle sweeps.'],'references':[{'url':'https://mmacklin.com/xpbd.pdf','use':'Compliance, total multipliers and per-step projection; no paper text/code/assets redistributed.'},{'url':'https://github.com/GPUOpen-Effects/TressFX/blob/master/src/TressFX/TressFXHairObject.cpp','use':'Guide/follow representation principle only; no library installed or source code copied.'}],'fullHairAppearanceAcceptance':False})
    bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.scene.frame_set(1);body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING']
    for md in body.modifiers:
        if md.type=='SUBSURF':md.levels=md.render_levels
    bpy.context.view_layer.update();row=g.k.mesh(body);P=row['V'];T=row['T'];mask=np.isin(row['mi'],(4,5))&(P[T,2].min(1)>1.38);ids=np.flatnonzero(mask);skin=BVHTree.FromPolygons(P.tolist(),T[ids].tolist(),all_triangles=True)
    origin=np.array((0.,-.038,1.471));direction=unit(np.array((.030,.058,.069)));hit=skin.ray_cast(Vector(origin+direction*.4),Vector(-direction),.6);assert hit[0] is not None;root=np.array(hit[0]);normal=np.array(hit[1]);p1=root+normal*.030;p2=np.array((.055,.100,1.505));p3=np.array((.060,.145,1.325));u=np.linspace(0,1,513);C=(1-u[:,None])**3*root+3*((1-u)**2*u)[:,None]*p1+3*((1-u)*u*u)[:,None]*p2+u[:,None]**3*p3;arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(C,axis=0),axis=1))];C=np.column_stack([np.interp(np.linspace(0,arc[-1],N),arc,C[:,axis]) for axis in range(3)]);nn,bb=frames(C)
    xy=np.array([(q+.5*r,math.sqrt(3)*.5*r) for q in range(-4,5) for r in range(-4,5) if max(abs(q),abs(r),abs(q+r))<=4]);roots=[];correction=[];records=[]
    for x,y in xy:
        plane=root+.00065*(x*nn[0]+y*bb[0]);hit=skin.ray_cast(Vector(plane+normal*.012),Vector(-normal),.024);assert hit[0] is not None;ti=int(ids[hit[2]]);A=P[T[ti]];w=np.linalg.lstsq((A[1:]-A[0]).T,np.array(hit[0])-A[0],rcond=None)[0];bc=np.r_[1-w.sum(),w];foot=bc@A;assert bc.min()>-1e-4;roots.append(foot);correction.append(foot-plane);records.append((ti,int(row['nativeTriangleFace'][ti]),*bc))
    roots=np.array(roots);correction=np.array(correction);records=np.array(records);Q=display(C,xy,correction,nn[0],roots);rr=np.full(Q.shape[:2],.000035,dtype='f4');rr[:,-12:]*=np.linspace(1.,.10,12).astype('f4');assert len(Q)==61
    static=pair.static(Q,rr);save('a-static-self-verification.json',static);print('R62_PACKED_STATIC',static['status'],static['unqualifiedFinitePairs'],flush=True)
    tree=BVHTree.FromPolygons(P.tolist(),T.tolist(),all_triangles=True);contact=g.k.f.flowcheck.check(Q[:,1:],rr[:,1:],tree,P[T],roots=True);save('a-static-body-verification.json',contact)
    old=bpy.data.objects['AFN57_CANONICAL_BOB_GUIDES'];old.hide_render=True;old.hide_set(True);ob=g.create_curves(NAME,Q,rr);ob['scope']='Actual61physicalshafts as one packed guide/follow bundle. Static method trial, not a complete hairstyle or individual-shaft rod physics.'
    for name,kind,data,field in [('AFN62_RestRenderTriangle','INT',records[:,0].astype('i4'),'value'),('AFN62_NativeScalpFace','INT',records[:,1].astype('i4'),'value'),('AFN62_RestBarycentric','FLOAT_VECTOR',records[:,2:].astype('f4'),'vector')]:ob.data.attributes.new(name,kind,'CURVE').data.foreach_set(field,data.ravel())
    np.savez_compressed(E/'a-packed-bundle-authoring.npz',guide=C,hexXY=xy,rootOffsets=correction,firstNormal=nn[0],rootPoints=roots,positions=Q,radii=rr,rootRecords=records)
    for md in body.modifiers:
        if md.type=='SUBSURF':md.levels=1
    bpy.context.preferences.filepaths.save_version=0;g.k.b.camera('face');bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save('a-build-summary.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(OUT),'outputSha256':sha(OUT),'actualFibres':len(Q),'pointsPerFibre':N,'rootPitchM':.00065,'freePitchM':.00018,'maximumFibreRadiusM':float(rr.max()),'bodyStatus':contact['status'],'selfStatus':static['status'],'originalBodyOrSkinChanged':False,'scope':'Small true packed-shaft structure attached to complete r60woman; no full hairstyle/physics/runtime acceptance.','seconds':time.time()-tick})
    g.E=E;g.k.f.E=E;g.k.f.render('a-packed',('face','profile','oblique'));g.extra_views('a-packed');print('R62_PACKED_PREVIEW_READY',time.time()-tick,flush=True)
if __name__=='__main__':main()
