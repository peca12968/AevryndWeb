"""Isolated CC0 female scan foundation; identical clay/camera/light anatomy review.

Append only the explicitly CC0 female collection. Preserve base topology, UV and
Multires sculpt data. No rig, program, material or male asset is imported.
"""
import bpy, hashlib, json, sys, time
from pathlib import Path
import numpy as np
from mathutils import Vector, Matrix

R=Path(r'D:\Download\Aevrynd')
S=R/'engine/assets/characters/female-next/source'
E=R/'Evidence/character-female-next/r0028-cc0-female-foundation'
E.mkdir(parents=True,exist_ok=True)
SRC=S/'aevrynd-female-next-r0023-b-neutral-review.blend'
REF=R/'Reference/character/blender-human-base-meshes-v1.4.1/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend'
OUT=S/'aevrynd-female-next-r0028-a-cc0-female-foundation.blend'
COLLECTION='Body Female - Realistic'
BODY='GEO-body_female_realistic'
HEAD=1.5624730926266572*.91
TARGET=(0.,-.02,HEAD)

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,obj):(E/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def read(name):return json.loads((E/name).read_text(encoding='utf8'))
def matrix(m):return [float(x) for row in m for x in row]
def mesh_signature(m):
    h=hashlib.sha256()
    for container,field,dtype,n in ((m.vertices,'co','f4',3),(m.loops,'vertex_index','i4',1),(m.polygons,'loop_start','i4',1),(m.polygons,'loop_total','i4',1)):
        a=np.empty(len(container)*n,dtype=dtype);container.foreach_get(field,a);h.update(a.tobytes())
    uv=[]
    for layer in m.uv_layers:
        a=np.empty(len(layer.data)*2,dtype='f4');layer.data.foreach_get('uv',a);uv.append({'name':layer.name,'sha256':hashlib.sha256(a.tobytes()).hexdigest()})
    return {'geometrySha256':h.hexdigest(),'uv':uv,'vertices':len(m.vertices),'polygons':len(m.polygons)}
def evaluated(o,triangles=False):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
    a=np.empty(len(m.vertices)*3,dtype='f4');m.vertices.foreach_get('co',a);a=a.reshape(-1,3).astype('f8');mx=np.array(ev.matrix_world,dtype='f8');a=a@mx[:3,:3].T+mx[:3,3]
    t=None
    if triangles:
        m.calc_loop_triangles();t=np.empty(len(m.loop_triangles)*3,dtype='i4');m.loop_triangles.foreach_get('vertices',t);t=t.reshape(-1,3)
    ev.to_mesh_clear();return a,t
def bounds(o):
    a,_=evaluated(o);return {'min':a.min(0).tolist(),'max':a.max(0).tolist(),'vertices':len(a)}
def eye_center(objects):
    return np.mean([(np.array(bounds(o)['min'])+np.array(bounds(o)['max']))*.5 for o in objects],axis=0)
def clay():
    m=bpy.data.materials.new('AFN28_IdenticalNeutralClay');m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.42,.42,.42,1);p.inputs['Roughness'].default_value=.55;p.inputs['Metallic'].default_value=0;p.inputs['Subsurface Weight'].default_value=0;p.inputs['IOR'].default_value=1.45;m.diffuse_color=(.42,.42,.42,1);return m
def assign(o,m):
    o.data.materials.clear();o.data.materials.append(m)
    for p in o.data.polygons:p.material_index=0
