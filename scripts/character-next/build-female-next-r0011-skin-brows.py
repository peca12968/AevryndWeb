"""Mapped CC0 pigment, explicit skin calibration, and separately bound brow fibres."""
import bpy,json,math,random,hashlib,importlib.util,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0011-skin-brows';S=R/'engine/assets/characters/female-next/source'
SRC=S/'aevrynd-female-next-r0010-c-spaced-lashes-study.blend'
spec=importlib.util.spec_from_file_location('rim_tools',Path(__file__).with_name('build-female-next-r0010-eye-rim.py'));rim=importlib.util.module_from_spec(spec);spec.loader.exec_module(rim);rim.stage.E=E

def skin(body):
    calibration=json.loads((E/'skin-albedo-calibration.json').read_text());image=bpy.data.images.load(calibration['source'],check_existing=True);image.colorspace_settings.name='sRGB';image.pack()
    mat=body.data.materials[0].copy();mat.name='AFN11_CalibratedMappedSkin';body.data.materials[0]=mat;nt=mat.node_tree
    shader=next(n for n in nt.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled' and n.name!='AFN10_WetMucosalSurface')
    uv=nt.nodes.new('ShaderNodeUVMap');uv.uv_map='UVMap';uv.name='AFN11_NativeUV'
    tex=nt.nodes.new('ShaderNodeTexImage');tex.image=image;tex.name='AFN11_CC0MappedPigment';tex.interpolation='Linear';nt.links.new(uv.outputs['UV'],tex.inputs['Vector'])
    gain=nt.nodes.new('ShaderNodeMixRGB');gain.blend_type='MULTIPLY';gain.inputs[0].default_value=1.;gain.inputs[2].default_value=(*calibration['perChannelReflectanceGain'],1.);gain.name='AFN11_ReferenceAlbedoCalibration';nt.links.new(tex.outputs['Color'],gain.inputs[1]);nt.links.new(gain.outputs[0],shader.inputs['Base Color'])
    attr=body.data.attributes.new('AFN11_RegionalRoughness','FLOAT','POINT');values=[]
    for v in body.data.vertices:
        x,y,z=v.co;value=.54
        if y<-.065 and 1.36<z<1.54:
            nose=math.exp(-((x/.012)**2+((z-1.432)/.017)**2));forehead=math.exp(-((x/.045)**2+((z-1.505)/.016)**2));lips=math.exp(-((x/.019)**2+((z-1.412)/.005)**2))
            value-=.12*nose+.045*forehead+.10*lips
        values.append(value)
    attr.data.foreach_set('value',values);a=nt.nodes.new('ShaderNodeAttribute');a.attribute_name=attr.name;nt.links.new(a.outputs['Fac'],shader.inputs['Roughness'])
    coords=nt.nodes.new('ShaderNodeTexCoord');noise=nt.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=3500.;noise.inputs['Detail'].default_value=2.;noise.name='AFN11_AuthoringMicroRelief'
    bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.14;bump.inputs['Distance'].default_value=.000012;bump.name='AFN11_MicronBumpOnly';nt.links.new(coords.outputs['Object'],noise.inputs['Vector']);nt.links.new(noise.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],shader.inputs['Normal'])
    shader.inputs['IOR'].default_value=1.4;shader.inputs['Specular IOR Level'].default_value=.30;shader.inputs['Subsurface Weight'].default_value=.09;shader.inputs['Subsurface Scale'].default_value=.0012;shader.inputs['Subsurface Radius'].default_value=(1.,.48,.25)
    mat['aevrynd_origin']='CC0 MakeHuman graphical pigment + Aevrynd calibration/roughness/microrelief. No imported tool code.'
    return {'material':mat.name,'calibration':calibration,'image':image.name,'skinRoughnessRange':[min(values),max(values)],'subsurfaceScaleM':.0012,'microRelief':'Procedural authoring-only bump, 12um distance x 0.14 strength; no geometry displacement. Needs baking for engine export.','wetRimPreserved':True}

