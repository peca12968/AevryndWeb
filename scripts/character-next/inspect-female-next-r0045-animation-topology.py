"""Inspect already-local CC0 animation topology as a manufacturing reference.
No character or asset promotion, no downloaded code, no male character work.
"""
import bpy,json,time,hashlib
from pathlib import Path
from mathutils import Vector
import numpy as np
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0045-closed-lid-topology';E.mkdir(exist_ok=True)
LIB=R/'Reference/character/blender-human-base-meshes-v1.4.1/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def points(o):return np.array([o.matrix_world@v.co for v in o.data.vertices])
def main():
    tick=time.time();assert sha(LIB)=='3c121505651140ceb4d69fd1d8923f7788ffadd81672f5be14845a5f2c75c137';bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(str(LIB),link=False) as (src,dst):dst.collections=['Head (Animation) - Realistic']
    col=dst.collections[0];bpy.context.scene.collection.children.link(col)
    for collection in (col,*col.children_recursive):collection.hide_render=False;collection.hide_viewport=False
    bpy.context.view_layer.update();head=next(o for o in col.all_objects if o.name=='GEO-head_animation_realistic');eyes=[o for o in col.all_objects if '.sclera.' in o.name];P=points(head);centers={o.name:points(o).mean(0).tolist() for o in eyes};cc=np.mean(list(centers.values()),axis=0);lo=P.min(0);hi=P.max(0)
    mat=bpy.data.materials.new('CC0_REFERENCE_INSPECTION_CLAY');mat.use_nodes=True;p=mat.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.42,.34,.29,1);p.inputs['Roughness'].default_value=.65
    for o in list(col.all_objects):
        if o.type=='MESH':o.hide_render=False;o.hide_set(False);o.data.materials.clear();o.data.materials.append(mat)
    s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=16;s.render.threads_mode='FIXED';s.render.threads=4;s.render.resolution_x=s.render.resolution_y=800;s.render.resolution_percentage=100;s.world=bpy.data.worlds.new('reference');s.world.use_nodes=True;s.world.node_tree.nodes.get('Background').inputs[0].default_value=(.1,.1,.1,1)
    cam=bpy.data.objects.new('reference_camera',bpy.data.cameras.new('reference_camera'));s.collection.objects.link(cam);s.camera=cam;cam.location=Vector(cc)+Vector((0,-float(hi[2]-lo[2])*3.2,.01));target=Vector((cc[0],cc[1],(lo[2]+hi[2])*.5));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=70
    for name,pos,power,size in [('key',(-.4,-.5,.6),500.,.5),('fill',(.4,-.2,.2),200.,.4)]:
        o=bpy.data.objects.new(name,bpy.data.lights.new(name,'AREA'));s.collection.objects.link(o);o.location=Vector(cc)+Vector(pos);o.rotation_euler=(Vector(cc)-o.location).to_track_quat('-Z','Y').to_euler();o.data.energy=power;o.data.shape='DISK';o.data.size=size
    s.render.filepath=str(E/'cc0-reference-animation-head.png');bpy.ops.render.render(write_still=True)
    write('cc0-animation-topology-inspection.json',{'library':str(LIB),'librarySha256':sha(LIB),'collection':col.name,'author':col.asset_data.author if col.asset_data else None,'license':col.asset_data.license if col.asset_data else None,'description':col.asset_data.description if col.asset_data else None,'object':head.name,'vertices':len(head.data.vertices),'polygons':len(head.data.polygons),'eyeCenters':centers,'headBounds':[lo.tolist(),hi.tolist()],'modifiers':[{'name':m.name,'type':m.type,'levels':getattr(m,'levels',None)} for m in head.modifiers],'use':'Already-local verified CC0 animation edge flow reference; no whole-head replacement, no male asset development, not an own production render.','seconds':time.time()-tick});np.savez_compressed(E/'cc0-reference-animation-native.npz',positions=P,edges=np.array([e.vertices[:] for e in head.data.edges]),polygons=np.array([p.vertices[:] for p in head.data.polygons],dtype=object));print('R45_REFERENCE_TOPOLOGY',cc,lo,hi,time.time()-tick,flush=True)
if __name__=='__main__':main()
