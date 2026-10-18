"""Route whole strand segments outside the closed body with conservative capsules."""
import bpy,json,hashlib,importlib.util,numpy as np,math
from pathlib import Path
from mathutils import Vector
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0012-layered-hair';S=R/'engine/assets/characters/female-next/source'
spec=importlib.util.spec_from_file_location('certificate',Path(__file__).with_name('verify-female-next-r0012-hair-segments.py'));cert=importlib.util.module_from_spec(spec);spec.loader.exec_module(cert)
SRC=S/'aevrynd-female-next-r0012-b-volume-hair-study.blend';bpy.ops.wm.open_mainfile(filepath=str(SRC));rig=bpy.data.objects['AFN_R0005_Rig'];cert.solid.stage.set_pose(rig,'neutral');body=bpy.data.objects['AFN_R0008_Body'];V,T,tree=cert.solid.data(body);tri=np.asarray([tuple(v) for v in V],dtype=np.float64)[np.asarray(T,dtype=np.int32)]
summary=[];allP=[];allR=[];allT=[];offsets=[0];guideP=[];guideR=[];guideT=[];guideOffsets=[0];details=[];unresolved=[]

def exterior(p,r,margin=.00055):
    p=np.asarray(p,dtype=np.float64);hit,n,fi,d=tree.find_nearest(Vector(p));signed=(Vector(p)-hit).dot(n)
    if d>r+.000012 and (signed>=0 or cert.solid.classify(tree,tri,Vector(p))=='outside'):return p,d
    for multiplier in (1.,2.,4.,8.,16.):
        q=hit+n*(r+margin*multiplier);h,nn,face,dq=tree.find_nearest(q)
        if dq>r+.000012 and cert.solid.classify(tree,tri,q)=='outside':return np.array(q),dq
    raise RuntimeError('Cannot establish an exterior strand point')

def route(A,B,ra,rb,ta,tb,da,db,depth=0):
    gap,kind=cert.segment_test(A,B,da,db,max(ra,rb),tree,tri)
    if gap>0:return [(A,ra,ta),(B,rb,tb)],0
    if depth>=12:return [(A,ra,ta),(B,rb,tb)],1
    mid=(A+B)*.5;rm=(ra+rb)*.5;tm=(ta+tb)*.5;mid,dm=exterior(mid,rm)
    left,bad1=route(A,mid,ra,rm,ta,tm,da,dm,depth+1);right,bad2=route(mid,B,rm,rb,tm,tb,dm,db,depth+1)
    return left[:-1]+right,bad1+bad2

