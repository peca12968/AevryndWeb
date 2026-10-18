"""Fit separated owned optical eye layers to the untouched r0005 native sockets."""
import bpy, math, json, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(r'D:\Download\Aevrynd');SRC=R/'engine/assets/characters/female-next/source/aevrynd-female-next-r0005-native-source.blend'
E=R/'Evidence/character-female-next/r0006-native-eyes';E.mkdir(parents=True,exist_ok=True)
TEXTURES=SRC.parent/'textures';TEXTURES.mkdir(exist_ok=True)
VARIANTS=(('a-recessed',.92),('b-balanced',.96),('c-full',1.0))
SEG=96

def helper_centres():
    raw=bpy.data.objects['AFN_R0005_EditableNativeCC0'];K=raw.data.shape_keys.key_blocks;P=[v.co.copy() for v in K[0].data]
    for k in K[1:]:
        if not k.mute:
            for i,v in enumerate(k.data):P[i]+=k.value*(v.co-k.relative_key.data[i].co)
    result={}
    for side,name in (('L','helper-l-eye'),('R','helper-r-eye')):
        group=raw.vertex_groups[name];points=[raw.matrix_world@P[v.index] for v in raw.data.vertices if any(g.group==group.index for g in v.groups)]
        bounds=[(min(p[a] for p in points),max(p[a] for p in points)) for a in range(3)]
        result[side]={'centre':[(a+b)/2 for a,b in bounds],'radius':min((b-a)/2 for a,b in bounds),'bounds':bounds}
    return result

def iris_image():
    size=1024;axis=(np.arange(size,dtype=np.float32)+.5)/size*2-1;x,z=np.meshgrid(axis,axis);r=np.sqrt(x*x+z*z);theta=np.arctan2(z,x)
    fibre=np.zeros_like(r)
    for freq,amp,phase in ((41,.20,.3),(79,.14,1.9),(143,.09,2.2),(269,.04,.7)):
        fibre+=amp*np.sin(theta*freq+7*np.sin(r*5+phase)+r*19)
    blend=np.clip((r-.30)/.60,0,1)
    inner=np.array((.18,.072,.022),dtype=np.float32);outer=np.array((.065,.092,.055),dtype=np.float32)
    colour=inner[None,None,:]*(1-blend[...,None])+outer[None,None,:]*blend[...,None]
    colour*=np.clip(1+fibre[...,None]*.34,.55,1.45)
    ring=.42+.025*np.sin(theta*7)+.012*np.sin(theta*17)
    crypt=np.exp(-((r-ring)/.035)**2)*(.5+.5*np.sin(theta*31+r*11))
    colour*=1-.19*crypt[...,None]
    limbus=np.clip((r-.87)/.13,0,1);colour*=1-.60*limbus[...,None]
    rgba=np.concatenate((np.clip(colour,0,1),np.ones_like(r)[...,None]),axis=-1).astype(np.float32)
    image=bpy.data.images.new('AFN_R0006_OwnedIris',width=size,height=size,alpha=False);image.colorspace_settings.name='sRGB';image.pixels.foreach_set(rgba.ravel());image.filepath_raw=str(TEXTURES/'aevrynd-iris-r0006.png');image.file_format='PNG';image.save();image.pack()
    image['aevrynd_origin']='Aevrynd analytic radial fibres and irregular collarette; no external image'
    return image

