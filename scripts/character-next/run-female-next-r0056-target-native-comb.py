"""One target-native full-head Comb trial through Blender's own modal API.

64 retained actual-skin follicles, no donor route or old r48 target stations.
Native collision/length response shapes a new normal seed using section-aware
sculpt directions. The tool flag is not independent contact evidence.
No desktop keyboard/mouse injection; only this Blender process's event queue.
"""
from pathlib import Path
import bpy,importlib.util,numpy as np,json,time,traceback,sys
from mathutils import Vector,Matrix
from bpy_extras.view3d_utils import location_3d_to_region_2d
sp=importlib.util.spec_from_file_location('target56',Path(__file__).with_name('build-female-next-r0054-clump-volume.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
b=k.b;f=k.f;SRC=k.SRC;E=b.R/'Evidence/character-female-next/r0056-target-native-comb';E.mkdir(parents=True,exist_ok=True)
WHOLE='--whole-curve-pilot' in sys.argv
TAG='b-pilot' if WHOLE else 'a'
OUT=b.S/('aevrynd-female-next-r0056-'+TAG+'-target-native-comb.blend');NAME='AFN56_TARGET_NATIVE_MASTER_CURVES';state={}
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def fail():
    error=traceback.format_exc();print(error,flush=True);save('native-session.json',{'status':'SCRIPT_ERROR','error':error,'strokes':state.get('logs',[])})
    bpy.ops.wm.quit_blender()

def init():
    try:
        assert Path(bpy.data.filepath)==SRC and b.sha(SRC)=='c293976b2745e372565eb990f2e844a8255f2cdaad8e004563643d0f51c9f537'
        before=f.state();source=bpy.data.objects['AFN53_NEW_PRIMARY_CURVES'];Q,R=f.v.hair_arrays(source)
        foundation=np.load(b.R/'Evidence/character-female-next/r0053-new-primary-groom/refined-foundation-data.npz')
        normals=foundation['normals'];assert np.array_equal(Q[:,0],foundation['initialPaths'][:,0].astype('f4'))
        L=.095+1.20*(Q[:,0,2]-1.43);P=(Q[:,0,None]+normals[:,None]*L[:,None,None]*np.linspace(0,1,128)[None,:,None]).astype('f4');P[:,0]=Q[:,0]
        d=source.data.copy();d.name=NAME;d.position_data.foreach_set('vector',P.ravel())
        for attr in list(d.attributes):
            if attr.name.startswith('.selection'):d.attributes.remove(attr)
        d.attributes.new('.selection','FLOAT','CURVE')
        o=bpy.data.objects.new(NAME,d);bpy.context.scene.collection.objects.link(o);o.matrix_world=Matrix.Identity(4)
        for obj in bpy.context.view_layer.objects:obj.select_set(False)
        o.hide_set(False);o.select_set(True);bpy.context.view_layer.objects.active=o
        d.surface=bpy.data.objects[b.BODY];d.surface_uv_map=d.surface.data.uv_layers[0].name;d.use_sculpt_collision=True;d.surface_collision_distance=.00010
        assert d.attributes['surface_uv_coordinate'].data_type=='FLOAT2'
        bpy.ops.object.mode_set(mode='SCULPT_CURVES')
        bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS',relative_asset_identifier='brushes/essentials_brushes-curve_sculpt.blend/Brush/Comb')
        area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
        with bpy.context.temp_override(area=area,region=region):bpy.ops.wm.tool_set_by_id(name='builtin.brush')
        brush=bpy.context.scene.tool_settings.curves_sculpt.brush;brush.use_pressure_size=False;brush.use_pressure_strength=False;brush.falloff_shape='SPHERE';brush.use_locked_size='VIEW';brush.size=115;brush.strength=.85
        unified=bpy.context.scene.tool_settings.curves_sculpt.unified_paint_settings;unified.use_unified_size=False;unified.use_unified_strength=False
        order=list(range(64))
        if WHOLE:
            roots=P[:,0];order=sorted(set(int(fn(roots[:,axis])) for axis in range(3) for fn in (np.argmin,np.argmax)))
            # Add side-specific crown roots to the six extrema where distinct.
            for side in (-1,1):
                ids=np.flatnonzero(roots[:,0]*side>0);order.append(int(ids[np.argmax(roots[ids,2])]))
            order=sorted(set(order));brush.falloff_shape='PROJECTED';brush.strength=1.
        state.update(o=o,P=P,R=R,normals=normals,before=before,area=area,region=region,window=bpy.context.window,brush=brush,curve=0,phase=0,point=-2,logs=[],start=time.time(),order=order)
        save(TAG+'-round-contract.json',{'revision':'female-next-r0056','previousGoalTurnClassification':'progress: r54/r55 rejected with actual full views, body capsules and exact archived history5c3188b; no appearance gain.',
            'source':str(SRC),'sourceSha256':b.sha(SRC),'mainDefect':'Complete natural crown-to-side/back guide flow absent',
            'productionDecision':'Use existing64actual target scalp follicles with new normal seeds and native Comb. Root-adjacent tangential, middle and distal downward strokes, with native length/collision response, replace copied station/donor trajectories.',
            'referenceScope':'Prior actual authored Bob views inform only the crown/side/back direction; no source path/root geometry copied. Existing native Comb API and effective-settings correction reused only as tools.',
            'minimumTest':('Small extrema/crown pilot with physically calculated whole-curve brush coverage. Not a complete hairstyle; reject local kinks/radial flow before a full64master trial.' if WHOLE else 'One complete64guide actual head/body/multiangle/second-light preview; no children. If coarse form succeeds, independently test all finite paths and affected pairs.'),
            'reject':['Outward root arches/roof or radial spikes remain','Hard turns, helmet or incoherent full silhouette','No readable natural whole-head flow'],
            'candidateCount':1,'nativeStrokes':len(order)*(3 if WHOLE else 4),'wholeCurveCoveragePilot':WHOLE,'sourceCurveIndices':order,'resourceLimit':'4threads,one hidden Blender job; first actual preview/checkpoint within45minutes; no parameter sweep'})
        bpy.app.timers.register(step,first_interval=.25)
    except Exception:fail()

def step():
    try:
        cursor=state['curve'];phase=state['phase'];o=state['o'];area=state['area'];region=state['region'];window=state['window']
        if cursor==len(state['order']):finish();return None
        ci=state['order'][cursor]
        if state['point']==-2:
            weights=np.zeros(64,dtype='f4');weights[ci]=1;o.data.attributes['.selection'].data.foreach_set('value',weights);o.data.update_tag();bpy.context.view_layer.update()
            Q,_=f.v.hair_arrays(o);n=state['normals'][ci];root=Q[ci,0];gravity=np.array([0.,0.,-1.]);side=1 if root[0]>=0 else -1
            tangent=gravity-n*np.dot(gravity,n)
            if n[2]>.88 or n[1]<-.25:
                desired=np.array([side,0.,-.25]);tangent=desired-n*np.dot(desired,n)
            tangent/=max(np.linalg.norm(tangent),1e-12)
            index=(18,50,92,123)[phase];delta=(tangent*.030,tangent*.055+gravity*.025,gravity*.095,gravity*.075)[phase]
            if WHOLE:
                index=(50,92,120)[phase];delta=(tangent*.120,gravity*.220,gravity*.110)[phase]
            start=Q[ci,index].astype('f8');end=start+delta
            outward=np.cross(n,delta)
            if np.linalg.norm(outward)<1e-5:outward=np.array([0.,-1.,0.])
            outward=Vector(outward).normalized();rv=area.spaces.active.region_3d;area.spaces.active.clip_start=.001
            rv.view_rotation=(-outward).to_track_quat('-Z','Y');rv.view_location=Vector((start+end)*.5);rv.view_distance=.60;rv.view_perspective='ORTHO';rv.update();area.tag_redraw()
            physicalRadius=None
            if WHOLE:
                physicalRadius=float(np.linalg.norm(Q[ci]-start,axis=1).max())*1.8
                right=rv.view_rotation@Vector((1.,0.,0.));c=location_3d_to_region_2d(region,rv,Vector(start));r=location_3d_to_region_2d(region,rv,Vector(start)+right*physicalRadius)
                requested=int(np.ceil((r-c).length));limit=state['brush'].bl_rna.properties['size'].hard_max
                assert requested<=limit,('Physical brush coverage exceeds native size limit',requested,limit)
                state['brush'].size=max(1,requested)
            world=start[None]+np.linspace(0,1,21)[:,None]*delta[None];pixel=[location_3d_to_region_2d(region,rv,Vector(p)) for p in world]
            assert all(p is not None and 5<p.x<region.width-5 and 5<p.y<region.height-5 for p in pixel)
            state['path']=[(int(p.x+region.x),int(p.y+region.y)) for p in pixel];state['gesture']={'curve':ci,'phase':phase,'controlIndex':index,'startM':start.tolist(),'deltaM':delta.tolist(),'normal':n.tolist(),'view':list(outward),'size':state['brush'].size,'strength':state['brush'].strength,'physicalCoverageRadiusM':physicalRadius,'regionSize':[region.width,region.height]};state['point']=-1;return .08
        if state['point']==-1:
            x,y=state['path'][0];window.event_simulate(type='MOUSEMOVE',value='NOTHING',x=x,y=y);window.event_simulate(type='LEFTMOUSE',value='PRESS',x=x,y=y);state['point']=0;return .04
        pi=state['point']
        if pi<len(state['path']):
            x,y=state['path'][pi];window.event_simulate(type='MOUSEMOVE',value='NOTHING',x=x,y=y);state['point']+=1;return .020
        if pi==len(state['path']):
            x,y=state['path'][-1];window.event_simulate(type='LEFTMOUSE',value='RELEASE',x=x,y=y);state['point']+=1;return .10
        Q,RR=f.v.hair_arrays(o);assert np.array_equal(Q[:,0],state['P'][:,0]) and np.array_equal(RR,state['R'])
        state['logs'].append(dict(state['gesture'],pixels=state['path'],actualTipM=Q[ci,-1].tolist()))
        state['phase']+=1
        if state['phase']==(3 if WHOLE else 4):state['phase']=0;state['curve']+=1;print('R56_COMBED_GUIDE',ci,flush=True)
        state['point']=-2;return .06
    except Exception:fail();return None

def finish():
    o=state['o'];bpy.ops.object.mode_set(mode='OBJECT');Q,R=f.v.hair_arrays(o);o.data.attributes.remove(o.data.attributes['.selection']);after=f.state()
    assert all(after[x]==state['before'][x] for x in ('meshes','materials','skinFields','stage'))
    assert all(after['curves'][name]==row for name,row in state['before']['curves'].items())
    assert np.isfinite(Q).all() and np.array_equal(Q[:,0],state['P'][:,0]) and np.array_equal(R,state['R'])
    changedMask=np.any(np.linalg.norm(Q-state['P'],axis=2)>1e-7,axis=1);changed=int(changedMask.sum())
    untouched=[ci for ci in state['order'] if not changedMask[ci]]
    indices=np.array(state['order'],dtype='i4')
    if WHOLE:
        o.data.remove_curves(indices=[i for i in range(64) if i not in state['order']]);Q,R=f.v.hair_arrays(o)
    bpy.data.objects[k.k.OLD].hide_render=True;bpy.data.objects[k.k.OLD].hide_set(True)
    bpy.data.brushes.remove(state['brush'],do_unlink=True);b.camera('face');bpy.context.scene.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0
    o['scope']=f'Target-native{len(Q)}master Comb trial. Actual physical radii preserved; no children, full contacts, dynamics or runtime accepted.'
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    np.savez_compressed(E/(TAG+'-native-guide-data.npz'),before=state['P'][indices],positions=Q,radii=R,normals=state['normals'][indices],sourceCurveIndices=indices)
    save(TAG+'-build-summary.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'output':str(OUT),'outputSha256':b.sha(OUT),'method':'Native modal Comb on new target-rooted normal seeds; no source path/station copying.',
        'curveCount':len(Q),'pointsPerCurve':128,'changedCurves':changed,'unchangedRequestedSourceCurves':untouched,'sourceCurveIndices':indices.tolist(),'wholeCurveCoveragePilot':WHOLE,'rootPositionsAndRadiiExact':True,'otherOriginalCharacterStateExact':True,'strokes':state['logs'],'seconds':time.time()-state['start'],
        'status':'TOOL_COVERAGE_INCOMPLETE_NOT_ADOPTED' if untouched else 'COARSE_TARGET_NATIVE_AUTHORING_PENDING_REVIEW','contact':'NOT_TESTED_NATIVE_FLAG_NOT_PROOF'})
    f.E=E;f.render(TAG+'-actual-fibres',('face','oblique','profile'));k.k.k.k.a.i.ch.review.extras(TAG+'-actual-fibres',E)
    o.data.attributes['radius'].data.foreach_set('value',np.full_like(R,.0007).ravel());bpy.context.view_layer.update()
    f.render(TAG+'-path-diagnostic',('face','oblique','profile'));k.k.k.k.a.i.ch.review.extras(TAG+'-path-diagnostic',E)
    save(TAG+'-native-session.json',{'status':'COMPLETED_SCRIPT','output':str(OUT),'strokes':len(state['logs'])});print('R56_NATIVE_COMB_READY',changed,time.time()-state['start'],flush=True)
    bpy.ops.wm.quit_blender()

bpy.app.timers.register(init,first_interval=3.)