def config(s):
    eevee={p.identifier:getattr(s.eevee,p.identifier) for p in s.eevee.bl_rna.properties if not p.is_readonly and p.type in ('BOOLEAN','INT','FLOAT','STRING','ENUM') and not getattr(p,'is_array',False)}
    return {'engine':s.render.engine,'transform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma,'transparent':s.render.film_transparent,'world':s.world.name if s.world else None,'camera':s.camera.name,'lights':[o.name for o in s.objects if o.type=='LIGHT'],'eevee':eevee}
def setup(s,c):
    s.render.engine=c['engine'];s.view_settings.view_transform=c['transform'];s.view_settings.look=c['look'];s.view_settings.exposure=c['exposure'];s.view_settings.gamma=c['gamma'];s.render.film_transparent=c['transparent'];s.render.threads_mode='FIXED';s.render.threads=4;s.render.image_settings.file_format='PNG';s.render.resolution_x=s.render.resolution_y=800;s.render.resolution_percentage=100
    s.camera=bpy.data.objects[c['camera']];s.world=bpy.data.worlds[c['world']] if c['world'] else None
    for k,v in c['eevee'].items():setattr(s.eevee,k,v)
def camera(view):
    s=bpy.context.scene;c=s.camera
    loc={'face':(0.,-.90,HEAD+.015),'oblique':(.46,-.82,HEAD+.04),'profile':(.86,-.16,HEAD+.02),'body-face':(0.,-4.6,.84),'body-profile':(4.6,-.12,.84)}[view]
    target=TARGET if not view.startswith('body') else (0,0,.78)
    c.location=loc;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=100 if not view.startswith('body') else 85;bpy.context.view_layer.update()
def render(label):
    s=bpy.context.scene;rows=[];original=[(o,o.matrix_world.copy()) for o in s.objects if o.type=='LIGHT']
    for light in ('saved','alternate'):
        if light=='alternate':
            for o,_ in original:o.location.x=-o.location.x;o.rotation_euler=(Vector(TARGET)-o.location).to_track_quat('-Z','Y').to_euler()
        for view in (('face','oblique','profile','body-face','body-profile') if light=='saved' else ('oblique',)):
            camera(view);p=E/f'{label}-{light}-{view}.png';s.render.filepath=str(p);start=time.time();bpy.ops.render.render(write_still=True)
            rows.append({'label':label,'view':view,'light':light,'path':str(p),'cameraMatrix':matrix(s.camera.matrix_world),'lens':s.camera.data.lens,'resolution':[800,800],'engine':s.render.engine,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma,'lights':[(o.name,matrix(o.matrix_world),o.data.energy,list(o.data.color),o.data.type,getattr(o.data,'size',None)) for o,_ in original],'world':s.world.name,'seconds':time.time()-start})
            save(label+'-renders.json',{'rows':rows,'scope':'Actual geometry/clay study, not textured/haired character realism or animation.'})
    for o,m in original:o.matrix_world=m
    camera('face')
def build():
    assert sha(SRC)=='5b9eecfb5d9bcd83790c17de2dfe2919b8c454d003852f117d7dc5abc7fbdf1f'
    assert sha(REF)=='3c121505651140ceb4d69fd1d8923f7788ffadd81672f5be14845a5f2c75c137'
    save('round-contract.json',{'previousGoalTurn':'no model progress: prompt verification only; actual r27 next action remains available','defect':'Repeated procedural changes retain artificial full-head anatomy and hair; isolate whether sculpted female geometry gives a more credible foundation.','hypothesis':'The explicitly CC0 female scan can provide more credible skull/face/ear/neck and body form while retaining editable topology and multires detail.','candidateCount':1,'scope':'Matched clay complete head and full-body geometry review; neutral structure/contact inspection. No hairstyle, texture, rig, engine or whole-character promotion.','reject':'No clear multi-angle anatomy benefit, invalid preserved sculpt/topology, or incompatible data. Contact problems prevent collision qualification even if form is retained for further work.','resources':'One Blender, four threads; 45 minute checkpoint; max Multires level3, 800 square renders.','reference':str(REF),'referenceSha256':sha(REF),'source':str(SRC),'sourceSha256':sha(SRC),'license':'Selected Body Female - Realistic collection explicitly CC0, Dan Ulrich; no other collection imported.'})
    bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene
    rig=bpy.data.objects['AFN_R0005_Rig']
    for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
    for o in bpy.data.objects:
        if o.data and hasattr(o.data,'shape_keys') and o.data.shape_keys:
            for k in list(o.data.shape_keys.key_blocks)[1:]:k.value=0
    visible={'AFN_R0008_Body'}|{o.name for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('AFN6_')}
    for o in s.objects:
        if o.type in ('MESH','CURVE','CURVES','SURFACE'):o.hide_render=o.name not in visible
    m=clay()
    for n in visible:assign(bpy.data.objects[n],m)
    bpy.context.view_layer.update();body=bpy.data.objects['AFN_R0008_Body'];bb=bounds(body);center=eye_center([bpy.data.objects['AFN6_L_Sclera'],bpy.data.objects['AFN6_R_Sclera']]);cfg=config(s);setup(s,cfg)
    save('baseline-controls.json',{'config':cfg,'bodyBounds':bb,'eyeCenter':center.tolist(),'sourceSha256':sha(SRC),'visible':sorted(visible),'clay':{'linearColor':[.42,.42,.42,1],'roughness':.55,'SSS':0,'IOR':1.45}})
    if '--skip-before' not in sys.argv:render('before')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(str(SRC),link=False) as (a,b):b.objects=cfg['lights']+[cfg['camera']];b.worlds=[cfg['world']] if cfg['world'] else []
    for o in b.objects:bpy.context.scene.collection.objects.link(o)
    with bpy.data.libraries.load(str(REF),link=False) as (a,b):
        assert COLLECTION in a.collections;b.collections=[COLLECTION]
    col=b.collections[0];assert col.asset_data and col.asset_data.license=='CC0' and col.asset_data.author=='Dan Ulrich';bpy.context.scene.collection.children.link(col);col.hide_render=False;col.hide_viewport=False
    objects=list(col.all_objects);assert len(objects)==3 and all(o.type=='MESH' for o in objects)
    original={}
    for o in objects:
        o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
        original[o.name]={'mesh':mesh_signature(o.data),'matrix':matrix(o.matrix_world),'parent':o.parent.name if o.parent else None,'drivers':len(o.animation_data.drivers) if o.animation_data else 0,'action':o.animation_data.action.name if o.animation_data and o.animation_data.action else None,'modifiers':[{'type':mod.type,'levels':getattr(mod,'levels',None),'renderLevels':getattr(mod,'render_levels',None),'totalLevels':getattr(mod,'total_levels',None)} for mod in o.modifiers]}
        assert o.parent is None or o.parent in objects
        assert original[o.name]['drivers']==0 and original[o.name]['action'] is None
        assert all(mod.type=='MULTIRES' for mod in o.modifiers)
        for mod in o.modifiers:mod.levels=min(3,mod.total_levels);mod.sculpt_levels=mod.levels;mod.render_levels=mod.levels
    bpy.context.view_layer.update();newbody=bpy.data.objects[BODY];rawbounds=bounds(newbody);newcenter=eye_center([o for o in objects if '.eye.' in o.name]);height=bb['max'][2]-bb['min'][2];rawheight=rawbounds['max'][2]-rawbounds['min'][2];scale=height/rawheight
    # All three objects share one explicit uniform unit/height normalization.
    # Human base meshes face -Y. This is checked through the eye-vs-body ranges
    # and real profile images; no anatomical morph or per-part transform occurs.
    translation=np.array([center[0]-newcenter[0]*scale,center[1]-newcenter[1]*scale,bb['min'][2]-rawbounds['min'][2]*scale])
    common=Matrix.Translation(Vector(translation.tolist()))@Matrix.Scale(scale,4)
    m=clay()
    for o in objects:
        if o.parent is None:o.matrix_world=common@o.matrix_world
    bpy.context.view_layer.update()
    for o in objects:
        assign(o,m);o['AFN28_original_name']=o.name;o['AFN28_author']='Dan Ulrich';o['AFN28_license']='CC0';o['AFN28_source_collection']=COLLECTION
        assert mesh_signature(o.data)==original[o.name]['mesh']
    setup(bpy.context.scene,cfg);bpy.context.view_layer.update();camera('face');s=bpy.context.scene;s['AFN28_status']='UNRIGGED_CC0_SCAN_FOUNDATION_STUDY_NOT_CURRENT_HEAD_OR_RUNTIME';s['AFN28_source_sha256']=sha(REF);s['AFN28_author']='Dan Ulrich';s['AFN28_license']='CC0';s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
    save('append-dependencies.json',{'texts':[{'name':t.name,'users':t.users,'length':len(t.as_string())} for t in bpy.data.texts],'libraries':[{'name':l.name,'path':l.filepath,'users':l.users} for l in bpy.data.libraries]})
    # Appending can leave unused library identifiers. Remove only true orphans.
    bpy.data.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
    linked=[{'name':i.name_full,'type':type(i).__name__,'library':i.library.filepath} for i in bpy.data.user_map() if i.library]
    save('linked-data-inspection.json',{'linkedIDs':linked,'libraryUsers':{l.name:[i.name_full for i in bpy.data.user_map().get(l,set())] for l in bpy.data.libraries}})
    assert not linked,linked
    for library in list(bpy.data.libraries):bpy.data.libraries.remove(library)
    assert len(bpy.data.texts)==0 and len(bpy.data.libraries)==0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save('build-verification.json',{'output':str(OUT),'outputSha256':sha(OUT),'reference':str(REF),'referenceSha256':sha(REF),'source':str(SRC),'sourceSha256':sha(SRC),'author':'Dan Ulrich','license':'CC0','selectedCollection':COLLECTION,'originalObjects':original,'rawBodyBounds':rawbounds,'rawEyeCenter':newcenter.tolist(),'uniformScale':scale,'translationM':translation.tolist(),'sharedNormalizationMatrix':matrix(common),'normalizedBodyBounds':bounds(newbody),'normalizedEyeCenter':eye_center([o for o in objects if '.eye.' in o.name]).tolist(),'alignment':'Same body height and feet Z; eye-center XY. No per-part transform, face shape edit, remesh or applied Multires.','config':cfg,'preservedRawGeometryUV':True,'externalLibraries':len(bpy.data.libraries),'textBlocks':len(bpy.data.texts),'scope':'Independent unrigged female geometry foundation. Hair, skin maps, expression rig, contact qualification and engine missing.'})
    render('after');print('R0028_FOUNDATION_DONE',flush=True)

if __name__=='__main__':build()