def build_brows(body,rig,ridge=False):
    m=body.data;m.calc_loop_triangles();V=[body.matrix_world@v.co for v in m.vertices];T=[tuple(t.vertices) for t in m.loop_triangles];tree=BVHTree.FromPolygons(V,T,all_triangles=True)
    collection=bpy.data.collections.new('AFN11_BROWS');bpy.context.scene.collection.children.link(collection)
    material=bpy.data.materials.new('AFN11_BrowKeratin');material.use_nodes=True;bs=next(n for n in material.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled');bs.inputs['Roughness'].default_value=.52;bs.inputs['Specular IOR Level'].default_value=.25
    a=material.node_tree.nodes.new('ShaderNodeAttribute');a.attribute_name='AFN11_BrowPigment';ramp=material.node_tree.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.014,.007,.003,1);ramp.color_ramp.elements[1].color=(.047,.025,.010,1);material.node_tree.links.new(a.outputs['Fac'],ramp.inputs[0]);material.node_tree.links.new(ramp.outputs['Color'],bs.inputs['Base Color'])
    rng=random.Random(1111);records=[];summary=[]
    for side,sign in [('L',1),('R',-1)]:
        verts=[];faces=[];weights=[];pigments=[];accepted=None;rejections=0
        for hair in range(320 if ridge else 190):
            chosen=None
            for attempt in range(12):
                t=rng.uniform(.025,.97);x=sign*(.014+.038*t);centre=1.478+.0065*math.sin(math.pi*(.10+.80*t))-.0018*t
                width=.0010+.0017*math.sin(math.pi*t)**.6;band=rng.uniform(-1.,1.);z=centre+band*width
                if ridge:
                    centre=1.4745+.0038*math.sin(math.pi*(.10+.80*t))-.0010*t
                    width=.0008+.0013*math.sin(math.pi*t)**.6;z=centre+band*width
                length=rng.uniform(.0030,.0058)*(1-.28*t);up=(.95*(1-t)**2+.12) if band<.25 else (-.12+.55*(1-t)**2)
                lateral=sign*(.15+.85*t);dx=length*lateral;dz=length*up;radius=rng.uniform(.000025,.000041);lift=rng.uniform(.00007,.00023)
                if ridge:radius*=1.20;lift*=1.20
                centres=[];normals=[];valid=True
                for j in range(8):
                    u=j/7;xx=x+dx*u;zz=z+dz*u*(1-.22*u);hit,n,ti,d=rim.front(tree,xx,zz)
                    if hit is None or hit.y>-.07:valid=False;break
                    centres.append(hit+n*(radius+.000035+lift*math.sin(math.pi*u)));normals.append(n)
                if not valid:continue
                P=[];F=[];radial=5
                for j,p in enumerate(centres):
                    tangent=(centres[min(j+1,7)]-centres[max(0,j-1)]).normalized();axis=tangent.cross(normals[j]).normalized();second=tangent.cross(axis).normalized();r=radius*(1-j/7)**.75+.000001
                    for k in range(radial):a=math.tau*k/radial;P.append(p+r*(math.cos(a)*axis+math.sin(a)*second))
                for j in range(7):
                    for k in range(radial):q=(k+1)%radial;F.append((j*radial+k,j*radial+q,(j+1)*radial+q,(j+1)*radial+k))
                F.append(tuple(reversed(range(radial))));F.append(tuple(35+k for k in range(radial)))
                trial=BVHTree.FromPolygons(P,F,epsilon=.000002)
                if tree.overlap(trial) or (accepted and accepted.overlap(trial)):rejections+=1;continue
                chosen=(P,F,centres[0],radius,length);break
            if chosen is None:continue
            P,F,root,radius,length=chosen;hit,n,ti,d=tree.find_nearest(root);ids=list(T[ti]);bc=rim.barycentric(hit,*[V[i] for i in ids]);groups={}
            for vi,w in zip(ids,bc):
                for g in m.vertices[vi].groups:
                    name=body.vertex_groups[g.group].name
                    if name in rig.data.bones:groups[name]=groups.get(name,0)+w*g.weight
            total=sum(groups.values());groups={k:v/total for k,v in groups.items() if v>1e-8};offset=len(verts);verts+=P;faces+=[tuple(offset+i for i in f) for f in F];weights += [groups]*len(P);pigments += [rng.random()]*len(P)
            records.append({'object':f'AFN11_{side}_BrowFibres','hair':offset//40,'firstVertex':offset,'vertices':40,'bodyTriangle':ti,'bodyVertices':ids,'barycentric':bc,'root':list(root),'rootGapM':d,'radiusM':radius,'lengthM':length,'boneWeights':groups})
            accepted=BVHTree.FromPolygons(verts,faces,epsilon=.000002)
        assert len(verts)//40>=165,(side,len(verts)//40)
        mesh=bpy.data.meshes.new(f'AFN11_{side}_BrowFibres');mesh.from_pydata(verts,[],faces);mesh.update();mesh.materials.append(material);attr=mesh.attributes.new('AFN11_BrowPigment','FLOAT','POINT');attr.data.foreach_set('value',pigments)
        obj=bpy.data.objects.new(mesh.name,mesh);collection.objects.link(obj);obj.parent=rig;obj['aevrynd_layer']='EYEBROWS';obj['aevrynd_root_binding']='brow-bindings.json';obj['aevrynd_revision']='female-next-r0011'
        vg={n:obj.vertex_groups.new(name=n) for n in sorted({n for w in weights for n in w})}
        for i,w in enumerate(weights):
            for n,value in w.items():vg[n].add([i],value,'REPLACE')
        mod=obj.modifiers.new('AFN11_SkinBinding','ARMATURE');mod.object=rig
        for p in mesh.polygons:p.use_smooth=True
        summary.append({'object':obj.name,'hairs':len(verts)//40,'vertices':len(verts),'triangles':sum(len(p.vertices)-2 for p in mesh.polygons),'rejectedPlacementTrials':rejections})
        print('AFN_R0011_BROW='+json.dumps(summary[-1]),flush=True)
    (E/(('b-ridge' if ridge else 'a')+'-brow-bindings.json')).write_text(json.dumps(records,indent=2)+'\n');return summary

def main(ridge=False):
    label='b-ridge-skin-brows' if ridge else 'a-skin-brows'
    bpy.ops.wm.open_mainfile(filepath=str(SRC));body=bpy.data.objects['AFN_R0008_Body'];rig=bpy.data.objects['AFN_R0005_Rig'];rim.stage.set_pose(rig,'neutral');fits=rim.stage.helper_centres();skin_info=skin(body)
    isolation=[str(E/f'skin-only-{v}-neutral.png') for v in ('face','eyes')]
    if not ridge:isolation=[rim.stage.render('skin-only',v,fits,'neutral') for v in ('face','eyes')]
    brows=build_brows(body,rig,ridge);images=[rim.stage.render(label,v,fits,'neutral') for v in ('face','eyes','oblique','profile')]
    for b in brows:bpy.data.objects[b['object']]['aevrynd_root_binding']=('b-ridge' if ridge else 'a')+'-brow-bindings.json'
    scene=bpy.context.scene;scene['aevrynd_revision']='female-next-r0011-'+label;scene['aevrynd_release_state']='SKIN_BROW_STUDY_PENDING_REVIEW'
    dest=S/('aevrynd-female-next-r0011-'+label+'-study.blend');bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    (E/('female-next-r0011-'+label+'.report.json')).write_text(json.dumps({'revision':'female-next-r0011','variant':label,'source':str(SRC),'sourceSha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'output':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'hypothesis':'Mapped anatomical pigmentation and skin-following brow fibres reduce the unfinished clay-mask appearance while preserving average reference albedo and fixed scene lighting.','skin':skin_info,'brows':brows,'skinIsolationRenders':isolation,'renders':images,'status':'PENDING_TECHNICAL_VISUAL_REVIEW','enginePromotionApproved':False,'websitePromotionApproved':False,'overallCharacterScore':None,'enginePerformance':'NOT_TESTED','remainingLimits':['No scalp hair model. Source texture contains baked scalp pigment.','Procedural micro-bump is not measured pore geometry and needs engine baking.','No blink/facial expressions, caruncle sculpt or tear-meniscus volume.','Source is high resolution, with no qualified runtime LOD.']},indent=2)+'\n');print('AFN_R0011_BUILD_DONE')

if __name__=='__main__':main('--ridge' in sys.argv)
