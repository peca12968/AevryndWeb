"""One source-grounded dental seating correction with coupled oral soft tissue."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,time,sys,importlib.util
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0075-occlusion-authoring';OLD=E.parent/'r0074-oral-controls'
SRC=S/'aevrynd-female-next-r0074-c-rigid-dentition-controls-study.blend';OUT=S/'aevrynd-female-next-r0075-a-seated-occlusion-study.blend';SRC_SHA='19d5d5ed6ae55edcd625c5ce8f342029c53efacd4a2a964573e0dc1654778294'
CELL=.00025;GUARD=.00005
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2)+'\n',encoding='utf8',newline='\n')
def arrays(o):
    d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;p=np.empty((len(d.vertices),3),'f4');d.vertices.foreach_get('co',p.ravel());a=np.array(o.matrix_world);p=p.astype('f8')@a[:3,:3].T+a[:3,3];d.calc_loop_triangles();t=np.array([v.vertices[:] for v in d.loop_triangles],dtype='i4');return d,p,t
def raster_bounds(vmin,vmax,t,origin,shape,mode):
    lo=np.floor((vmin[t].min(1)[:,:2]-origin)/CELL).astype('i4');hi=np.floor((vmax[t].max(1)[:,:2]-origin)/CELL).astype('i4');lo=np.maximum(lo,0);hi=np.minimum(hi,np.array(shape)-1);valid=np.all(lo<=hi,axis=1);lo=lo[valid];hi=hi[valid];z=(vmin[t][:,:,2].min(1) if mode=='min' else vmax[t][:,:,2].max(1))[valid]
    grid=np.full(int(np.prod(shape)),np.inf if mode=='min' else -np.inf);operation=np.minimum.at if mode=='min' else np.maximum.at
    for dx in range(int((hi[:,0]-lo[:,0]).max())+1):
        ix=np.flatnonzero(lo[:,0]+dx<=hi[:,0])
        for dy in range(int((hi[ix,1]-lo[ix,1]).max())+1):
            use=ix[lo[ix,1]+dy<=hi[ix,1]];cells=(lo[use,0]+dx)*shape[1]+lo[use,1]+dy;operation(grid,cells,z[use])
    return grid
def preflight():
    assert sha(SRC)==SRC_SHA;bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();ud,u,ut=arrays(bpy.data.objects['AFN74_UPPER_TEETH_RIGID']);ld,l,lt=arrays(bpy.data.objects['AFN74_LOWER_TEETH_RIGID'])
    charts=[v for v in json.loads((OLD/'source-oral-uv-islands.json').read_text())[3:] if v['jawAffected']>0];assert len(charts)==16;lookup={int(f):i for i,c in enumerate(charts) for f in c['faces']};fids=np.array([x.value for x in ld.attributes['AFN60_NativeFaceID'].data]);triangle_tooth=np.array([lookup[int(fids[t.polygon_index])] for t in ld.loop_triangles]);point_tooth=np.full(len(l),-1,'i4')
    for i in range(16):
        ids=np.unique(lt[triangle_tooth==i]);assert np.all((point_tooth[ids]<0)|(point_tooth[ids]==i));point_tooth[ids]=i
    assert point_tooth.min()>=0;origin=np.floor(u[:,:2].min(0)/CELL)*CELL-CELL;shape=np.ceil((u[:,:2].max(0)-origin)/CELL).astype('i4')+2;upper=raster_bounds(u,u,ut,origin,shape,'min');deltas=[];rows=[]
    for i in range(16):
        lower=raster_bounds(l,l,lt[triangle_tooth==i],origin,shape,'max');active=np.isfinite(upper)&np.isfinite(lower);assert active.any();overlap=float((lower[active]-upper[active]).max());delta=max(0.,overlap+GUARD);assert delta<.004,('Seating exceeds bounded anatomy assumption; stop',i,delta);deltas.append(delta);rows.append({'tooth':i,'nativeUVIsland':charts[i],'conservativeVerticalOverlapUpperBoundM':overlap,'authoredDownwardSeatingM':delta})
    deltas=np.array(deltas);corrected=l.copy();corrected[:,2]-=deltas[point_tooth];lower=raster_bounds(corrected,corrected,lt,origin,shape,'max');active=np.isfinite(upper)&np.isfinite(lower);gap=float((upper[active]-lower[active]).min());assert gap>=GUARD-1e-12
    np.savez_compressed(E/'rest-seating-data.npz',upper=u,upperTriangles=ut,lower=l,lowerTriangles=lt,pointTooth=point_tooth,triangleTooth=triangle_tooth,downwardSeating=deltas,origin=origin,shape=shape,upperMinimum=upper)
    save('rest-seating-preflight.json',{'source':str(SRC),'sourceSha256':SRC_SHA,'method':'Conservative actual finite-triangle XY cell envelopes. Each occupied cell stores minimum upper vertex height and maximum lower vertex height over every triangle whose full XY AABB overlaps it.','cellWidthM':CELL,'guardM':GUARD,'minimumCertifiedRestVerticalSeparationM':gap,'notGlobalEuclideanOrSignedDistance':True,'noSizeOrClosedAngleChanges':True,'perTooth':rows});print('R75_REST_DECISION',deltas.tolist(),'guaranteedDirectionalGap',gap,flush=True)
def coordinate(global_arch=False):
    import bmesh
    assert sha(SRC)==SRC_SHA;bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();ud,u,ut=arrays(bpy.data.objects['AFN74_UPPER_TEETH_RIGID']);ld,l,lt=arrays(bpy.data.objects['AFN74_LOWER_TEETH_RIGID']);charts=json.loads((OLD/'source-oral-uv-islands.json').read_text())[3:];lowercharts=[v for v in charts if v['jawAffected']>0];uppercharts=[v for v in charts if v['jawAffected']==0]
    def classify(d,t,rows):
        lookup={int(f):i for i,c in enumerate(rows) for f in c['faces']};fids=np.array([v.value for v in d.attributes['AFN60_NativeFaceID'].data]);tc=np.array([lookup[int(fids[v.polygon_index])] for v in d.loop_triangles]);pc=np.full(len(d.vertices),-1,'i4')
        for i in range(16):
            ids=np.unique(t[tc==i]);assert np.all((pc[ids]<0)|(pc[ids]==i));pc[ids]=i
        assert pc.min()>=0;return pc,tc
    upc,utc=classify(ud,ut,uppercharts);lpc,ltc=classify(ld,lt,lowercharts);hulls=[]
    for i in range(16):
        points=u[upc==i];bm=bmesh.new()
        for p in points:bm.verts.new(p)
        bmesh.ops.convex_hull(bm,input=list(bm.verts),use_existing_faces=False);bm.normal_update();center=points.mean(0);normals=[]
        for f in bm.faces:
            n=np.array(f.normal,dtype='f8');n/=np.linalg.norm(n)
            if np.dot(np.array(f.verts[0].co)-center,n)<0:n=-n
            normals.append(n)
        bm.free();normals=np.unique(np.r_[np.round(normals,8),np.eye(3),-np.eye(3)],axis=0);normals/=np.linalg.norm(normals,axis=1)[:,None];support=(points@normals.T).max(0);hulls.append((normals,support,points.min(0),points.max(0)))
    if global_arch:
        direction=np.array([0.,1.,-.5]);direction/=np.linalg.norm(direction);gaps=[[(l[lpc==i]@n.T).min(0)-support for n,support,_,_ in hulls] for i in range(16)];distance=0.;steps=[]
        for iteration in range(16):
            required=[]
            for i in range(16):
                for j,(n,_,_,_) in enumerate(hulls):
                    rate=n@direction;gap=gaps[i][j]+distance*rate
                    if gap.max()>=GUARD:continue
                    ok=rate>1e-8;required.append((float(((GUARD-gap[ok])/rate[ok]).min()),i,j))
            if not required:break
            amount,i,j=max(required);distance+=amount+1e-7;steps.append({'lowerTooth':i,'upperTooth':j,'additionalShiftM':amount});assert distance<.0035,('Whole arch rest coordination exceeded bounded anatomical edit',distance)
        else:raise AssertionError('No defensible coordinated whole-arch solution')
        shifts=np.tile(direction*distance,(16,1));certificates=[[{'upperTooth':j,'lowerBoundEuclideanGapM':float((gaps[i][j]+distance*(hulls[j][0]@direction)).max())} for j in range(16)] for i in range(16)];assert min(v['lowerBoundEuclideanGapM'] for row in certificates for v in row)>=GUARD-1e-10
        rows=[{'tooth':i,'nativeUVIsland':lowercharts[i],'worldRestShiftM':shifts[i].tolist(),'direction':'One coherent rigid whole-arch lingual/inferior rest placement; every inter-tooth relation preserved.'} for i in range(16)]
        np.savez_compressed(E/'whole-arch-seating-data.npz',upper=u,upperTriangles=ut,upperPointTooth=upc,lower=l,lowerTriangles=lt,pointTooth=lpc,triangleTooth=ltc,worldRestShifts=shifts)
        save('whole-arch-seating-preflight.json',{'source':str(SRC),'sourceSha256':SRC_SHA,'method':'One whole-arch rigid rest translation, fixed lingual/inferior direction, conservative supporting planes remeasured on all actual upper vertices. Preserves original tooth-to-tooth positions.','guardM':GUARD,'worldWholeArchShiftM':shifts[0].tolist(),'placementSteps':steps,'minimumRestActualSurfaceDistanceLowerBoundM':min(v['lowerBoundEuclideanGapM'] for row in certificates for v in row),'notActualGlobalMinimumOrSignedDistance':True,'perTooth':rows,'all256ToothPairCertificates':certificates});print('R75_WHOLE_ARCH_AUTHORING',distance,shifts[0].tolist(),flush=True);return
    center=np.array([0.,max(l[lpc==i,1].mean() for i in range(16))+.015]);shifts=[];rows=[];certificates=[]
    for i in range(16):
        p=l[lpc==i];radial=p[:,:2].mean(0)-center;inward=-radial/np.linalg.norm(radial);direction=np.r_[inward,-.5];direction/=np.linalg.norm(direction);distance=0.;steps=[]
        for iteration in range(12):
            q=p+distance*direction;needs=[]
            for j,(normals,support,lo,hi) in enumerate(hulls):
                if max(float((q.min(0)-hi).max()),float((lo-q.max(0)).max()))>=GUARD:continue
                gap=(q@normals.T).min(0)-support
                if gap.max()>=GUARD:continue
                rate=normals@direction;ok=rate>1e-8;required=float(((GUARD-gap[ok])/rate[ok]).min());needs.append((required,j))
            if not needs:break
            amount,j=max(needs);distance+=amount+1e-7;steps.append({'opposingUpperTooth':j,'additionalShiftM':amount});assert distance<.0025,('Lingual seating exceeds bounded edit',i,distance)
        else:raise AssertionError('Source arch cannot be coordinated with this anatomical direction')
        shift=distance*direction;shifts.append(shift);q=p+shift;paircert=[]
        for j,(normals,support,lo,hi) in enumerate(hulls):
            axisgap=max(float((q.min(0)-hi).max()),float((lo-q.max(0)).max()));gap=(q@normals.T).min(0)-support;bound=max(axisgap,float(gap.max()));assert bound>=GUARD-1e-10;paircert.append({'upperTooth':j,'lowerBoundEuclideanGapM':bound})
        certificates.append(paircert);rows.append({'tooth':i,'nativeUVIsland':lowercharts[i],'worldRestShiftM':shift.tolist(),'direction':'Lingual and inferior, fixed by source arch center and source contact geometry, no tooth scaling or jaw-angle edit','supportingPlanePlacementSteps':steps})
    np.savez_compressed(E/'rest-seating-data.npz',upper=u,upperTriangles=ut,upperPointTooth=upc,lower=l,lowerTriangles=lt,pointTooth=lpc,triangleTooth=ltc,worldRestShifts=np.array(shifts))
    save('rest-seating-preflight.json',{'source':str(SRC),'sourceSha256':SRC_SHA,'method':'Per-tooth lingual/inferior rest coordination using conservative convex supporting planes; supports remeasured on every actual upper vertex. Each full lower tooth must be separated from every upper tooth by an actual supporting plane or AABB axis.','rejectedMethod':'Vertical-only ordering required over4.45mm for an anterior crown and was rejected before authoring; no increased threshold or vertical-placement sweep.','guardM':GUARD,'minimumRestActualSurfaceDistanceLowerBoundM':min(v['lowerBoundEuclideanGapM'] for row in certificates for v in row),'notActualGlobalMinimumOrSignedDistance':True,'perTooth':rows,'all256ToothPairCertificates':certificates});print('R75_LINGUAL_COORDINATION_DECIDED',np.linalg.norm(shifts,axis=1).tolist(),flush=True)
def author(global_arch=False):
    out=OUT if not global_arch else S/'aevrynd-female-next-r0075-b-coordinated-arch-study.blend';tag='a' if not global_arch else 'b';prefix='rest' if not global_arch else 'whole-arch'
    assert not out.exists() and sha(SRC)==SRC_SHA;data=np.load(E/(prefix+'-seating-data.npz'),allow_pickle=False);ref=json.loads((E/(prefix+'-seating-preflight.json')).read_text());bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();lower=bpy.data.objects['AFN74_LOWER_TEETH_RIGID'];p=data['lower']+data['worldRestShifts'][data['pointTooth']];a=np.array(lower.matrix_world);inv=np.linalg.inv(a);local=p@inv[:3,:3].T+inv[:3,3];assert len(local)==len(lower.data.vertices);lower.data.vertices.foreach_set('co',local.astype('f4').ravel());lower.data.update()
    body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];d=body.data;n=len(d.vertices);native=np.array([x.value for x in d.attributes['AFN60_NativeVertexID'].data]);native_to_local={int(v):i for i,v in enumerate(native)};oral=np.zeros(n,bool);skin=np.zeros(n,bool)
    for face in d.polygons:
        if 'CANONICAL_MOUTH' in d.materials[face.material_index].name:oral[list(face.vertices)]=True
        else:skin[list(face.vertices)]=True
    edge=np.array([v.vertices[:] for v in d.edges]);frozen=skin.copy()
    for _ in range(4):
        neighbors=np.any(frozen[edge],axis=1);frozen[np.unique(edge[neighbors])]=True
    field=np.zeros((n,3));fixed=~oral|frozen;seed=np.zeros(n,bool)
    for row in ref['perTooth']:
        ids=np.array([native_to_local[int(i)] for i in row['nativeUVIsland']['nativeIDs']]);assert not frozen[ids].any(),('Dental pins touch frozen skin boundary',row['tooth']);assert not seed[ids].any();seed[ids]=True;fixed[ids]=True;field[ids]=row['worldRestShiftM']
    upper_native={v for row in json.loads((OLD/'source-oral-uv-islands.json').read_text())[3:] if row['jawAffected']==0 for v in row['nativeIDs']};upperids=[native_to_local[int(v)] for v in upper_native];fixed[upperids]=True;field[upperids]=0
    if global_arch:
        support=set()
        for row in json.loads((OLD/'source-oral-uv-islands.json').read_text())[1:3]:support.update(row['nativeIDs'])
        pin=np.zeros(n,bool);pin[[native_to_local[int(v)] for v in support]]=True
        for _ in range(4):
            touched=np.any(pin[edge],axis=1);pin[np.unique(edge[touched])]=True;pin &=oral&~frozen;pin[upperids]=False
        assert pin.any();seed |=pin;fixed[pin]=True;field[pin]=data['worldRestShifts'][0]
    keybase=np.array([v.co[:] for v in d.shape_keys.key_blocks[0].data]);current=keybase.copy()
    for k in d.shape_keys.key_blocks[1:]:current+=(np.array([v.co[:] for v in k.data])-keybase)*k.value
    e=edge[np.all(oral[edge],axis=1)];length=np.linalg.norm(current[e[:,1]]-current[e[:,0]],axis=1);weight=1/np.maximum(length,1e-8);degree=np.bincount(np.r_[e[:,0],e[:,1]],weights=np.r_[weight,weight],minlength=n);free=oral&~fixed&(degree>0);iterations=0;residual=0.
    for iterations in range(1000):
        sums=np.stack([np.bincount(np.r_[e[:,0],e[:,1]],weights=np.r_[weight*field[e[:,1],j],weight*field[e[:,0],j]],minlength=n) for j in range(3)],axis=1);new=sums[free]/degree[free,None];residual=float(np.max(np.abs(new-field[free])));field[free]=new
        if residual<1e-9:break
    assert np.isfinite(field).all() and not np.any(field[skin]);axis=np.array(json.loads((OLD/'c-build-summary.json').read_text())['rigidFit']['axis']);axis/=np.linalg.norm(axis);angle=json.loads((OLD/'c-build-summary.json').read_text())['rigidFit']['angleRadians'];v=field;parallel=(v@axis)[:,None]*axis;components={'PARALLEL':parallel,'COS':v-parallel,'SIN':np.cross(axis,v)};inverse=np.linalg.inv(np.array(body.matrix_world)[:3,:3]);ctrl=bpy.data.objects['AFN74_ORAL_CONTROLS']
    for name,values in components.items():
        delta=values@inverse.T;k=body.shape_key_add(name='AFN75_GINGIVA_BITE_'+name,from_mix=False);k.relative_key=d.shape_keys.key_blocks[0];k.data.foreach_set('co',(keybase+delta).astype('f4').ravel());k.slider_min=-1;k.slider_max=1
        if name=='PARALLEL':k.value=1
        else:
            dr=k.driver_add('value').driver;dr.type='SCRIPTED';dr.expression=('cos' if name=='COS' else 'sin')+'('+repr(float(angle))+'*jaw)';var=dr.variables.new();var.name='jaw';var.type='SINGLE_PROP';var.targets[0].id=ctrl;var.targets[0].data_path='["jaw_open"]'
    np.savez_compressed(E/(tag+'-authored-oral-field.npz'),nativeVertexIDs=native,worldRestField=field,dentalPins=seed,frozenSkinBoundary=frozen)
    ctrl['AFN75_scope']=('One coherent whole-arch rest seating with pinned tongue/lower gum support and smooth oral transition.' if global_arch else 'Per-tooth rest seating plus source-indexed smooth oral support field.')+' Existing full opening angle unchanged. Actual contact/continuous/gum seating acceptance requires independent evidence.';s['AFN75_scope']='One complete anatomical occlusion-seating candidate;16 rigid lower crowns retained, no tooth resizing or jaw amplitude change; source body topology/scalp reference preserved.'
    sp=importlib.util.spec_from_file_location('oral75render',Path(__file__).with_name('build-female-next-r0074-oral-controls.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);m.E=E;m.m.shade.g.E=E;s.frame_set(1);bpy.context.view_layer.update();m.m.k.b.camera('face');s.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
    save(tag+'-build-summary.json',{'source':str(SRC),'sourceSha256':SRC_SHA,'output':str(out),'outputSha256':sha(out),'outputBytes':out.stat().st_size,'wholeArchCoherent':global_arch,'maximumSeatingM':float(np.linalg.norm(data['worldRestShifts'],axis=1).max()),'perToothWorldRestShiftsM':data['worldRestShifts'].tolist(),'constrainedFieldRelaxationIterations':iterations+1,'fieldLastUpdateM':residual,'convergedToRequested1nmUpdate':residual<1e-9,'positiveDentalPins':int(seed.sum()),'frozenSourceVertices':int(frozen.sum()),'newBodyTopologyOrRadiusOrPigmentOrLightingChanges':False,'jawOpeningAngleRadiansUnchanged':angle,'globalContactNaturalDynamicsRuntimeAccepted':False})
    rows=[]
    for frame,label in ((1,tag+'-neutral'),(13,tag+'-open')):
        s.frame_set(frame);bpy.context.view_layer.update();rows += [m.render(label,'face'),m.render(label,'body-face')]
    save(tag+'-pilot-controls.json',rows);print('R75_COMPLETE_SEATING_CANDIDATE_AND_PILOTS_DONE',tag,flush=True)
if __name__=='__main__':
    if '--coordinate-whole' in sys.argv:coordinate(True)
    elif '--whole-arch' in sys.argv:author(True)
    elif '--coordinate' in sys.argv:coordinate()
    elif '--inspect' in sys.argv:preflight()
    else:author()
