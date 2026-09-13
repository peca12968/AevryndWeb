import json, math, random
from pathlib import Path
import bpy
from mathutils import Matrix, Vector
from mathutils.kdtree import KDTree

ROOT=Path(__file__).resolve().parents[1]; ASSETS=ROOT/'assets-source/aevrynd-character'
SOURCE=ASSETS/'aevrynd-female-authoring-v249-mainline-fitted-upper-lip-r475.blend'
OUTPUT=ASSETS/'aevrynd-female-authoring-v249-mainline-refined-anatomical-brows-r478.blend'
REPORT=ASSETS/'female-v249-mainline-refined-anatomical-brows-r478.build-report.json'
REVIEW=ASSETS/'reviews/v249r478-refined-anatomical-brows'; BODY='AevryndFemaleBodyBaseV118'; RIG='AevryndFemaleRig'

def look_at(o,t): o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
def make_mat(name,color,roughness):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True
 s=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');s.inputs['Base Color'].default_value=(*color,1);s.inputs['Roughness'].default_value=roughness;s.inputs['Specular IOR Level'].default_value=.22
 m['aevrynd_layer']='material.keratin.eyebrow';m['aevrynd_revision']='v249r478';return m

def surface_lookup(body):
 dg=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dg);mesh=ev.to_mesh();pts=[ev.matrix_world@v.co for v in mesh.vertices];tree=KDTree(len(pts))
 for i,p in enumerate(pts):tree.insert((p.x,p.z,0),i)
 tree.balance()
 def front_y(x,z,r=.0022):
  hits=tree.find_range((x,z,0),r)
  if hits:return min(pts[i].y for _co,i,_d in hits)
  _co,i,_d=tree.find((x,z,0));return pts[i].y
 return ev,front_y

def path_z(t,side):
 side_delta=.00018 if side=='L' else -.00012;arch=math.sin(math.pi*min(1,t/.88)) if t<.88 else 0;tail=max(0,(t-.62)/.38)
 return 1.62515+side_delta+.00535*arch-.00215*tail*tail

def angle(t,rng):
 if t<.17:base=math.radians(82-85*t);spread=math.radians(8)
 elif t<.55:u=(t-.17)/.38;base=math.radians(57-38*u);spread=math.radians(5)
 else:u=(t-.55)/.45;base=math.radians(19-39*u);spread=math.radians(4)
 return base+rng.gauss(0,spread)

def create_brow(side,front_y,rig,mats):
 rng=random.Random(47801 if side=='L' else 47802);sign=1 if side=='L' else -1;fibers=[];count=420
 for i in range(count):
  t=min(1,max(0,(i+rng.uniform(.05,.95))/count));x=sign*(.0149+.0394*t);half=.00135+.00070*math.sin(math.pi*t)+.00025*(1-t)
  z=path_z(t,side)+max(-1,min(1,rng.gauss(0,.48)))*half+.00022*math.sin(i*2.399+(.4 if side=='L' else 1.2))
  clearance=.00014+rng.uniform(0,.00007);y=front_y(x,z)-clearance;a=angle(t,rng);med=min(1,t/.10);tail=min(1,(1-t)/.16);sil=max(.38,min(med,tail))
  length=(.00245+.00080*math.sin(math.pi*t))*sil*max(.72,min(1.25,rng.gauss(1,.12)));dx=sign*length*math.cos(a);dz=length*math.sin(a);lift=.00020+.00012*rng.random()
  coords=((x,y,z),(x+dx*.34,y-lift*.40,z+dz*.32),(x+dx*.72,y-lift*.78,z+dz*.73),(x+dx,y-lift,z+dz));fibers.append((coords,(.78,.58,.30,.04),0 if rng.random()<.72 else 1,clearance))
 data=bpy.data.curves.new(f'AevryndFemaleBrow_{side}_R478_Geometry','CURVE');data.dimensions='3D';data.resolution_u=2;data.bevel_depth=.000038;data.bevel_resolution=2
 for m in mats:data.materials.append(m)
 for coords,radii,mi,_ in fibers:
  sp=data.splines.new('POLY');sp.points.add(3);sp.material_index=mi
  for p,co,r in zip(sp.points,coords,radii):p.co=(*co,1);p.radius=r
 obj=bpy.data.objects.new(f'AevryndFemaleBrow_{side}_R478',data);bpy.context.scene.collection.objects.link(obj);world=Matrix.Identity(4);obj.parent=rig;obj.parent_type='BONE';obj.parent_bone='head';obj.matrix_world=world
 obj['aevrynd_layer']=f'face.{side.lower()}.eyebrow_fibers';obj['aevrynd_revision']='v249r478';obj['aevrynd_binding']='rig.head';obj['aevrynd_method']='stochastic anatomical head-body-tail direction field; surface fitted tapered fibers';return obj,fibers