def material(name,colour,rough):
    m=bpy.data.materials.new(name);m.use_nodes=True;s=next(n for n in m.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled');s.inputs['Base Color'].default_value=(*colour,1.);s.inputs['Roughness'].default_value=rough
    return m,s

def eye_materials(image):
    sclera,s=material('AFN6_Sclera',(.52,.55,.53),.30);s.inputs['Coat Weight'].default_value=.12;s.inputs['Coat Roughness'].default_value=.08
    iris,s=material('AFN6_Iris',(.12,.07,.03),.38);t=iris.node_tree.nodes.new('ShaderNodeTexImage');t.image=image;iris.node_tree.links.new(t.outputs['Color'],s.inputs['Base Color'])
    pupil,s=material('AFN6_Pupil',(.0015,.0012,.0010),.38);s.inputs['Specular IOR Level'].default_value=.15
    cornea,s=material('AFN6_Cornea',(1.,1.,1.),.025);s.inputs['Transmission Weight'].default_value=1.;s.inputs['IOR'].default_value=1.376
    if hasattr(cornea,'use_raytrace_refraction'):cornea.use_raytrace_refraction=True
    return {'Sclera':sclera,'Iris':iris,'Pupil':pupil,'Cornea':cornea}

def create_surface(side,name,rings,centre,bone,rig,mat,uv_radius=.006):
    verts=[];UV=[];indices=[]
    for radius,depth in rings:
        if radius<=1e-8:
            indices.append([len(verts)]);verts.append((centre.x,centre.y+depth,centre.z));UV.append((.5,.5));continue
        indices.append(list(range(len(verts),len(verts)+SEG)))
        for j in range(SEG):
            a=2*math.pi*j/SEG;verts.append((centre.x+radius*math.cos(a),centre.y+depth,centre.z+radius*math.sin(a)));UV.append((.5+.5*radius/uv_radius*math.cos(a),.5+.5*radius/uv_radius*math.sin(a)))
    faces=[]
    for i in range(len(rings)-1):
        for j in range(SEG):
            n=(j+1)%SEG
            if len(indices[i+1])==1:faces.append((indices[i][j],indices[i][n],indices[i+1][0]))
            else:faces.append((indices[i][j],indices[i][n],indices[i+1][n],indices[i+1][j]))
    if name=='Sclera':faces=[tuple(reversed(face)) for face in faces]
    mesh=bpy.data.meshes.new(f'AFN6_{side}_{name}');mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(mesh.name,mesh);bpy.data.collections['AFN5_EYES'].objects.link(obj);mesh.materials.append(mat)
    for p in mesh.polygons:p.use_smooth=True
    uv=mesh.uv_layers.new(name='OpticalUV')
    for p in mesh.polygons:
        for li,vi in zip(p.loop_indices,p.vertices):uv.data[li].uv=UV[vi]
    group=obj.vertex_groups.new(name=bone);group.add(list(range(len(verts))),1.,'REPLACE');obj.parent=rig;mod=obj.modifiers.new('AFN_OpticalSkinning','ARMATURE');mod.object=rig
    obj['aevrynd_layer']='EYES';obj['aevrynd_optical_component']=name;obj['aevrynd_revision']='female-next-r0006'
    return obj

def make_eye(side,fit,scale,rig,mats):
    centre=Vector(fit['centre']);rad=fit['radius']*scale;limbus=.0056*scale;pupil=.0019*scale
    edge=-math.sqrt(rad*rad-limbus*limbus);angle=math.asin(limbus/rad)
    # An open scleral shell allows the iris and pupil to sit beneath the cornea.
    scleral=[]
    for i in range(41):
        theta=angle+(math.pi-angle)*i/40
        scleral.append((0. if i==40 else rad*math.sin(theta),-rad*math.cos(theta)))
    parts=[create_surface(side,'Sclera',scleral,centre,'eye.'+side,rig,mats['Sclera'])]
    # Reverse radial order for the anterior surfaces so normals point outwards.
    iris=[]
    for i in range(17):
        radius=limbus-(limbus-pupil)*i/16;depth=edge+.00025+.00055*(1-(radius/limbus)**2)
        iris.append((radius,depth))
    parts.append(create_surface(side,'Iris',iris,centre,'eye.'+side,rig,mats['Iris'],uv_radius=limbus))
    pupil_depth=iris[-1][1]+.00018
    parts.append(create_surface(side,'Pupil',[(pupil,pupil_depth),(0.,pupil_depth+.0001)],centre,'eye.'+side,rig,mats['Pupil']))
    sag=.0020*scale;curve=(limbus*limbus+sag*sag)/(2*sag);corneal=[]
    for i in range(25):
        radius=limbus*(1-i/24);depth=edge-sag+curve-math.sqrt(max(0.,curve*curve-radius*radius))
        corneal.append((radius,depth))
    parts.append(create_surface(side,'Cornea',corneal,centre,'eye.'+side,rig,mats['Cornea']))
    return parts,{'centre':list(centre),'radiusM':rad,'limbusRadiusM':limbus,'pupilRadiusM':pupil,'cornealSagM':sag,'irisAtLimbusDepthM':edge+.00025}

def add_bones(rig,fits):
    bpy.context.view_layer.objects.active=rig;rig.hide_set(False);rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
    for side,fit in fits.items():
        b=rig.data.edit_bones.new('eye.'+side);b.head=fit['centre'];b.tail=Vector(fit['centre'])+Vector((0.,-.022,0.));b.parent=rig.data.edit_bones['head'];b.use_deform=True
    bpy.ops.object.mode_set(mode='OBJECT');rig.select_set(False)

def set_pose(rig,pose):
    for name in ('head','eye.L','eye.R'):
        rig.pose.bones[name].rotation_mode='XYZ';rig.pose.bones[name].rotation_euler=(0.,0.,0.)
    if pose=='gaze':
        for side in ('L','R'):rig.pose.bones['eye.'+side].rotation_euler[2]=math.radians(10)
    if pose=='turn':rig.pose.bones['head'].rotation_euler[1]=math.radians(20)
    bpy.context.view_layer.update()

def audit(body,parts):
    dg=bpy.context.evaluated_depsgraph_get();dg.update();ev=body.evaluated_get(dg);m=ev.to_mesh();vertices=[ev.matrix_world@v.co for v in m.vertices];m.calc_loop_triangles();triangles=[tuple(t.vertices) for t in m.loop_triangles];tree=BVHTree.FromPolygons(vertices,triangles,all_triangles=True);result={}
    for part in parts:
        pe=part.evaluated_get(dg);pm=pe.to_mesh();pv=[pe.matrix_world@v.co for v in pm.vertices];pm.calc_loop_triangles();pt=[tuple(t.vertices) for t in pm.loop_triangles];own=BVHTree.FromPolygons(pv,pt,all_triangles=True);cross=tree.overlap(own);signed=[];samples=[]
        for i,p in enumerate(pv):
            h=tree.find_nearest(p);value=(p-h[0]).dot(h[1].normalized());signed.append(value)
            if value<0 and len(samples)<6:samples.append({'vertex':i,'signedM':value,'world':list(p)})
        result[part.name]={'vertices':len(pv),'triangles':len(pt),'minimumSignedBodyClearanceM':min(signed),'negativeVertices':sum(v<0 for v in signed),'bodyTriangleIntersectionPairs':len(cross),'negativeSamples':samples};pe.to_mesh_clear()
    ev.to_mesh_clear();return result

def render(label,view,fits,pose):
    scene=bpy.context.scene;c=scene.camera;height=1.5624730926266572;head=(0.,-.02,height*.91);eyeZ=fits['L']['centre'][2]
    V={'face':((0.,-.90,head[2]+.015),head,100,(1100,1100)),'oblique':((.36,-.84,head[2]+.02),head,100,(1100,1100)),'profile':((.9,-.03,head[2]+.015),head,100,(1100,1100)),'eyes':((0.,-.43,eyeZ+.005),(0.,-.115,eyeZ),100,(1400,650))}
    c.location,t,c.data.lens,size=V[view];c.rotation_euler=(Vector(t)-c.location).to_track_quat('-Z','Y').to_euler();scene.render.resolution_x,scene.render.resolution_y=size;scene.render.resolution_percentage=100;path=E/f'{label}-{view}-{pose}.png';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);return str(path)

