"""Replay native Comb through Blender's own window event queue, hidden GUI only.

The Curves stroke operator has invoke/modal callbacks, no execute callback.
No desktop mouse/keyboard injection and no direct replacement hair algorithm.
"""
from pathlib import Path
import bpy,importlib.util,numpy as np,time,traceback,sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.view3d_utils import location_3d_to_region_2d
sp=importlib.util.spec_from_file_location('comb52events',Path(__file__).with_name('build-female-next-r0052-combed-bob.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
b=k.b;f=k.f;E=k.E;state={}
SECTIONED='--sectioned' in sys.argv
EFFECTIVE='--effective-settings' in sys.argv
PREFIX=('b-fixed' if EFFECTIVE else 'b') if SECTIONED else 'a'
PILOT=(PREFIX+'-native-comb-pilot.json') if SECTIONED else 'native-comb-pilot.json'
if SECTIONED:k.OUT=b.S/'aevrynd-female-next-r0052-b-native-sectional-bob.blend'
if EFFECTIVE:k.OUT=b.S/'aevrynd-female-next-r0052-b-effective-sectional-bob.blend'

def quit_with_error():
    error=traceback.format_exc();print(error,flush=True);k.k.save('native-event-session-result.json',{'status':'SCRIPT_ERROR','error':error})
    bpy.ops.wm.quit_blender()

def init():
    try:
        assert Path(bpy.data.filepath)==k.SRC
        assert b.sha(k.SRC)=='b86f7eeedf6fd6a4d9a7f13ff42dc4051907516bc90be8261f02e7678242a3ff'
        full='--full' in sys.argv;source=bpy.data.objects[k.NAME];before=f.state()
        if full:
            import json
            assert json.loads((E/PILOT).read_text())['status']=='PASS_NATIVE_STROKE_PILOT_STATIC_SCOPE'
            o=source
        else:
            d=source.data.copy();o=bpy.data.objects.new('AFN52_NATIVE_COMB_PILOT',d);bpy.context.scene.collection.objects.link(o)
            o.matrix_world=source.matrix_world.copy();keep=set(np.linspace(0,len(d.curves)-1,160,dtype=int))
            d.remove_curves(indices=[i for i in range(len(d.curves)) if i not in keep])
        for ob in bpy.context.view_layer.objects:ob.select_set(False)
        o.hide_set(False);o.select_set(True);bpy.context.view_layer.objects.active=o
        P,R=f.v.hair_arrays(o);o.data.surface=bpy.data.objects[b.BODY];o.data.surface_uv_map=o.data.surface.data.uv_layers[0].name
        plan=k.STROKES;sectionWeights=None;guideNames=[]
        if SECTIONED:
            ps=importlib.util.spec_from_file_location('section52',Path(__file__).with_name('plan-female-next-r0052-sectional-sculpt.py'))
            planner=importlib.util.module_from_spec(ps);ps.loader.exec_module(planner)
            ALL,_=f.v.hair_arrays(source);mx=np.array(source.matrix_world)
            ALL=ALL.astype('f8')@mx[:3,:3].T+mx[:3,3]
            plan,guideRoots,guideNames=planner.plan(ALL)
            mx=np.array(o.matrix_world);roots=P[:,0].astype('f8')@mx[:3,:3].T+mx[:3,3]
            sectionWeights=planner.weights(roots,guideRoots).astype('f4')
            for attrName in ('.selection','.selection_handle_left','.selection_handle_right'):
                if attrName in o.data.attributes:o.data.attributes.remove(o.data.attributes[attrName])
            o.data.attributes.new('.selection','FLOAT','CURVE')
        o.data.use_sculpt_collision=True;o.data.surface_collision_distance=.00010
        bpy.ops.object.mode_set(mode='SCULPT_CURVES')
        bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS',relative_asset_identifier='brushes/essentials_brushes-curve_sculpt.blend/Brush/Comb')
        area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
        with bpy.context.temp_override(area=area,region=region):bpy.ops.wm.tool_set_by_id(name='builtin.brush')
        brush=bpy.context.scene.tool_settings.curves_sculpt.brush;brush.use_pressure_size=False;brush.use_pressure_strength=False;brush.falloff_shape='SPHERE'
        if EFFECTIVE:
            unified=bpy.context.scene.tool_settings.curves_sculpt.unified_paint_settings
            unified.use_unified_size=False;unified.use_unified_strength=False
        state.update(full=full,o=o,P=P,R=R,before=before,area=area,region=region,brush=brush,
                     window=bpy.context.window,stroke=0,point=-2,logs=[],start=time.time(),plan=plan,
                     sectionWeights=sectionWeights,guideNames=guideNames)
        bpy.app.timers.register(step,first_interval=.3)
    except Exception:quit_with_error()
    return None

def step():
    try:
        index=state['stroke']
        if index==len(state['plan']):finish();return None
        row=state['plan'][index];brush=state['brush'];region=state['region'];area=state['area'];window=state['window']
        if state['point']==-2:
            if SECTIONED:
                state['o'].data.attributes['.selection'].data.foreach_set('value',state['sectionWeights'][:,row['guideIndex']])
                state['o'].data.update_tag();bpy.context.view_layer.update()
            rv=area.spaces.active.region_3d;area.spaces.active.clip_start=.001
            outward=Vector(row['view']).normalized();rv.view_rotation=(-outward).to_track_quat('-Z','Y')
            rv.view_location=(0,-.015,1.445);rv.view_distance=.45;rv.view_perspective='ORTHO';rv.update();area.tag_redraw()
            brush.size=row['radius'];brush.strength=row['strength'];brush.use_locked_size='VIEW'
            K=np.array(row['knots']);u=np.linspace(0,2,17);points=np.column_stack([np.interp(u,np.arange(3),K[:,j]) for j in range(3)])
            path=[location_3d_to_region_2d(region,rv,Vector(p)) for p in points]
            assert all(p is not None for p in path)
            state['path']=[(int(p.x+region.x),int(p.y+region.y)) for p in path];state['point']=-1
            return .15
        if state['point']==-1:
            x,y=state['path'][0];window.event_simulate(type='MOUSEMOVE',value='NOTHING',x=x,y=y)
            window.event_simulate(type='LEFTMOUSE',value='PRESS',x=x,y=y);state['point']=0;return .06
        pi=state['point']
        if pi<len(state['path']):
            x,y=state['path'][pi];window.event_simulate(type='MOUSEMOVE',value='NOTHING',x=x,y=y)
            state['point']+=1;return .04
        x,y=state['path'][-1];window.event_simulate(type='LEFTMOUSE',value='RELEASE',x=x,y=y)
        unified=bpy.context.scene.tool_settings.curves_sculpt.unified_paint_settings
        state['logs'].append(dict(row,windowPath=state['path'],mode='NATIVE_WINDOW_EVENT_SIMULATION',region=[region.width,region.height],
                                 actualBrushSize=brush.size,unifiedSize=unified.size,useUnifiedSize=unified.use_unified_size,
                                 actualBrushStrength=brush.strength,useUnifiedStrength=unified.use_unified_strength))
        print('R52_EVENT_STROKE',row['name'],flush=True)
        state['stroke']+=1;state['point']=-2;return .25
    except Exception:quit_with_error();return None

def finish():
    o=state['o'];bpy.ops.object.mode_set(mode='OBJECT');bpy.context.view_layer.update()
    if SECTIONED:o.data.attributes.remove(o.data.attributes['.selection'])
    P,R=state['P'],state['R'];Q,RR=f.v.hair_arrays(o);delta=np.linalg.norm(Q-P,axis=2)
    row={'source':str(k.SRC),'sourceSha256':b.sha(k.SRC),'method':'Actual native Comb via modal internal window events; native collision enabled, original fibres/root positions/radii retained.',
        'strokes':state['logs'],'curveCount':len(P),'pointsPerCurve':P.shape[1],
        'changedCurves':int(np.any(delta>1e-8,axis=1).sum()),'maximumLocalDisplacementM':float(delta.max()),
        'maximumRootDisplacementM':float(np.linalg.norm(Q[:,0]-P[:,0],axis=1).max()),
        'radiiExact':bool(np.array_equal(R,RR)),'collisionSurface':o.data.surface.name,
        'nativeCollisionDistanceM':float(o.data.surface_collision_distance),'seconds':time.time()-state['start'],
        'authoringMode':'RETAINED_GUIDE_DIRECTED_NATIVE_SECTIONAL_SCULPT' if SECTIONED else 'LOCAL_COMB_TOUCHUP',
        'retainedGuidesUsed':state['guideNames'],'effectiveSettingsCorrection':EFFECTIVE}
    assert row['changedCurves']>0,'Modal strokes made no geometry change'
    assert row['maximumRootDisplacementM']<1e-8 and row['radiiExact']
    if not state['full']:
        V,T=b.evaluated(bpy.data.objects[b.BODY],True);tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True)
        mx=np.array(o.matrix_world);W=Q.astype('f8')@mx[:3,:3].T+mx[:3,3];rad=RR.astype('f8')*np.linalg.norm(mx[:3,:3],ord=2)
        contact=f.flowcheck.check(W,rad,tree,V[T]);row['actualFiniteBodyCapsules']=contact
        row['status']='PASS_NATIVE_STROKE_PILOT_STATIC_SCOPE' if contact['status']=='PASS_TESTED_STATIC_CAPSULES' else 'REJECT_NATIVE_STROKE_PILOT_CONTACT'
        k.k.save(PILOT,row);np.savez_compressed(E/((PREFIX+'-native-comb-pilot.npz') if SECTIONED else 'native-comb-pilot.npz'),before=P,after=Q,radii=RR)
    else:
        after=f.state();before=state['before']
        assert all(after[key]==before[key] for key in ('meshes','materials','skinFields','stage'))
        assert all(after['curves'][n]==r for n,r in before['curves'].items() if n!=k.NAME)
        # Baked native positions are the asset. Do not retain the activated
        # production-tool brush datablock as an engine/model dependency.
        brush=state['brush'];bpy.data.brushes.remove(brush,do_unlink=True)
        row['activatedProductionBrushRemovedBeforeSave']=True
        row['externalLibraries']=[{'name':lib.name,'filepath':lib.filepath} for lib in bpy.data.libraries]
        b.camera('face');bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(k.OUT),compress=True)
        row.update(output=str(k.OUT),outputSha256=b.sha(k.OUT),status='FULL_NATIVE_COMB_CANDIDATE_PENDING_REVIEW')
        k.k.save(PREFIX+'-build-summary.json',row)
        f.E=E;f.render(PREFIX+'-after',('face','oblique','profile'));k.k.k.a.i.i.E=E;k.k.k.a.i.i.closeup(PREFIX+'-after');k.k.k.a.i.ch.review.extras(PREFIX+'-after',E)
    print('R52_NATIVE_MODAL_RESULT',row['status'],row['changedCurves'],row['maximumLocalDisplacementM'],flush=True)
    k.k.save('native-event-session-result.json',{'status':'COMPLETED_SCRIPT','full':state['full']})
    bpy.ops.wm.quit_blender()

bpy.app.timers.register(init,first_interval=3.)