def render(scene,cam,frame,name,location,target,lens,size):
 scene.frame_set(frame);bpy.context.view_layer.update();cam.location=location;cam.data.lens=lens;look_at(cam,target);scene.render.resolution_x,scene.render.resolution_y=size;scene.render.filepath=str(REVIEW/f'{name}.png');bpy.ops.render.render(write_still=True)

bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.preferences.filepaths.save_version=0;scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();body=bpy.data.objects[BODY];rig=bpy.data.objects[RIG]
for name in ('Brow_L','Brow_R','Brow_L_Density','Brow_R_Density'):
 old=bpy.data.objects.get(name)
 if old:old.hide_render=True;old.hide_viewport=True
ev,front_y=surface_lookup(body);mats=(make_mat('Aevrynd_BrowFiber_DeepBrown_R478',(.020,.0065,.0032),.48),make_mat('Aevrynd_BrowFiber_WarmBrown_R478',(.040,.014,.0065),.52));created={}
for side in ('L','R'):
 obj,fibers=create_brow(side,front_y,rig,mats);created[obj.name]={'fibers':len(fibers),'pointsPerFiber':4,'minimumAuthoredRootClearanceMm':min(f[3] for f in fibers)*1000,'maximumAuthoredRootClearanceMm':max(f[3] for f in fibers)*1000}
ev.to_mesh_clear();scene.render.engine='BLENDER_EEVEE';scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
if scene.world and scene.world.use_nodes:
 bg=next((n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND'),None)
 if bg:bg.inputs['Strength'].default_value=.15
lights={'Aevrynd Review Face Fill':4.5,'Aevrynd Review Fill':10.0,'Aevrynd Review Hair Rim':12.0,'Aevrynd Review Key':15.0,'Aevrynd Review Top':9.0}
for name,energy in lights.items():
 light=bpy.data.objects.get(name)
 if light and light.type=='LIGHT':light.data.energy=energy;light.data.color=(1,1,1)
scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene['aevrynd_mainline_revision']='v249r478-refined-anatomical-brows';scene['aevrynd_mainline_parent']=SOURCE.name;scene['aevrynd_release_state']='ANATOMICAL_BROW_VISUAL_AND_COLLISION_REVIEW_PENDING';scene['aevrynd_review_lighting_contract']='Standard/None exposure0 gamma1 world0.15 fixed neutral five-light rig';REVIEW.mkdir(parents=True,exist_ok=True)
cam=bpy.data.objects.get('Aevrynd R249 Review Camera') or bpy.data.objects['Aevrynd Review Camera'];scene.camera=cam
views=((1,'01-face-front-f01',(0,-.56,1.585),(0,-.06,1.585),108,(1100,1100)),(1,'02-eyes-f01',(0,-.45,1.615),(0,-.125,1.615),118,(1300,750)),(1,'03-three-quarter-f01',(.40,-.57,1.58),(0,-.03,1.56),92,(1000,1000)),(20,'04-face-front-f20',(0,-.56,1.585),(0,-.06,1.585),108,(1100,1100)),(20,'05-three-quarter-f20',(.40,-.57,1.58),(0,-.03,1.56),92,(1000,1000)))
for v in views:render(scene,cam,*v)
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT));report={'source':str(SOURCE),'output':str(OUTPUT),'createdLayers':created,'hiddenLegacyLayers':['Brow_L','Brow_R','Brow_L_Density','Brow_R_Density'],'geometryChangedOutsideBrows':False,'reviewLightingContract':{'viewTransform':'Standard','look':'None','exposure':0,'gamma':1,'worldStrength':.15,'lights':lights},'reviewDirectory':str(REVIEW),'status':'STRICT_VISUAL_AND_COLLISION_REVIEW_REQUIRED'};REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8');print('AEVRYND_V249R478_ANATOMICAL_BROWS='+json.dumps(report,sort_keys=True))
