"""Density-shaped two-level brow fibres; original skin, pigment and hair held."""
import bpy,json,math,random,hashlib,importlib.util,time,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('inspect_brow',Path(__file__).with_name('inspect-female-next-r0018-brows.py'));inspect=importlib.util.module_from_spec(spec);spec.loader.exec_module(inspect)
R,S,E,SRC=inspect.R,inspect.S,inspect.E,inspect.SRC;base=inspect.base;solid=base.v14.solid
VARIANT='c' if '--triangulated' in sys.argv else 'b' if '--clean' in sys.argv else 'a'
DST=S/('aevrynd-female-next-r0018-c-triangulated-brows-study.blend' if VARIANT=='c' else 'aevrynd-female-next-r0018-b-clean-layered-brows-study.blend' if VARIANT=='b' else 'aevrynd-female-next-r0018-a-layered-brows-study.blend')
def save(name,data):inspect.save(name,data)
def sha(p):return inspect.sha(p)
def controls():
    state=base.snapshot();state['meshes']={k:v for k,v in state['meshes'].items() if not k.startswith('AFN11_')}
    hair={}
    for o in bpy.data.objects:
        if o.type=='CURVES':
            p=np.empty(len(o.data.points)*3,np.float32);o.data.position_data.foreach_get('vector',p);hair[o.name]={'positionsSha256':hashlib.sha256(p.tobytes()).hexdigest(),'signature':base.v14.strand_signature(o)}
    state['hair']=hair
    return state

