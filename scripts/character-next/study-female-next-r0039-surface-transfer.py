"""Private C1 body-surface transfer; original artist data never public.
Own regularized biharmonic radial-basis deformation with source/target actual
skull surface ray correspondences plus fixed far-field anchors. This is not
hair generation or a contact guarantee; actual finite capsules are rechecked.
"""
import bpy,importlib.util,json,math,time
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('private39warp',Path(__file__).with_name('study-female-next-r0039-artist-transfer.py'));c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c)
a=c.a;m=c.m;f=c.f;b=c.b;v=c.v;S=c.a.S;E=c.E;PVT=c.PRIVATE
OUT=PVT/'aevrynd-female-next-r0039-c1-surface-transfer-study.blend'
C=np.array((0.,-.015,1.49));scale=np.array((.094,.085,.081));offset=np.array((0.,.005,.234))
def tree(V,T):return BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True)
def direction(phi,theta):return a.norm(np.array((.080*math.cos(theta)*math.sin(phi),-.100*math.cos(theta)*math.cos(phi),.09*math.sin(theta))))
def anchors(source,target):
    X=[];Y=[];notes=[]
    for phi in np.linspace(0,2*math.pi,32,endpoint=False):
        base=.27 if math.cos(phi)>.6 else -.72
        for theta in np.linspace(base,1.48,10):
            d=direction(phi,theta);start=C+d*.32
            sh,sn,si,sd=source.ray_cast(Vector(start),Vector(-d),.38)
            th,tn,ti,td=target.ray_cast(Vector(start),Vector(-d),.38)
            if sh is None or th is None or np.array(sn)@d<.1 or np.array(tn)@d<.1:continue
            X.append(np.array(sh));Y.append(np.array(th));notes.append((float(phi),float(theta)))
    count=len(X)
    for phi in np.linspace(0,2*math.pi,12,endpoint=False):
        for theta in np.linspace(-1.3,1.3,6):
            p=C+direction(phi,theta)*.25;X.append(p);Y.append(p)
    return np.array(X),np.array(Y),{'actualSurfacePairs':count,'fixedFarFieldPairs':len(X)-count,'skinRayParams':notes}
def fit(X,Y):
    Q=(X-C)/.10;delta=Y-X;K=np.linalg.norm(Q[:,None]-Q[None,:],axis=2);K+=np.eye(len(Q))*1e-6
    B=np.column_stack((np.ones(len(Q)),Q));A=np.block([[K,B],[B.T,np.zeros((4,4))]])
    coef=np.linalg.solve(A,np.vstack((delta,np.zeros((4,3)))))
    def apply(P):
        shape=P.shape;flat=P.reshape(-1,3);out=np.empty_like(flat,dtype='f8')
        for lo in range(0,len(flat),4096):
            q=(flat[lo:lo+4096]-C)/.10;D=np.linalg.norm(q[:,None]-Q[None,:],axis=2)
            out[lo:lo+4096]=flat[lo:lo+4096]+D@coef[:-4]+np.column_stack((np.ones(len(q)),q))@coef[-4:]
        return out.reshape(shape)
    return apply,coef
def exact_triangle_foot(point,tri):
    aa,bb,cc=tri;bc=np.linalg.lstsq(np.column_stack((bb-aa,cc-aa)),point-aa,rcond=None)[0];bary=np.r_[1-bc.sum(),bc]
    options=[]
    if bary.min()>=0:options.append(bary)
    for i,j in ((0,1),(1,2),(2,0)):
        edge=tri[j]-tri[i];t=float(np.clip((point-tri[i])@edge/max(edge@edge,1e-30),0,1));w=np.zeros(3);w[i]=1-t;w[j]=t;options.append(w)
    best=min(options,key=lambda w:float(np.linalg.norm(w@tri-point)))
    return best@tri,best
