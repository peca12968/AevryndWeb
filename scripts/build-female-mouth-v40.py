import math
from pathlib import Path
import bpy
from mathutils import Matrix, Vector

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'assets-source'/'aevrynd-character'/'aevrynd-female-authoring-v39.blend'
OUTPUT=ROOT/'assets-source'/'aevrynd-character'/'aevrynd-female-authoring-v40.blend'
OUT=ROOT.parent/'Temp'/'female-realism'/'mouth-v40'
BUILD=ROOT/'.character-build'/'aevrynd-female-authoring-v40.glb'
LOD1=ROOT/'.character-build'/'aevrynd-female-authoring-v40-lod1.glb'

def material(name,color,roughness):
    mat=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes=True
    shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    shader.inputs['Base Color'].default_value=(*color,1)
    shader.inputs['Roughness'].default_value=roughness
    shader.inputs['Specular IOR Level'].default_value=.22
    mat['aevrynd_runtime_owned']=True
    return mat

def bind(obj,rig,role):
    obj['aevrynd_role']=role; obj['aevrynd_face_revision']=40
    obj.parent=rig; obj.parent_type='BONE'; obj.parent_bone='head'; obj.matrix_world=Matrix.Identity(4)

def ellipse_component(verts,faces,center,radii,segments=16,rings=6):
    base=len(verts)
    for r in range(1,rings):
        phi=-math.pi/2+math.pi*r/rings
        for s in range(segments):
            th=math.tau*s/segments
            verts.append((center[0]+radii[0]*math.cos(phi)*math.cos(th),center[1]+radii[1]*math.cos(phi)*math.sin(th),center[2]+radii[2]*math.sin(phi)))
    bottom=len(verts); verts.append((center[0],center[1],center[2]-radii[2]))
    top=len(verts); verts.append((center[0],center[1],center[2]+radii[2]))
    for r in range(rings-2):
        a=base+r*segments; b=a+segments
        for s in range(segments): faces.append((a+s,a+(s+1)%segments,b+(s+1)%segments,b+s))
    for s in range(segments):
        faces.append((bottom,base+(s+1)%segments,base+s))
        a=base+(rings-2)*segments; faces.append((top,a+s,a+(s+1)%segments))

def mesh_object(name,verts,faces,mat,rig,role):
    old=bpy.data.objects.get(name)
    if old: bpy.data.objects.remove(old,do_unlink=True)
    mesh=bpy.data.meshes.new(name+'MeshV40'); mesh.from_pydata(verts,[],faces); mesh.materials.append(mat)
    for p in mesh.polygons:p.use_smooth=True
    obj=bpy.data.objects.new(name,mesh); bpy.context.scene.collection.objects.link(obj); bind(obj,rig,role); return obj

def oral_cup(rig):
    verts=[]; faces=[]; seg=48
    rings=[(-.1065,.0220,.0030),(-.099,.026,.009),(-.089,.024,.012),(-.079,.017,.009)]
    for y,rx,rz in rings:
        for i in range(seg):
            a=math.tau*i/seg
            verts.append((rx*math.cos(a),y,1.5342+rz*math.sin(a)))
    for r in range(len(rings)-1):
        for i in range(seg):
            a=r*seg+i;b=r*seg+(i+1)%seg;c=(r+1)*seg+(i+1)%seg;d=(r+1)*seg+i
            faces.append((a,d,c,b))
    back=len(verts);verts.append((0,-.077,1.5342))
    for i in range(seg): faces.append((back,(len(rings)-1)*seg+i,(len(rings)-1)*seg+(i+1)%seg))
    return mesh_object('Mouth_OralCavity',verts,faces,material('Aevrynd_OralCavity_v40',(.075,.006,.008),.66),rig,'oral_cavity_cup')

def teeth(rig):
    verts=[];faces=[]
    xs=(-.0118,-.0078,-.0032,.0032,.0078,.0118)
    for i,x in enumerate(xs):
        ellipse_component(verts,faces,(x,-.0860,1.5370),(0.00255 if i in (2,3) else .00235,.00115,.00225),14,6)
    return mesh_object('Mouth_UpperTeeth',verts,faces,material('Aevrynd_Teeth_v40',(.78,.69,.56),.31),rig,'upper_teeth')

def tongue(rig):
    verts=[];faces=[];ellipse_component(verts,faces,(0,-.086,1.5288),(.015,.0045,.0028),24,8)
    return mesh_object('Mouth_Tongue',verts,faces,material('Aevrynd_Tongue_v40',(.31,.045,.055),.43),rig,'tongue')