def build():
    assert VARIANT=='a','Use repair-female-next-r0018-self-crossings.py for candidate B'
    start=time.time();bpy.ops.wm.open_mainfile(filepath=str(SRC));rig=bpy.data.objects['AFN_R0005_Rig'];solid.stage.set_pose(rig,'neutral');before=controls()
    save('candidate-a-contract.json',{'source':str(SRC),'sourceSha256':sha(SRC),'diagnosis':'Saved dark-pigment graph is connected and visible. Constant dark diffuse material remains sparse in the full face; changing pigment alone does not solve the low image coverage. Emission diagnostic confirms the same fine-stroke footprint.','hypothesis':'A central-density follicle field with short under-fibres, longer directional fibres and feathered inner/outer boundaries improves brow readability without turning it into a flat stripe.','changes':['650 placement attempts per brow, bounded and collision-rejected, rather than unbounded density.','Smoothly denser central root distribution with tapered tails.','Two length/lift levels and coherent upright-to-outward growth.'],'held':['Original brow material and pigment palette','Skin/head/eyes/lashes/hair geometry and shading','Camera/light/exposure'],'rejectIf':['Any body/component/self crossing in tested poses.','Brows become a solid strip or coarse comb.','No visible full-face improvement at matching views.'],'resources':{'threads':4,'maximumFibres':1300,'attemptsPerFibre':20,'minimumAcceptedPerBrow':500,'staticPoses':5}})
    body=bpy.data.objects['AFN_R0008_Body'];V,T,bodytree=solid.data(body);m=body.data;material=bpy.data.materials['AFN11_BrowKeratin'];rng=random.Random(1818);bindings=[];rows=[]
    def front(x,z):return bodytree.ray_cast(Vector((x,-.5,z)),Vector((0,1,0)),.7)
    for side,sign in (('L',1),('R',-1)):
        vertices=[];faces=[];weights=[];pigment=[];accepted=None;rejects=0;rootrecords=[]
        for hair in range(650):
            chosen=None;under=hair<160
            for trial in range(20):
                t=.025+.945*rng.betavariate(1.45,1.70);x=sign*(.014+.038*t)
                centre=1.4745+.0038*math.sin(math.pi*(.10+.80*t))-.0010*t
                width=.00065+.00145*math.sin(math.pi*t)**.7
                band=max(-1.,min(1.,rng.gauss(-.20 if under else 0.,.38 if under else .48)));z=centre+band*width
                length=rng.uniform(.0013,.0026) if under else rng.uniform(.0028,.0048);length*=1-.28*t
                radius=rng.uniform(.000028,.000039) if under else rng.uniform(.000034,.000051)
                lift=rng.uniform(.000035,.00010) if under else rng.uniform(.00011,.00029)
                lateral=.20+.80*t;slope=(.0038*.80*math.pi*math.cos(math.pi*(.10+.80*t))-.0010)/.038
                up=.80*(1-t)**2+slope*lateral-.25*band;norm=math.hypot(lateral,up);dx=sign*length*lateral/norm;dz=length*up/norm
                centres=[];normals=[];valid=True
                for j in range(8):
                    u=j/7;hit,n,ti,d=front(x+dx*u,z+dz*u*(1-.15*u))
                    if hit is None or hit.y>-.07:valid=False;break
                    centres.append(hit+n*(radius+.000040+lift*math.sin(math.pi*u)));normals.append(n)
                if not valid:continue
                P=[];F=[]
                for j,p in enumerate(centres):
                    tangent=(centres[min(j+1,7)]-centres[max(0,j-1)]).normalized();axis=tangent.cross(normals[j]).normalized();second=tangent.cross(axis).normalized();r=radius*(1-j/7)**.75+.000001
                    for k in range(5):
                        a=math.tau*k/5;P.append(p+r*(math.cos(a)*axis+math.sin(a)*second))
                for j in range(7):
                    for k in range(5):q=(k+1)%5;F.append((j*5+k,j*5+q,(j+1)*5+q,(j+1)*5+k))
                F.append(tuple(reversed(range(5))));F.append(tuple(35+k for k in range(5)))
                tree=BVHTree.FromPolygons(P,F,epsilon=.000001)
                if bodytree.overlap(tree) or (accepted and accepted.overlap(tree)):rejects+=1;continue
                chosen=(P,F,centres[0],radius,length);break
            if chosen is None:continue
            P,F,root,radius,length=chosen;hit,n,ti,d=bodytree.find_nearest(root);ids=list(T[ti]);bc=solid.stage.barycentric(hit,*[V[i] for i in ids]) if hasattr(solid.stage,'barycentric') else None
            if bc is None:
                tri=np.array([tuple(V[i]) for i in ids]);solution=np.linalg.lstsq(np.column_stack((tri[1]-tri[0],tri[2]-tri[0])),np.array(hit)-tri[0],rcond=None)[0];bc=[float(1-solution.sum()),float(solution[0]),float(solution[1])]
            groups={}
            for vi,w in zip(ids,bc):
                for g in m.vertices[vi].groups:
                    name=body.vertex_groups[g.group].name
                    if name in rig.data.bones:groups[name]=groups.get(name,0)+float(w)*g.weight
            total=sum(groups.values());groups={k:v/total for k,v in groups.items() if v>1.e-8};offset=len(vertices);vertices+=P;faces.extend(tuple(offset+i for i in f) for f in F);weights.extend([groups]*len(P));pigment.extend([rng.random()]*len(P))
            rootrecords.append({'object':f'AFN11_{side}_BrowFibres','hair':offset//40,'firstVertex':offset,'vertices':40,'bodyTriangle':int(ti),'bodyVertices':ids,'barycentric':list(bc),'root':list(root),'rootNormal':list(n),'rootGapM':d,'radiusM':radius,'lengthM':length,'kind':'under' if under else 'directional','boneWeights':groups})
            accepted=BVHTree.FromPolygons(vertices,faces,epsilon=.000001)
        assert len(vertices)//40>=500,(side,len(vertices)//40)
        o=bpy.data.objects[f'AFN11_{side}_BrowFibres'];mesh=bpy.data.meshes.new(f'AFN18_{side}_LayeredBrowFibres');mesh.from_pydata(vertices,[],faces);mesh.update();mesh.materials.append(material);attr=mesh.attributes.new('AFN11_BrowPigment','FLOAT','POINT');attr.data.foreach_set('value',pigment);o.data=mesh
        o.vertex_groups.clear();vg={name:o.vertex_groups.new(name=name) for name in sorted({name for w in weights for name in w})}
        for i,w in enumerate(weights):
            for name,value in w.items():vg[name].add([i],value,'REPLACE')
        for p in mesh.polygons:p.use_smooth=True
        o['aevrynd_revision']='female-next-r0018-a';o['aevrynd_root_binding']='aevrynd-female-next-r0018-a-brow-bindings.json'
        bindings.extend(rootrecords);rows.append({'object':o.name,'fibres':len(vertices)//40,'vertices':len(vertices),'triangles':sum(len(p.vertices)-2 for p in mesh.polygons),'placementRejections':rejects})
        print('R0018_BROW '+json.dumps(rows[-1]),flush=True)
    assert controls()==before
    scene=bpy.context.scene;scene['aevrynd_revision']='female-next-r0018-a';scene['aevrynd_release_state']='LAYERED_BROW_STUDY_PENDING_SAVED_AND_VISUAL_GATES';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(DST));bpy.ops.wm.open_mainfile(filepath=str(DST));assert controls()==before
    bindingPath=S/'aevrynd-female-next-r0018-a-brow-bindings.json';bindingPath.write_text(json.dumps(bindings,separators=(',',':'))+'\n')
    save('saved-build-verification.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(DST),'outputSha256':sha(DST),'browBindings':str(bindingPath),'browBindingsSha256':sha(bindingPath),'originalHeadSkinEyesLashesHairRigLightMaterialsUnchanged':True,'browMaterialUnchanged':True,'sourceBrowObjectsReplacedByEditableMeshes':True,'layers':rows,'fileBytes':DST.stat().st_size,'wallSeconds':time.time()-start,'status':'REOPEN_CONTROL_PASS_COLLISION_PENDING'})
    print('R0018_BUILD_REOPEN_PASS',flush=True)

def render():
    from mathutils import Vector
    baseline='--baseline' in sys.argv;alternate='--alternate' in sys.argv;src=SRC if baseline else DST;bpy.ops.wm.open_mainfile(filepath=str(src));solid.stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],'neutral');s=bpy.context.scene;s.render.threads_mode='FIXED';s.render.threads=4;head=1.5624730926266572*.91;target=(0.,-.02,head)
    if alternate:
        for light in (o for o in bpy.data.objects if o.type=='LIGHT'):
            d=np.array(light.location)-np.array(target);light.location=Vector(np.array(target)+np.array((-d[1],d[0],d[2])));light.rotation_euler=(Vector(target)-light.location).to_track_quat('-Z','Y').to_euler()
    views=[('face',(0.,-.90,head+.015),target,(1100,1100)),('oblique',(.36,-.84,head+.02),target,(1100,1100)),('brows',(0.,-.43,1.474),(0.,-.115,1.474),(1400,650))]
    if '--pilot' in sys.argv:views=[views[0],views[2]]
    if alternate:views=[views[0],views[2]]
    rows=[];label=('baseline' if baseline else 'candidate-'+VARIANT)+('-side-light' if alternate else '')
    for view,location,target,res in views:
        c=s.camera;c.location=location;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=100;s.render.resolution_x,s.render.resolution_y=res;s.render.resolution_percentage=100;s.render.filepath=str(E/f'{label}-{view}.png');bpy.ops.render.render(write_still=True)
        rows.append({'path':s.render.filepath,'view':view,'cameraMatrix':[x for row in c.matrix_world for x in row],'lens':100,'resolution':res,'engine':s.render.engine,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma,'lights':[(o.name,list(o.location),list(o.rotation_euler),o.data.energy,o.data.size,list(o.data.color)) for o in bpy.data.objects if o.type=='LIGHT']})
    save(label+'-renders.json',{'source':str(src),'sourceSha256':sha(src),'renders':rows})
    print('R0018_RENDER_DONE '+label,flush=True)

if __name__=='__main__':
    if '--render' in sys.argv:render()
    else:build()
