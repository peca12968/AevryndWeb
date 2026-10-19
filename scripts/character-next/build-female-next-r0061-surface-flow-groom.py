"""New scalp-intrinsic ponytail authoring on the coherent female.

Actual render-level skin supplies follicles and the surface used by hand-chosen
combing routes. No Bob geometry, normal-seed Comb strokes or clump shell reuse.
The small guide trial must precede density expansion and contact acceptance.
"""
from pathlib import Path
import bpy, numpy as np, json, hashlib, importlib.util, sys, time
import math
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

R=Path(r'D:\Download\Aevrynd'); E=R/'Evidence/character-female-next/r0061-surface-flow-groom'
S=R/'engine/assets/characters/female-next/source'
SRC=S/'aevrynd-female-next-r0060-b-limit-surface-assembly-study.blend'
SOURCE_SHA='3324231ec149a138a9de72c19a38ab7e46165e7ccde872f9e130a5b6abf56d9d'
E.mkdir(parents=True,exist_ok=True)
sp=importlib.util.spec_from_file_location('ocular61',Path(__file__).with_name('verify-female-next-r0060-assembly.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(E/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def extra_views(tag):
    spec=importlib.util.spec_from_file_location('views61',Path(__file__).with_name('verify-female-next-r0038-live-groom.py'))
    views=importlib.util.module_from_spec(spec);spec.loader.exec_module(views);views.E=E
    return views.render_extras(tag)

def load():
    assert sha(SRC)==SOURCE_SHA
    bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.scene.frame_set(1)
    body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING']
    for mod in body.modifiers:
        if mod.type=='SUBSURF':mod.levels=mod.render_levels
    bpy.context.view_layer.update()
    row=k.mesh(body);P=row['V'];T=row['T'];skin=np.isin(row['mi'],(4,5));top=float(P[:,2].max())
    rows=[]
    for delta in (.015,.04,.07,.10,.13,.16,.19,.22,.27,.34):
        points=P[np.abs(P[:,2]-(top-delta))<.001]
        rows.append({'belowTopM':delta,'count':len(points),'min':points.min(0).tolist() if len(points) else [],'max':points.max(0).tolist() if len(points) else []})
    save('actual-head-sections.json',{'source':str(SRC),'sha256':SOURCE_SHA,'top':top,'worldBounds':[P.min(0).tolist(),P.max(0).tolist()],'sections':rows})
    np.savez_compressed(E/'actual-body-render-surface.npz',P=P,T=T,skin=skin,sourceFace=row['nativeTriangleFace'])
    return body,row

def normalize(p):return p/np.linalg.norm(p,axis=-1,keepdims=True)

def create_curves(name,Q,radii):
    # Retain the proven portable native curve data format. No new addon/data API.
    d=bpy.data.objects['AFN57_CANONICAL_BOB_GUIDES'].data.copy();d.name=name
    if len(d.curves)>1:d.remove_curves(indices=list(range(1,len(d.curves))))
    for a in list(d.attributes):
        if a.name not in ('position','radius','curve_type','material_index') and not a.is_required:d.attributes.remove(a)
    d.surface=None;d.materials.clear();d.resize_curves([Q.shape[1]])
    d.add_curves([Q.shape[1]]*(len(Q)-1));d.position_data.foreach_set('vector',Q.astype('f4').ravel())
    a=d.attributes.get('radius') or d.attributes.new('radius','FLOAT','POINT');a.data.foreach_set('value',radii.astype('f4').ravel())
    a=d.attributes.get('curve_type') or d.attributes.new('curve_type','INT8','CURVE');a.data.foreach_set('value',[1]*len(Q))
    a=d.attributes.get('material_index') or d.attributes.new('material_index','INT','CURVE');a.data.foreach_set('value',[0]*len(Q))
    # Existing approved-for-lookdev colour only; character skin/light stay exact.
    d.materials.append(bpy.data.objects['AFN57_CANONICAL_BOB_GUIDES'].data.materials[0])
    ob=bpy.data.objects.new(name,d);bpy.context.scene.collection.objects.link(ob);ob.matrix_world=Matrix.Identity(4)
    return ob

def groom(row,count,pilot=False):
    P=row['V'];T=row['T'];mi=row['mi'];centres=P[T].mean(1)
    select=np.isin(mi,(4,5))&(P[T,2].min(1)>1.365)
    ids=np.flatnonzero(select);tree=BVHTree.FromPolygons(P.tolist(),T[ids].tolist(),all_triangles=True)
    C=np.array((0.,-.038,1.471));axes=np.array((.073,.096,.090))
    rng=np.random.default_rng(61061)
    # Anatomical hairline: high frontal forehead, temples, behind ears, nape.
    # Directions are authored on a scalp atlas, never grown along normals.
    accepted=[]
    while len(accepted)<count:
        az=rng.uniform(-math.pi,math.pi);cosPolar=rng.uniform(-.75,1);theta=math.acos(cosPolar)
        front=(1+math.cos(az))*.5
        limit=2.30-1.20*front**1.35
        limit+=.030*math.sin(5*az+.4)+.015*math.sin(11*az-.5)
        if theta<limit:accepted.append((theta,az))
    atlas=np.array(accepted);theta,az=atlas.T
    directions=np.column_stack((np.sin(theta)*np.sin(az),-np.sin(theta)*np.cos(az),np.cos(theta)))
    gather=np.array((0.,math.sin(1.28),math.cos(1.28)))
    # A slightly spread attachment domain produces a real ponytail tie volume,
    # not all strands passing through a zero-radius shared mathematical pole.
    diskR=.010*np.sqrt(rng.random(count));diskAz=rng.uniform(0,2*math.pi,count)
    tieOffset=np.column_stack((diskR*np.cos(diskAz),np.zeros(count),diskR*np.sin(diskAz)))
    routes=[];rootRows=[];keptAtlas=[];excludedAnatomical=[];clearance=[];N=224
    def surface(direction):
        ray=normalize(np.asarray(direction)*axes);h=tree.ray_cast(Vector(C+ray*.40),Vector(-ray),.65)
        assert h[0] is not None,('Scalp atlas ray missed',direction)
        return np.array(h[0]),np.array(h[1]),int(ids[h[2]])
    baseTie,nTie,_=surface(gather);tie=baseTie+nTie*.034
    for ci,start in enumerate(directions):
        rootFoot,rootNormal,rootTI=surface(start)
        if '--scalp-domain-repair' in sys.argv:
            # Explicit anatomical pinna cutout, fixed from the actual superior
            # helix/ear-base landmarks. Ears are not a hair-bearing scalp.
            # This reauthors the scalp domain, not a failing-root displacement.
            if abs(rootFoot[0])>.063 and -.055<rootFoot[1]<.020 and rootFoot[2]<1.481:
                excludedAnatomical.append({'atlasIndex':ci,'surfacePoint':rootFoot.tolist(),'nativeFace':int(row['nativeTriangleFace'][rootTI]),'reason':'Actual pinna/ear-base region outside authored scalp growth domain.'})
                continue
        # Smooth spherical comb routes evaluated on the actual skin. This is
        # an authored atlas route, NOT a claim of exact intrinsic geodesics.
        end=normalize(gather+np.array((tieOffset[ci,0]*2.5,0,tieOffset[ci,2]*2.5)))
        dot=np.clip(start@end,-1,1);omega=math.acos(dot);s=np.linspace(0,1,81)
        directionsRoute=normalize(np.sin((1-s[:,None])*omega)*start+np.sin(s[:,None]*omega)*end) if omega>1e-5 else np.repeat(start[None],len(s),axis=0)
        xyz=[];rootHit=None
        for j,direction in enumerate(directionsRoute):
            foot,normal,ti=surface(direction)
            if j==0:rootHit=(foot.copy(),ti,normal.copy())
            # Root centre lies on skin; free fibre gradually lifts into its
            # own layer. No arbitrary root relocation to hide a collision.
            lift=.0034*(1-math.exp(-s[j]*15))
            loft=s[j]**7
            xyz.append(foot+normal*lift+(tie+tieOffset[ci]-baseTie-normal*.0034)*loft)
        xyz=np.array(xyz);xyz[-1]=tie+tieOffset[ci]
        u=np.linspace(0,1,101)[1:]
        length=rng.uniform(.225,.315);phase=rng.uniform(0,2*math.pi)
        # The visible loose tail is authored independently of the scalp flow:
        # rearward exit from the tie, then gravity-facing arc and staggered ends.
        tail=np.repeat(xyz[-1,None],len(u),axis=0)
        tail[:,0]+=.012*np.sin(1.5*math.pi*u)*u+.006*np.sin(2*math.pi*u+phase)*u
        tail[:,1]+=.14*u-.065*u*u+.003*np.sin(2*math.pi*u+phase)*u
        tail[:,2]+=.018*u-length*u*u
        tail+=tieOffset[ci][None]*(.65*np.sin(math.pi*u)[:,None])
        full=np.concatenate((xyz,tail));arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(full,axis=0),axis=1))]
        at=np.r_[0,.00025,np.linspace(.0010,arc[-1],N-2)]
        q=np.column_stack([np.interp(at,arc,full[:,axis]) for axis in range(3)])
        # Record exact actual-surface triangle and barycentric root lineage.
        foot,ti,n=rootHit;A=P[T[ti]];w=np.linalg.lstsq((A[1:]-A[0]).T,foot-A[0],rcond=None)[0];bc=np.r_[1-w.sum(),w]
        # BVH ray output is float32 world space. Reconstruct the SAME hit
        # triangle's exact barycentric point; no nearest-body/root fit.
        exactRoot=bc@A
        assert np.linalg.norm(exactRoot-foot)<1e-6 and bc.min()>-1e-4
        q[0]=exactRoot
        routes.append(q);rootRows.append((ti,int(row['nativeTriangleFace'][ti]),*bc));keptAtlas.append(atlas[ci])
        if ci%256==0:print('R61_AUTHORED_SURFACE_FLOW',ci,count,flush=True)
    Q=np.array(routes,dtype='f4');thickness=.00023 if pilot else .000035
    taper=np.minimum(1.,(1-np.linspace(0,1,N))/.13);taper=np.maximum(taper,.06)
    radii=np.tile(thickness*taper,(len(Q),1)).astype('f4')
    return Q,radii,np.array(rootRows),np.array(keptAtlas),{'atlasCentre':C.tolist(),'atlasAxes':axes.tolist(),'tieCentre':tie.tolist(),'rootSelection':'Authored frontal/temporal/ear-back/nape boundary on exact rendered skin, not moved failed roots.','earDomainExclusions':excludedAnatomical,'notCertified':'Hair/self, finite body clearance, animated head-follow and runtime remain separate acceptance gates.'}