def smooth_wetline(rig):
    old=bpy.data.objects.get('Mouth_WetLine')
    if old:bpy.data.objects.remove(old,do_unlink=True)
    verts=[];faces=[];n=65
    for i in range(n):
        t=i/(n-1)*2-1; x=.0275*t
        taper=max(0,1-abs(t)**2.4); center=1.53472+.00018*math.cos(math.pi*t)
        half=.00010+.00022*taper
        y=-.1420+.0003*abs(t)**1.8
        verts.extend(((x,y,center-half),(x,y,center+half)))
    for i in range(n-1):
        a=2*i;faces.append((a,a+2,a+3,a+1))
    return mesh_object('Mouth_WetLine',verts,faces,material('Aevrynd_MouthWetLine_v40',(.035,.002,.003),.27),rig,'mouth_wet_margin')

def rebuild_lip(name,upper,rig):
    old=bpy.data.objects.get(name)
    if old:bpy.data.objects.remove(old,do_unlink=True)
    verts=[];faces=[];n=65
    # Three continuous front rows form a rounded vermilion surface without the
    # exposed side caps of the legacy crescent meshes.
    for i in range(n):
        t=i/(n-1)*2-1; x=.0280*t; envelope=max(0,1-abs(t)**1.65)
        inner=1.53472 + (.00016 if upper else -.00016)*envelope
        if upper:
            peaks=math.exp(-((abs(t)-.34)/.20)**2)
            outer=1.53472 + envelope*(.00265+.00165*peaks-.00055*math.exp(-(t/.16)**2))
        else:
            outer=1.53472-envelope*(.00355-.00050*math.exp(-(t/.28)**2))
        middle=outer+(inner-outer)*.52
        y_outer=-.1382-.0006*envelope; y_mid=-.1408-.0005*envelope; y_inner=-.1393-.0003*envelope
        verts.extend(((x,y_outer,outer),(x,y_mid,middle),(x,y_inner,inner)))
    for i in range(n-1):
        a=3*i;faces.extend(((a,a+3,a+4,a+1),(a+1,a+4,a+5,a+2)))
    color=(.255,.061,.055) if upper else (.285,.075,.068)
    return mesh_object(name,verts,faces,material('Aevrynd_'+('LipUpper' if upper else 'LipLower')+'_v40',color,.49),rig,'upper_lip_volume' if upper else 'lower_lip_volume')

def mouth_alpha(body):
    # The retained Multires base has no lip-loop topology.  Vertex-alpha holes
    # expose entire coarse triangles and fail close-up review, so v40 keeps the
    # skin opaque and records that a real opening still needs retopology.
    body['aevrynd_mouth_alpha_vertices']=0
    body['aevrynd_mouth_opening_state']='opaque_multires_safe'

def look_at(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()

def export_runtime(path,rig,excluded=()):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.data.objects:
        if obj.type in {'MESH','ARMATURE'} and obj.name not in excluded:
            obj.hide_render=False;obj.select_set(True)
    bpy.context.view_layer.objects.active=rig
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_extras=True,export_animations=True,export_frame_range=True,export_attributes=True,export_vertex_color='ACTIVE')

bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.preferences.filepaths.save_version=0
rig=bpy.data.objects['AevryndFemaleRig'];body=bpy.data.objects['AevryndFemaleBodyBase']
mouth_alpha(body); rebuild_lip('Lip_Upper',True,rig); rebuild_lip('Lip_Lower',False,rig); oral_cup(rig); teeth(rig); tongue(rig); smooth_wetline(rig)
bpy.context.scene['aevrynd_face_revision']=40
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
OUT.mkdir(parents=True,exist_ok=True);scene=bpy.context.scene;scene.frame_set(1);scene.render.engine='BLENDER_EEVEE';scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
cam=bpy.data.objects['Aevrynd Review Camera']
for name,loc,target,lens,w,h in [('mouth-close',(0,-.43,1.525),(0,-.105,1.525),120,1000,700),('face-front',(0,-.72,1.575),(0,-.005,1.555),96,900,900),('face-three-quarter',(.28,-.64,1.58),(0,0,1.55),96,900,900)]:
    scene.render.resolution_x=w;scene.render.resolution_y=h;cam.data.lens=lens;cam.location=loc;look_at(cam,target);scene.render.filepath=str(OUT/f'{name}.png');bpy.ops.render.render(write_still=True)
BUILD.parent.mkdir(parents=True,exist_ok=True)
multires=next(m for m in body.modifiers if m.type=='MULTIRES');levels=(multires.levels,multires.sculpt_levels,multires.render_levels);multires.levels=multires.sculpt_levels=multires.render_levels=0
export_runtime(BUILD,rig);export_runtime(LOD1,rig,{'HairMain','HairFlyaways'})
multires.levels,multires.sculpt_levels,multires.render_levels=levels
print('AEVRYND_MOUTH_V40='+str({'alpha_vertices':body['aevrynd_mouth_alpha_vertices'],'objects':['Mouth_OralCavity','Mouth_UpperTeeth','Mouth_Tongue','Mouth_WetLine']}))
