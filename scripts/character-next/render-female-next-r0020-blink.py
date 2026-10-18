"""Render actual saved geometry, alternate light, eye IDs and playable review."""
import bpy,json,importlib.util,sys,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
spec=importlib.util.spec_from_file_location('pin',Path(__file__).with_name('build-female-next-r0020-pinned-blink.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
a,E,S=b.a,b.E,b.S
PREFIX='b' if '--b' in sys.argv else 'a'
SOURCE=S/('aevrynd-female-next-r0020-b-visible-rim-blink-study.blend' if PREFIX=='b' else 'aevrynd-female-next-r0020-a-pinned-angular-blink-study.blend')
HEAD=1.5624730926266572*.91
def camera(view='face',resolution=900):
    s=bpy.context.scene;c=s.camera
    if view=='eyes':location=(0.,-.43,1.459975242614746+.005);target=(0.,-.115,1.459975242614746);res=(1400,650)
    elif view=='oblique':location=(.46,-.82,HEAD+.04);target=(0.,-.01,HEAD);res=(resolution,resolution)
    elif view=='side':location=(.86,-.16,HEAD+.02);target=(0.,-.01,HEAD);res=(resolution,resolution)
    else:location=(0.,-.90,HEAD+.015);target=(0.,-.02,HEAD);res=(resolution,resolution)
    c.location=location;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=100;s.render.resolution_x,s.render.resolution_y=res;s.render.resolution_percentage=100;s.render.threads_mode='FIXED';s.render.threads=4
def render(name):
    path=E/name;bpy.context.scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);return str(path)
def load():
    report=json.loads((E/f'{PREFIX}-build-verification.json').read_text());assert a.sha(SOURCE)==report['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(SOURCE));a.solid.stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],'neutral');return bpy.context.scene
def ids():
    s=bpy.context.scene
    def mat(name,color):
        m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');e=n.new('ShaderNodeEmission');e.inputs['Color'].default_value=(*color,1.);m.node_tree.links.new(e.outputs[0],out.inputs['Surface']);return m
    black=mat('AFN20_MASK_OCCLUDER',(0.,0.,0.));white=mat('AFN20_MASK_EYES',(1.,1.,1.))
    for o in bpy.data.objects:
        if o.type in ('MESH','CURVES','CURVE'):
            o.data.materials.clear();o.data.materials.append(white if o.name.startswith('AFN6_') else black)
            if o.type=='MESH':
                for p in o.data.polygons:p.material_index=0
    s.world.use_nodes=True
    for n in s.world.node_tree.nodes:
        if n.bl_idname=='ShaderNodeBackground':n.inputs['Strength'].default_value=0.
    s.view_settings.view_transform='Raw';s.view_settings.look='None';s.view_settings.exposure=0.;s.view_settings.gamma=1.;s.render.film_transparent=False
def stills():
    s=load();rows=[]
    for view,w in (('face',0.),('face',.5),('face',1.),('oblique',0.),('oblique',1.),('side',0.),('side',1.)):
        a.set_blink(w,w);camera(view);rows.append({'view':view,'weight':w,'light':'saved','path':render(f'{PREFIX}-{view}-{w:.2f}.png')})
    for o in bpy.data.objects:
        if o.type=='LIGHT':o.location.x=-o.location.x;o.rotation_euler=(Vector((0.,-.02,HEAD))-o.location).to_track_quat('-Z','Y').to_euler()
    for w in (0.,1.):
        a.set_blink(w,w);camera('face');rows.append({'view':'face','weight':w,'light':'mirrored positions, reaimed at head; exposure unchanged','path':render(f'{PREFIX}-alternate-face-{w:.2f}.png')})
    load();ids()
    for view,w in (('eyes',0.),('eyes',1.),('oblique',1.),('side',1.)):
        a.set_blink(w,w);camera(view);rows.append({'view':view,'weight':w,'material':'temporary opaque white optical union, all else black, Raw view','path':render(f'{PREFIX}-eye-id-{view}-{w:.2f}.png')})
    b.save(f'{PREFIX}-render-verification.json',{'source':str(SOURCE),'sha256':a.sha(SOURCE),'renders':rows,'scope':'Actual saved geometry. Eye-ID raster only measures opaque optical-surface visibility in listed cameras, not continuous/all-view geometric closure. No source overwritten.'})
def shape_digest():
    h=hashlib.sha256()
    for o in sorted((x for x in bpy.data.objects if x.type=='MESH' and x.data.shape_keys),key=lambda x:x.name):
        for k in o.data.shape_keys.key_blocks:
            p=np.empty((len(k.data),3),np.float32);k.data.foreach_get('co',p.ravel());h.update(o.name.encode());h.update(k.name.encode());h.update(p.tobytes())
    return h.hexdigest()
def animate():
    s=load();a.set_blink(0.,0.);before=a.prior.controls();digest=shape_digest();rig=bpy.data.objects['AFN_R0005_Rig'];s.render.fps=60;s.frame_start=1;s.frame_end=121
    for frame,value in ((1,0.),(31,0.),(39,1.),(41,1.),(55,0.),(121,0.)):
        for side in ('L','R'):rig['AFN19_Blink_'+side]=value;rig.keyframe_insert(data_path='["AFN19_Blink_'+side+'"]',frame=frame)
    action=rig.animation_data.action;curves=[]
    if hasattr(action,'fcurves'):curves=list(action.fcurves)
    else:
        for layer in action.layers:
            for strip in layer.strips:
                bag=strip.channelbag(rig.animation_data.action_slot)
                if bag:curves.extend(bag.fcurves)
    assert len(curves)==2
    for f in curves:
        for k in f.keyframe_points:k.interpolation='LINEAR'
    s.frame_set(1);assert a.prior.controls()==before and shape_digest()==digest;camera('face',700);s['aevrynd_release_state']='PARTIAL_BLINK_REVIEW_NOT_ACCEPTED_CONTINUOUS_CONTACT_AND_CLOSURE_PENDING';s['aevrynd_motion_scope']='Artist-authored two-second blink; no measured natural timing or continuous contact certificate.';bpy.context.preferences.filepaths.save_version=0;dest=S/f'aevrynd-female-next-r0020-{PREFIX}-animated-review.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));bpy.ops.wm.open_mainfile(filepath=str(dest));s=bpy.context.scene;s.frame_set(1);assert shape_digest()==digest;frames=[];folder=E/(PREFIX+'-review-frames');folder.mkdir(exist_ok=True)
    for i,frame in enumerate(range(1,122,4)):
        s.frame_set(frame);path=folder/f'blink-{i:03d}.png';s.render.filepath=str(path);bpy.ops.render.render(write_still=True);frames.append({'frame':frame,'left':float(bpy.data.objects['AFN_R0005_Rig']['AFN19_Blink_L']),'right':float(bpy.data.objects['AFN_R0005_Rig']['AFN19_Blink_R']),'path':str(path)})
    b.save(f'{PREFIX}-animated-review-verification.json',{'source':str(SOURCE),'sourceSha256':a.sha(SOURCE),'output':str(dest),'outputSha256':a.sha(dest),'shapeArrayDigest':digest,'allShapeArraysExact':True,'channels':2,'fps':60,'frameRange':[1,121],'previewFps':15,'frames':frames,'scope':'Playable artist-authored diagnostic only; no overall/continuous motion/engine acceptance.'})
def previous():
    source=S/'aevrynd-female-next-r0019-c-angular-blink-study.blend';report=json.loads((a.E/'c-build-verification.json').read_text());assert a.sha(source)==report['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(source));a.solid.stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],'neutral');rows=[]
    for w in (0.,.5,1.):
        a.set_blink(w,w);camera('face');rows.append({'weight':w,'path':render(f'before-r0019-c-face-{w:.2f}.png')})
    b.save('before-comparison-render-verification.json',{'source':str(source),'sourceSha256':a.sha(source),'renders':rows,'sameCameraLightExposureResolutionAsCandidateA':True,'scope':'Old C and new A saved studies rendered by the same face camera function at 900 square; saved lighting unchanged.'})
if __name__=='__main__':
    if '--previous' in sys.argv:previous()
    elif '--animate' in sys.argv:animate()
    else:stills()