def main():
    start=time.time();raw=np.load(PVT/'artist-render-12k-reference-only.npz')['positions'].astype('f8');world0=raw*scale+offset;count=len(raw)
    assert b.sha(c.REF)=='1ad6202095c1793678fee7d69a7e9f8b5fdb6e5c293d300eb1062d2d437e8d48'
    bpy.ops.wm.open_mainfile(filepath=str(c.REF))
    def enable(lc):
        lc.exclude=False;lc.hide_viewport=False
        for q in lc.children:enable(q)
    enable(bpy.context.view_layer.layer_collection)
    for o in bpy.context.scene.objects:
        if o.name!='head':
            for mm in o.modifiers:mm.show_viewport=False;mm.show_render=False
    head=bpy.data.objects['head'];head.hide_set(False);bpy.context.view_layer.update()
    VS,TS=b.evaluated(head,True);VS=VS*scale+offset
    print('SOURCE_HEAD',len(VS),len(TS),VS.min(0),VS.max(0),flush=True)
    keep=np.all(np.abs(VS[TS][:,:,0])<.16,axis=1);TS=TS[keep];assert len(TS)>100
    source_tree=tree(VS,TS);ids=np.linspace(0,count-1,256,dtype='i4')
    # Original donor roots may be anatomically embedded. The diagnostic is
    # deliberately not called a source qualification and includes all segments.
    sourceR=np.load(S/'aevrynd-female-next-r0033-c-bob-fibres.npz')['radii'][:count]
    donor_diag=f.flowcheck.check(world0[ids],sourceR[ids],source_tree,VS[TS],roots=False)
    c.write('c1-donor-original-contact-diagnostic.json',donor_diag)
    bpy.ops.wm.open_mainfile(filepath=str(a.SRC));s=bpy.context.scene;b.setup(s,b.config(s));before=f.state()
    hair0=bpy.data.objects[f.OLD];base,rad=m.eval_arrays(hair0);mx=np.array(hair0.matrix_world);inv=np.linalg.inv(mx)
    V,T=b.evaluated(bpy.data.objects[b.BODY],True);target=tree(V,T)
    X,Y,info=anchors(source_tree,target);assert info['actualSurfacePairs']>150;warp,coef=fit(X,Y)
    world=warp(world0);fiterr=np.linalg.norm(warp(X)-Y,axis=1);print('RBF_FIT',len(X),fiterr.max(),flush=True)
    maximum_rebind=0.;roots=[];barys=[]
    for i,q in enumerate(world):
        h,n,ti,dist=target.find_nearest(Vector(q[0]));face=V[T[ti]];h,bary=exact_triangle_foot(q[0],face);n=a.norm(np.cross(face[1]-face[0],face[2]-face[0]));root=h+n*.00018;delta=root-q[0]
        maximum_rebind=max(maximum_rebind,float(np.linalg.norm(delta)));arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(q,axis=0),axis=1))]
        w=(1-np.clip(arc/.030,0,1))**2;q+=delta*w[:,None];q[0]=root
        assert bary.min()>=0 and abs(bary.sum()-1)<1e-12;roots.append(ti);barys.append(bary)
    local=((world-mx[:3,3])@inv[:3,:3].T).astype('f4');d=hair0.data.copy();d.name='AFN39_C1_PRIVATE_SURFACE_TRANSFER';d.remove_curves(indices=list(range(count,len(d.curves))));d.position_data.foreach_set('vector',local.ravel())
    obj=hair0.copy();obj.data=d;obj.name=d.name
    for mm in list(obj.modifiers):obj.modifiers.remove(mm)
    for key in list(obj.keys()):del obj[key]
    obj['aevrynd_layer']='PRIVATE_ARTIST_GROOM_SURFACE_TRANSFER_RESEARCH';obj['author']='Daniel Bystedt; surface deformation/retarget by Aevrynd';obj['license']='Upstream CC BY-SA version unresolved. No formal promotion/public geometry redistribution.'
    s.collection.objects.link(obj);obj.hide_render=True;hair0.hide_render=True;assert f.state()==before;obj.hide_render=False;obj.hide_set(False)
    p,r=v.hair_arrays(obj);world_saved=p.astype('f8')@mx[:3,:3].T+mx[:3,3];r=r.astype('f8')*np.linalg.norm(mx[:3,:3],ord=2)
    audit=f.flowcheck.check(world_saved[ids],r[ids],target,V[T]);c.write('c1-representative-body-contact.json',audit)
    # This is a body-shape retarget diagnostic, not a whole-character pass.
    f.E=PVT;f.render('c1-private')
    b.camera('face');s.camera.data.lens=85;s['AFN39_status']='PRIVATE_SURFACE_RETARGET_CONTACT_RESEARCH_NOT_ADOPTED'
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    np.savez_compressed(PVT/'c1-private-surface-transfer.npz',sourceAnchors=X,targetAnchors=Y,coefficients=coef,rootTriangles=np.array(roots,dtype='i4'),rootBarycentric=np.array(barys))
    c.write('c1-private-build.json',{'source':str(a.SRC),'sourceSha256':b.sha(a.SRC),'donor':str(c.REF),'donorSha256':b.sha(c.REF),
      'output':str(OUT),'outputSha256':b.sha(OUT),'author':'Daniel Bystedt (original groom), Aevrynd (retarget only)',
      'license':'CC BY-SA exact version unresolved; PRIVATE_RESEARCH_ONLY_NOT_ADOPTED','originalDonorContact':{k:donor_diag[k] for k in ('status','unqualifiedSegments','methods')},
      'surfaceTransfer':info,'regularizer':1e-6,'maximumAnchorFitErrorM':float(fiterr.max()),'maximumFinalRootRebindM':maximum_rebind,
      'count':count,'pointsPerCurve':128,'bodyEyeSkinLashBrowLightExposurePreserved':True,'sourceRadiiAndMaterialSubsetExact':True,
      'pilot':audit,'fullChildrenSelfContinuousMotionRuntime':'NOT_QUALIFIED','surfaceWarpInjectivity':'NOT_PROVED','noPublicAssetOrWebsitePromotion':True,'seconds':time.time()-start})
    print('R39_C1_DONE',audit['status'],audit['unqualifiedSegments'],maximum_rebind,time.time()-start,flush=True)
if __name__=='__main__':main()
