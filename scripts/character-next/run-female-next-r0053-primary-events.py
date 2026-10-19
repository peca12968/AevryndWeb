"""Author new masters through Blender's native modal Pull Tips tool.

One selected curve per gesture; projected motion plane contains the intended
world displacement. Thick guide renders are diagnostics, never physical hair.
The real fibre radius remains unchanged and is checked independently.
"""
from pathlib import Path
import bpy,importlib.util,numpy as np,json,time,traceback,sys
from mathutils import Vector
from bpy_extras.view3d_utils import location_3d_to_region_2d
sp=importlib.util.spec_from_file_location('foundation53artist',Path(__file__).with_name('build-female-next-r0053-scalp-foundation.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
b=k.b;f=k.f;E=k.E
INFO=json.loads((E/'refined-foundation-build.json').read_text())
SRC=Path(INFO['output']);GROW='--short-grow' in sys.argv;PILOT='--pilot' in sys.argv;FIXED='--corrected-route' in sys.argv
RESUME='--resume-pilot' in sys.argv;INHERITED=[];INPUT_SHA=INFO['outputSha256']
if RESUME:
    assert GROW and FIXED and not PILOT
    pilot=json.loads((E/'grown-fixed-pilot-build-summary.json').read_text())
    proof=json.loads((E/'grown-fixed-pilot-saved-static-verification.json').read_text())
    assert proof['sourceSha256']==pilot['outputSha256']
    assert proof['surfaceUVBindingMatchesActualFoot'] and proof['rootPositionsAndRadiiRetained']
    assert proof['actualFiniteBodyCapsules']['unqualifiedSegments']==0 and not proof['actualFiniteBodyCapsules']['rootFailures']
    assert proof['actualFiniteMasterSelfCapsules']['overlapsBeyondNumericalAllowance']==0
    SRC=Path(pilot['output']);INPUT_SHA=pilot['outputSha256'];INHERITED=pilot['authoredCurveIndices']
PREFIX=(('grown-fixed-pilot' if PILOT else 'grown-fixed') if FIXED else ('grown-pilot' if PILOT else 'grown')) if GROW else 'primary'
OUT=b.S/('aevrynd-female-next-r0053-b-native-grown-primary-groom.blend' if GROW else 'aevrynd-female-next-r0053-a-pulled-primary-groom.blend')
if PILOT:OUT=b.S/'aevrynd-female-next-r0053-b-native-grown-primary-pilot.blend'
if FIXED:OUT=b.S/('aevrynd-female-next-r0053-c-reparameterized-primary-pilot.blend' if PILOT else 'aevrynd-female-next-r0053-c-reparameterized-primary-groom.blend')
NAME=k.NAME;state={}

def save(name,row):k.save(name,row)

def failure():
    error=traceback.format_exc();print(error,flush=True)
    save(PREFIX+'-native-session.json',{'status':'SCRIPT_ERROR','error':error,'completedStrokes':state.get('logs',[])})
    bpy.ops.wm.quit_blender()

def init():
    try:
        assert Path(bpy.data.filepath)==SRC and b.sha(SRC)==INPUT_SHA
        before=f.state();o=bpy.data.objects[NAME];P,R=f.v.hair_arrays(o)
        assert P.shape==(64,128,3) and np.isfinite(P).all()
        data=np.load(E/'refined-foundation-data.npz');section=data['section']
        if GROW and not RESUME:
            normal=data['normals'];P=P[:,0,None]+normal[:,None]*np.linspace(0,.0008,128)[None,:,None]
            o.data.position_data.foreach_set('vector',P.astype('f4').ravel())
            P=P.astype('f4')
        guides=[bpy.data.objects[n] for n in INFO['sectionGuideNames']]
        # surface_uv_coordinate is a native FLOAT2 attribute, not FLOAT_VECTOR.
        oldUV=o.data.attributes['surface_uv_coordinate']
        sourceUVType=oldUV.data_type
        if sourceUVType!='FLOAT2':
            values=np.array([list(v.vector)[:2] for v in oldUV.data],dtype='f4')
            o.data.attributes.remove(oldUV)
            attr=o.data.attributes.new('surface_uv_coordinate','FLOAT2','CURVE')
            attr.data.foreach_set('vector',values.ravel())
        for ob in bpy.context.view_layer.objects:ob.select_set(False)
        o.hide_set(False);o.select_set(True);bpy.context.view_layer.objects.active=o
        for attr in list(o.data.attributes):
            if attr.name.startswith('.selection'):o.data.attributes.remove(attr)
        o.data.attributes.new('.selection','FLOAT','CURVE')
        o.data.surface=bpy.data.objects[b.BODY];o.data.surface_uv_map=o.data.surface.data.uv_layers[0].name
        o.data.use_sculpt_collision=True;o.data.surface_collision_distance=.00010
        bpy.ops.object.mode_set(mode='SCULPT_CURVES')
        bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS',relative_asset_identifier='brushes/essentials_brushes-curve_sculpt.blend/Brush/Pull Tips')
        area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
        region=next(r for r in area.regions if r.type=='WINDOW')
        with bpy.context.temp_override(area=area,region=region):bpy.ops.wm.tool_set_by_id(name='builtin.brush')
        brush=bpy.context.scene.tool_settings.curves_sculpt.brush
        brush.use_pressure_size=False;brush.use_pressure_strength=False
        brush.falloff_shape='PROJECTED';brush.use_locked_size='VIEW';brush.size=90;brush.strength=1.
        unified=bpy.context.scene.tool_settings.curves_sculpt.unified_paint_settings
        unified.use_unified_size=False;unified.use_unified_strength=False
        targets=[];routes=[]
        for ci,gi in enumerate(section):
            guide=guides[int(gi)];points=guide.data.splines[0].bezier_points
            guideRoot=np.array(guide.matrix_world@points[0].co)
            tip=np.array(guide.matrix_world@points[-1].co)
            # Distinct endpoint per master; roots are actual anatomy, not moved
            # to avoid contact. This is an artist target, not copied guide shape.
            shift=(P[ci,0]-guideRoot)*.35
            targets.append(tip+shift)
            route=np.array([guide.matrix_world@p.co for p in points[1:]])
            route+=shift[None]
            if FIXED:
                # The old guide's short exit belongs to its own root. This
                # new root needs its own anatomical departure before free flow.
                route=route[1:]
                normal=data['normals'][ci];direction=route[0]-P[ci,0]
                tangent=direction-normal*np.dot(direction,normal)
                tangent/=max(np.linalg.norm(tangent),1e-20)
                exit=P[ci,0]+normal*.006+tangent*.012
                route=np.vstack((exit,route))
            routes.append(route)
        order=[ci for ci in range(len(P)) if ci not in INHERITED]
        if PILOT:
            roots=P[:,0];order=sorted(set(int(fn(roots[:,axis])) for axis in range(3) for fn in (np.argmin,np.argmax)))
        state.update(o=o,P=P,R=R,before=before,area=area,region=region,order=order,
                     brush=brush,window=bpy.context.window,index=0,point=-2,
                     targets=np.array(targets),routes=routes,routeIndex=0,logs=[],start=time.time(),sourceUVType=sourceUVType)
        bpy.app.timers.register(step,first_interval=.3)
    except Exception:failure()
    return None

def step():
    try:
        o=state['o'];area=state['area'];region=state['region'];window=state['window']
        if state['index']==len(state['order']):finish();return None
        ci=state['order'][state['index']]
        if FIXED and state['point']>=0:
            # Blender's tip-extension resampling can clamp old sample lengths
            # to the previous tip, as measured in the six-master trial. Keep
            # the existing POLY path but uniformly reparameterize it between
            # native events. This does not push points away from failed skin.
            Q,_=f.v.hair_arrays(o);curve=Q[ci].astype('f8')
            arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(curve,axis=0),axis=1))]
            keep=np.r_[True,np.diff(arc)>1e-10]
            if arc[-1]>0:
                target=np.linspace(0,arc[-1],len(curve))
                sampled=np.column_stack([np.interp(target,arc[keep],curve[keep,j]) for j in range(3)])
                sampled[0]=state['P'][ci,0];Q[ci]=sampled.astype('f4')
                o.data.position_data.foreach_set('vector',Q.ravel());o.data.update_tag();bpy.context.view_layer.update()
        if state['point']==-2:
            weights=np.zeros(len(state['P']),dtype='f4');weights[ci]=1
            o.data.attributes['.selection'].data.foreach_set('value',weights)
            o.data.update_tag();bpy.context.view_layer.update()
            P,_=f.v.hair_arrays(o);start=P[ci,-1].astype('f8')
            routeIndex=state['routeIndex']
            if GROW:
                route=state['routes'][ci][routeIndex:routeIndex+2]
                K=np.vstack((start,route));end=K[-1]
                outward=np.cross(K[1]-start,end-start) if len(K)==3 else np.zeros(3)
            else:
                end=state['targets'][ci];K=np.vstack((start,end));outward=np.zeros(3)
            delta=end-start
            if np.linalg.norm(outward)<1e-5:outward=np.cross(delta,(1.,0,0))
            if np.linalg.norm(outward)<1e-5:outward=np.cross(delta,(0,1.,0))
            outward=Vector(outward).normalized()
            rv=area.spaces.active.region_3d;area.spaces.active.clip_start=.001
            rv.view_rotation=(-outward).to_track_quat('-Z','Y')
            rv.view_location=Vector((K.min(0)+K.max(0))*.5);rv.view_distance=max(.6,2.7*float(np.linalg.norm(K.max(0)-K.min(0))))
            rv.view_perspective='ORTHO';rv.update();area.tag_redraw()
            segments=[]
            for a,z in zip(K[:-1],K[1:]):
                # Smooth directional strokes through real three-dimensional
                # artist stations; each two-leg gesture lies in its own plane.
                segments.append(a[None]+np.linspace(0,1,17,endpoint=False)[:,None]*(z-a)[None])
            points=(np.vstack(segments+[K[-1:]]) if GROW else start[None]+np.linspace(0,1,33)[:,None]*delta[None])
            if FIXED and len(K)==3:
                la=np.linalg.norm(K[1]-K[0]);lb=np.linalg.norm(K[2]-K[1]);rounding=.25*min(la,lb)
                a=K[1]+(K[0]-K[1])*rounding/max(la,1e-20)
                z=K[1]+(K[2]-K[1])*rounding/max(lb,1e-20)
                u=np.linspace(0,1,17)[:,None]
                rounded=(1-u)**2*a+2*(1-u)*u*K[1]+u*u*z
                points=np.vstack((K[0]+np.linspace(0,1,9,endpoint=False)[:,None]*(a-K[0]),
                                  rounded,z+np.linspace(0,1,9)[1:,None]*(K[2]-z)))
            elif GROW and len(K)==3:
                u=np.linspace(0,1,33)[:,None];control=2*K[1]-.5*(K[0]+K[2])
                points=(1-u)**2*K[0]+2*(1-u)*u*control+u*u*K[2]
            pixel=[location_3d_to_region_2d(region,rv,Vector(p)) for p in points]
            assert all(p is not None and 12<p.x<region.width-12 and 12<p.y<region.height-12 for p in pixel),('Gesture outside view',ci)
            state['path']=[(int(p.x+region.x),int(p.y+region.y)) for p in pixel]
            state['gesture']={'curveIndex':ci,'startM':start.tolist(),'targetM':end.tolist(),'view':list(outward),
                              'viewDistance':rv.view_distance,'selection':'ONE_FULL_NATIVE_CURVE',
                              'brush':'Pull Tips','brushSize':state['brush'].size,'strength':state['brush'].strength,
                              'falloff':state['brush'].falloff_shape,'useUnifiedSize':False,'useUnifiedStrength':False,
                              'routeStationsM':K.tolist(),'routeIndex':routeIndex,'shortRootExtension':GROW}
            state['point']=-1;return .15
        if state['point']==-1:
            x,y=state['path'][0];window.event_simulate(type='MOUSEMOVE',value='NOTHING',x=x,y=y)
            window.event_simulate(type='LEFTMOUSE',value='PRESS',x=x,y=y);state['point']=0;return .06
        pi=state['point']
        if pi<len(state['path']):
            x,y=state['path'][pi];window.event_simulate(type='MOUSEMOVE',value='NOTHING',x=x,y=y)
            state['point']+=1;return .025
        x,y=state['path'][-1];window.event_simulate(type='LEFTMOUSE',value='RELEASE',x=x,y=y)
        # The event is consumed after this callback; inspect it on the next step.
        state['logs'].append(dict(state['gesture'],windowPath=state['path'],region=[region.width,region.height]))
        print('R53_PULL',ci,state['routeIndex'],flush=True)
        state['routeIndex']+=2
        if not GROW or state['routeIndex']>=len(state['routes'][ci]):state['index']+=1;state['routeIndex']=0
        state['point']=-2
        return .2
    except Exception:failure();return None