def main():
    variants=[]
    for label,scale in VARIANTS:
        bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene;scene.frame_set(1);body=bpy.data.objects['AFN_R0005_Body'];rig=bpy.data.objects['AFN_R0005_Rig'];fits=helper_centres();add_bones(rig,fits);image=iris_image();mats=eye_materials(image)
        scene.eevee.use_raytracing=True
        parts=[];geometry={}
        for side in ('L','R'):
            p,g=make_eye(side,fits[side],scale,rig,mats);parts+=p;geometry[side]=g
        audits={};renders=[]
        for pose in ('neutral','gaze','turn'):
            set_pose(rig,pose);audits[pose]=audit(body,parts)
            for view in (('face','oblique','profile','eyes') if pose=='neutral' else ('eyes',)):renders.append(render(label,view,fits,pose))
        set_pose(rig,'neutral');scene['aevrynd_revision']='female-next-r0006-'+label;scene['aevrynd_release_state']='OPTICAL_FIT_STUDY_NOT_PROMOTED';scene['aevrynd_website_promotion']='forbidden'
        output=SRC.parent/f'aevrynd-female-next-r0006-{label}-study.blend';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(output))
        total_neg=sum(v['negativeVertices'] for a in audits.values() for v in a.values());total_cross=sum(v['bodyTriangleIntersectionPairs'] for a in audits.values() for v in a.values())
        item={'label':label,'radiusScale':scale,'geometry':geometry,'poseAudit':audits,'renders':renders,'output':str(output),'fileBytes':output.stat().st_size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'bodyFitStatus':'PASS' if total_neg==0 and total_cross==0 else 'FAIL','negativeObservations':total_neg,'bodyCrossPairsAcrossPoses':total_cross,'renderSettings':{'engine':scene.render.engine,'eeveeRaytracing':scene.eevee.use_raytracing,'corneaTransmission':1.,'corneaIor':1.376},'remainingLimits':['No blink key or eye-lid motion is present.','No whole-character or runtime performance qualification.','Sclera/cornea share a designed limbus boundary; iris and pupil are distinct recessed surfaces.']};variants.append(item)
        (E/'female-next-r0006-native-eyes.report.json').write_text(json.dumps({'revision':'female-next-r0006','source':str(SRC),'hypothesis':'Native helper positions and a bounded globe radius can fit separate optical layers to unchanged eyelids.','variants':variants,'status':'VISUAL_REVIEW_PENDING','selectedVariant':None,'enginePromotionApproved':False,'websitePromotionApproved':False,'enginePerformance':{'status':'NOT_TESTED','cpuMs':None,'gpuMs':None,'memoryBytes':None}},indent=2)+'\n')
        print('AFN_R0006='+json.dumps({'label':label,'negativeObservations':total_neg,'bodyCrossPairs':total_cross,'fit':item['bodyFitStatus']}),flush=True)


if __name__ == "__main__":
    main()