def production(row):
    tick=time.time();pilot='--pilot' in sys.argv;count=256 if pilot else 18000
    tag=('b' if '--scalp-domain-repair' in sys.argv else 'a')+('-guides' if pilot else '-fibres')
    out=S/f'aevrynd-female-next-r0061-{tag}-ponytail-study.blend';assert not out.exists()
    save('round-contract.json',{'source':str(SRC),'sha256':SOURCE_SHA,'previousGoalTurnClassification':'progress: user-requested prompt v16 saved/synchronized and GitHub44dbb10verified; no model iteration.',
        'sixLineContract':[
            'Use exact r60B complete coherent character; no live Blender job at start, no unregistered r61 source.',
            'Dominant sparse/incomplete head hair; secondary flat skin response and eye approximations. Select full hairstyle.',
            'Deliver an actually editable complete ponytail, scalp coverage/hairline/ear routes and loose tail on the same woman.',
            'Blender native Curves/scalp guide principle; hand-authored spherical comb routes ray-evaluated on this actual scalp, separate rear tail. No donor Bob, normal-seed Comb or clump shell.',
            'First256editable guide routes in actual complete head/profile/back/body views. Reject incoherent scalp flow, funnels outside intended tie, ear/body crossings or absent full-character benefit before18kfibres.',
            'One heavy job,4threads; diagnostic10min,45min resource checkpoint; one method, no angle/radius/margin sweep.'
        ],'reference':[{'url':'https://www.blender.org/download/releases/3-5/','use':'Separate scalp-attached guide curves and interpolated display structure; our explicit route authoring is original, not an implementation of an undocumented Blender algorithm.'}],
        'pilotIsPhysicalHair':False,'rootAndContactStatus':'Pending actual finite-fibre checks; source ocular evidence retained only if original data/stage invariance verified.'})
    before=k.f.v.stage();Q,radii,roots,atlas,info=groom(row,count,pilot)
    old=bpy.data.objects['AFN57_CANONICAL_BOB_GUIDES'];old.hide_render=True;old.hide_set(True);old['AFN61_role']='Unqualified old Bob preserved hidden for history, not adopted or displayed.'
    ob=create_curves('AFN61_SURFACE_FLOW_PRIMARY_GUIDES' if pilot else 'AFN61_SCALP_ATTACHED_PONYTAIL_FIBRES',Q,radii)
    ob['scope']='Editable STYLE GUIDE preview at enlarged radius, not final hair or collision evidence.' if pilot else 'Actual35um-radius fibre study; finite/self/animated/root-contact acceptance pending. Same-source rendered triangle/barycentric roots in adjacent NPZ.'
    if not pilot:
        # A real, separately editable tie makes the intentional gathered region
        # legible. Contact/compression of tie vs fibres is not yet accepted.
        bpy.ops.mesh.primitive_torus_add(major_radius=.0112,minor_radius=.0016,major_segments=48,minor_segments=8,location=info['tieCentre'],rotation=(math.pi/2,0,0))
        band=bpy.context.object;band.name='AFN61_PONYTAIL_TIE';mat=bpy.data.materials.new('AFN61_NEUTRAL_FABRIC_TIE');mat.use_nodes=True;pr=mat.node_tree.nodes.get('Principled BSDF');pr.inputs['Base Color'].default_value=(.016,.012,.009,1);pr.inputs['Roughness'].default_value=.85;band.data.materials.append(mat)
    assert k.f.v.stage()==before
    np.savez_compressed(E/(tag+'-authoring.npz'),positions=Q,radii=radii,rootTriangles=roots[:,0].astype('i4'),rootNativeFaces=roots[:,1].astype('i4'),rootBarycentric=roots[:,2:],rootAtlas=atlas)
    scene=bpy.context.scene;scene['AFN61_status']='UNACCEPTED_PONYTAIL_GROOM_STYLE_TRIAL' if pilot else 'UNACCEPTED_ACTUAL_FIBRE_STUDY'
    # Restore viewport level; render remains exactly original subdivision2.
    for md in bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'].modifiers:
        if md.type=='SUBSURF':md.levels=1
    k.b.camera('face');scene.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
    save(tag+'-build-summary.json',{'output':str(out),'outputSha256':sha(out),'source':str(SRC),'sourceSha256':SOURCE_SHA,'curves':len(Q),'pointsPerCurve':Q.shape[1],'renderRadiusM':float(radii.max()),'pilot':pilot,'stageUnchanged':True,'skinAndOcularGeometryModified':False,'route':info,'engine':scene.render.engine,'secondsBeforeRenders':time.time()-tick})
    k.f.E=E;k.f.render(tag,('face','profile','oblique'))
    extra_views(tag)
    print('R61_STYLE_PREVIEW_READY',out,time.time()-tick,flush=True)

if __name__=='__main__':
    if '--recover-pilot-views' in sys.argv:
        ref=json.loads((E/'a-guides-build-summary.json').read_text());source=Path(ref['output']);assert sha(source)==ref['outputSha256']
        bpy.ops.wm.open_mainfile(filepath=str(source));extra_views('a-guides')
        save('pilot-view-recovery.json',{'source':str(source),'sha256':sha(source),'sourceOverwritten':False,'reason':'Source and first3renders completed; nested legacy helper lookup failed. Explicit helper import renders only missing views.'})
    else:
        start=time.time();body,row=load();print('R61_SURFACE_READY',time.time()-start,flush=True)
        if '--pilot' in sys.argv or '--fibres' in sys.argv:production(row)