def diagnostics(o,Q):
    # Separate, visibly labelled technical paths; radii are not collision radii.
    d=bpy.data.curves.new('AFN53_THICK_GUIDE_DIAGNOSTIC','CURVE')
    d.dimensions='3D';d.bevel_depth=.0010;d.bevel_resolution=2;d.resolution_u=1;d.use_fill_caps=True
    mat=bpy.data.materials.new('AFN53_GUIDE_DIAGNOSTIC_GOLD');mat.diffuse_color=(.32,.12,.025,1)
    d.materials.append(mat)
    for curve in Q:
        spline=d.splines.new('POLY');spline.points.add(len(curve)-1)
        spline.points.foreach_set('co',np.column_stack((curve,np.ones(len(curve)))).astype('f4').ravel())
        spline.points.foreach_set('radius',np.linspace(1,.2,len(curve)).astype('f4'))
    display=bpy.data.objects.new(d.name,d);bpy.context.scene.collection.objects.link(display)
    display['scope']='UNSAVED_DIAGNOSTIC_ONLY_1MM_RADII_NOT_ACTUAL_HAIR_OR_COLLISION_PROOF'
    o.hide_render=True;f.E=E;f.render(PREFIX+'-path-diagnostic',('face','oblique','profile'))
    k.k.k.a.i.ch.review.extras(PREFIX+'-path-diagnostic',E)