objects=sorted((o for o in bpy.data.objects if o.type=='CURVE' and o.name.startswith('AFN12_')),key=lambda o:o.name)
for obj in objects:
    old=obj.data;data=bpy.data.curves.new(obj.name+'-segment-corrected','CURVE');data.dimensions='3D';data.resolution_u=1;data.bevel_depth=old.bevel_depth;data.bevel_resolution=old.bevel_resolution;data.use_fill_caps=True;data.twist_mode='MINIMUM'
    for m in old.materials:data.materials.append(m)
    added=0;bad=0;max_shift=0.;repaired_curves=0
    for ci,spline in enumerate(old.splines):
        original=np.array([p.co[:3] for p in spline.points],dtype=np.float64);rs=np.array([p.radius*old.bevel_depth for p in spline.points]);ts=np.linspace(0,1,len(original));P=[];ds=[]
        for p,r in zip(original,rs):
            q,d=exterior(p,r);max_shift=max(max_shift,float(np.linalg.norm(q-p)));P.append(q);ds.append(d)
        path=[];curve_bad=0
        for j in range(len(P)-1):
            segment,fail=route(P[j],P[j+1],rs[j],rs[j+1],ts[j],ts[j+1],ds[j],ds[j+1]);path+=segment if not path else segment[1:];curve_bad+=fail
        newP=np.asarray([p for p,r,t in path],dtype=np.float32);newR=np.asarray([r for p,r,t in path],dtype=np.float32);newT=np.asarray([t for p,r,t in path],dtype=np.float32)
        extra=len(path)-len(original);added+=extra;repaired_curves+=extra>0;bad+=curve_bad
        sp=data.splines.new('POLY');sp.points.add(len(path)-1);sp.points.foreach_set('co',np.column_stack((newP,np.ones(len(path)))).astype(np.float32).ravel());sp.points.foreach_set('radius',(newR/data.bevel_depth).astype(np.float32));sp.material_index=spline.material_index
        if curve_bad:unresolved.append({'object':obj.name,'curve':ci,'badSegments':curve_bad})
        if extra:details.append({'object':obj.name,'curve':ci,'insertedPoints':extra})
        if obj.hide_render:guideP.extend(newP);guideR.extend(newR);guideT.extend(newT);guideOffsets.append(len(guideP))
        else:allP.extend(newP);allR.extend(newR);allT.extend(newT);offsets.append(len(allP))
    obj.data=data;obj['aevrynd_revision']='female-next-r0012-c-corrected-hair';obj['aevrynd_collision_basis']='Actual POLY segment capsules; adaptive routing, not CV-only projection.'
    row={'object':obj.name,'curves':len(data.splines),'insertedPoints':added,'reroutedCurves':repaired_curves,'unresolvedSegments':bad,'maximumOriginalPointShiftM':max_shift};summary.append(row);print('AFN_R0012_ROUTE='+json.dumps(row),flush=True)
(E/'c-segment-routing.json').write_text(json.dumps({'source':str(SRC),'sourceSha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'layers':summary,'modifiedCurves':details,'unresolved':unresolved,'maximumSubdivisionDepth':12,'method':'Conservative segment capsule test. Failed segments split at their midpoint; penetrating or too-close midpoint moved to a verified exterior skin offset; recursively re-test both complete subsegments. Original roots kept when already valid.'},indent=2)+'\n')
data_path=S/'aevrynd-female-next-r0012-c-hair-data.npz';np.savez_compressed(data_path,positions=np.asarray(allP,dtype=np.float32),radii=np.asarray(allR,dtype=np.float32),strandT=np.asarray(allT,dtype=np.float32),offsets=np.asarray(offsets,dtype=np.int32),guidePositions=np.asarray(guideP,dtype=np.float32),guideRadii=np.asarray(guideR,dtype=np.float32),guideT=np.asarray(guideT,dtype=np.float32),guideOffsets=np.asarray(guideOffsets,dtype=np.int32))
fits=cert.solid.stage.eyes.helper_centres();cert.solid.stage.eyes.E=E;images=[cert.solid.stage.eyes.render('c-corrected-hair',v,fits,'neutral') for v in ('face','oblique','profile')]
scene=bpy.context.scene;scene['aevrynd_revision']='female-next-r0012-c-corrected-hair';scene['aevrynd_release_state']='HAIR_SEGMENT_RESEARCH_PENDING_INDEPENDENT_VERIFICATION';dest=S/'aevrynd-female-next-r0012-c-corrected-hair-study.blend';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(dest))
report=json.loads((E/'female-next-r0012-b-volume-hair.report.json').read_text());report.update({'variant':'c-corrected-hair','output':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'repairInput':str(SRC),'repairInputSha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'hairData':str(data_path),'hairDataSha256':hashlib.sha256(data_path.read_bytes()).hexdigest(),'hairControlPoints':len(allP),'renders':images,'routingSummary':summary,'routingUnresolvedSegments':sum(x['badSegments'] for x in unresolved),'dataSchema':'Flat positions/radii/strandT plus offsets, variable-length POLY curves; source b interpolation weights remain available in its companion NPZ.','status':'PENDING_INDEPENDENT_VERIFICATION'})
(E/'female-next-r0012-c-corrected-hair.report.json').write_text(json.dumps(report,indent=2)+'\n');print('AFN_R0012_ROUTE_DONE')
