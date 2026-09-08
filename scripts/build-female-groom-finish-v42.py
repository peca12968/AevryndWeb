import json
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'assets-source'/'aevrynd-character'/'aevrynd-female-authoring-v41.blend'
OUTPUT=ROOT/'assets-source'/'aevrynd-character'/'aevrynd-female-authoring-v42.blend'
BUILD=ROOT/'.character-build'/'aevrynd-female-authoring-v42.glb';LOD1=ROOT/'.character-build'/'aevrynd-female-authoring-v42-lod1.glb'
RENDER_DIR=ROOT.parent/'Temp'/'female-realism'/'groom-v42'

def prune_tail_fibers(obj,stride,sides):
    remove=set();removed=0
    for start in range(0,len(obj.data.vertices)-stride+1,stride):
        rows=stride//sides
        points=[sum((obj.matrix_world@obj.data.vertices[start+r*sides+k].co for k in range(sides)),Vector())/sides for r in range(rows)]
        if points[-1].z<1.585 and (points[0].y>-.04 or abs(points[0].x)>.075):
            remove.update(range(start,start+stride));removed+=1
    old=obj.data;mapping={index:new for new,index in enumerate(i for i in range(len(old.vertices)) if i not in remove)}
    vertices=[old.vertices[i].co.copy() for i in range(len(old.vertices)) if i not in remove]
    faces=[];material_indices=[];smooth=[]
    for polygon in old.polygons:
        if any(index in remove for index in polygon.vertices):continue
        faces.append(tuple(mapping[index] for index in polygon.vertices));material_indices.append(polygon.material_index);smooth.append(polygon.use_smooth)
    mesh=bpy.data.meshes.new(obj.name+'MeshV42');mesh.from_pydata(vertices,[],faces)
    for mat in old.materials:mesh.materials.append(mat)
    for polygon,material_index,use_smooth in zip(mesh.polygons,material_indices,smooth):polygon.material_index=material_index;polygon.use_smooth=use_smooth
    obj.data=mesh
    if old.users==0:bpy.data.meshes.remove(old)
    obj['aevrynd_groom_revision']=42;obj['aevrynd_removed_tail_fibers']=removed
    return removed

def tune_card_material():
    source=bpy.data.materials['Aevrynd_Hair_Clumps_v41'];mat=source.copy();mat.name='Aevrynd_Hair_Clumps_v42'
    shader=next(node for node in mat.node_tree.nodes if node.type=='BSDF_PRINCIPLED')
    shader.inputs['Roughness'].default_value=.61;shader.inputs['Specular IOR Level'].default_value=.09
    if shader.inputs.get('Anisotropic IOR Level'):shader.inputs['Anisotropic IOR Level'].default_value=.30
    mat['aevrynd_runtime_owned']=True
    for name in ('HairClumpsLarge','HairClumpsMediumCards'):
        slots=bpy.data.objects[name].data.materials;slots.clear();slots.append(mat);bpy.data.objects[name]['aevrynd_groom_revision']=42
    return mat

def look_at(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
def render(camera,name,location,target):
    scene=bpy.context.scene;scene.frame_set(1);scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.filepath=str(RENDER_DIR/f'{name}.png');camera.data.lens=82;camera.location=location;look_at(camera,target);bpy.ops.render.render(write_still=True)
def export(path,rig,excluded=()):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.data.objects:
        if obj.type in {'MESH','ARMATURE'} and obj.name not in excluded:obj.hide_render=False;obj.select_set(True)
    bpy.context.view_layer.objects.active=rig
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_extras=True,export_animations=True,export_frame_range=True,export_attributes=True,export_vertex_color='ACTIVE')

bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.preferences.filepaths.save_version=0;RENDER_DIR.mkdir(parents=True,exist_ok=True);BUILD.parent.mkdir(parents=True,exist_ok=True)
removed={name:prune_tail_fibers(bpy.data.objects[name],stride,sides) for name,stride,sides in (('HairMain',27,3),('HairGuides',24,3),('HairFlyaways',27,3))}
tune_card_material();bpy.context.scene['aevrynd_hair_revision']=42;bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
camera=bpy.data.objects['Aevrynd Review Camera']
for name,location,target in (('female-groom-front',(0,-.72,1.575),(0,-.005,1.555)),('female-groom-three-quarter',(.28,-.64,1.58),(0,0,1.55)),('female-groom-left',(-.66,-.05,1.575),(0,0,1.545)),('female-groom-right',(.66,-.05,1.575),(0,0,1.545)),('female-groom-back',(0,.76,1.575),(0,.01,1.545))):render(camera,name,location,target)
body=bpy.data.objects['AevryndFemaleBodyBase'];rig=bpy.data.objects['AevryndFemaleRig'];multires=next(m for m in body.modifiers if m.type=='MULTIRES');levels=(multires.levels,multires.sculpt_levels,multires.render_levels);multires.levels=multires.sculpt_levels=multires.render_levels=0
export(BUILD,rig);export(LOD1,rig,{'HairMain','HairFlyaways','HairGuides','HairClumpsMediumCards'});multires.levels,multires.sculpt_levels,multires.render_levels=levels
print('AEVRYND_GROOM_V42_REPORT='+json.dumps({'state':'AUTHORING','removed_tail_fibers':removed,'runtime_glb':str(BUILD),'lod1_glb':str(LOD1)}))