def finish():
    o=state['o'];bpy.ops.object.mode_set(mode='OBJECT');bpy.context.view_layer.update()
    o.data.attributes.remove(o.data.attributes['.selection'])
    Q,RR=f.v.hair_arrays(o);P,R=state['P'],state['R'];after=f.state()
    assert np.array_equal(P[:,0],Q[:,0]) and np.array_equal(R,RR)
    assert all(after[key]==state['before'][key] for key in ('meshes','materials','skinFields','stage'))
    assert all(after['curves'][n]==row for n,row in state['before']['curves'].items() if n!=NAME)
    delta=np.linalg.norm(Q-P,axis=2);tipErrors=np.linalg.norm(Q[:,-1]-state['targets'],axis=1)
    brush=state['brush'];bpy.data.brushes.remove(brush,do_unlink=True)
    o['scope']='64 new native surface-bound sculpted masters; coarse static authoring prototype, no dense hair, dynamic/self/runtime acceptance.'
    row={'source':str(SRC),'sourceSha256':b.sha(SRC),'method':'Native modal Pull Tips, one selected surface-bound curve per gesture, actual body collision enabled.',
         'shortRootExtension':GROW,'initialRootLengthM':.0008 if GROW else None,
         'correctedRootExitAndUniformReparameterization':FIXED,
         'curveCount':len(Q),'pointsPerCurve':Q.shape[1],'strokes':state['logs'],
         'pilot':PILOT,'authoredCurveIndices':sorted(set(state['order']+INHERITED)),
         'executedCurveIndices':state['order'],'inheritedVerifiedCurveIndices':INHERITED,
         'changedCurves':int(np.any(delta>1e-8,axis=1).sum()),'maximumDisplacementM':float(delta.max()),
         'rootPositionsExact':True,'radiiExact':True,'otherBodySkinMaterialsStageAndCurvesExact':True,
         'sourceSurfaceUVType':state['sourceUVType'],'correctedSurfaceUVType':o.data.attributes['surface_uv_coordinate'].data_type,
         'tipTargetErrorsM':tipErrors.tolist(),'seconds':time.time()-state['start'],
         'bodyContact':'PENDING_INDEPENDENT_FULL_FINITE_PATH_CHECK','selfDynamicRuntime':'NOT_ACCEPTED',
         'status':'COARSE_PRIMARY_AUTHORING_PENDING_VISUAL_REVIEW_NOT_FINISHED_HAIR'}
    assert row['changedCurves']>0,'Native tool made no geometry change'
    b.camera('face');bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    row.update(output=str(OUT),outputSha256=b.sha(OUT));save(PREFIX+'-build-summary.json',row)
    np.savez_compressed(E/(PREFIX+'-native-data.npz'),before=P,after=Q,radii=RR,targets=state['targets'])
    f.E=E;f.render(PREFIX+'-actual-fibres',('face','oblique','profile'))
    k.k.k.a.i.ch.review.extras(PREFIX+'-actual-fibres',E)
    diagnostics(o,Q)
    save(PREFIX+'-native-session.json',{'status':'COMPLETED_SCRIPT','source':str(SRC),'output':str(OUT)})
    print('R53_NATIVE_PRIMARY_RESULT',row['changedCurves'],float(tipErrors.max()),flush=True)
    bpy.ops.wm.quit_blender()

bpy.app.timers.register(init,first_interval=3.)
