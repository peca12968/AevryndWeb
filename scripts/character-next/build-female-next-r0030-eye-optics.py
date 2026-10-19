"""Contour-preserving separated optics on the retained CC0 female head.

Original globe triangles are partitioned by a limbus plane, retaining the full
exterior. Iris is an actual annulus with thickness and a recessed dark backing
behind the pupil aperture. All art and optical assumptions are recorded.
"""
import bpy,importlib.util,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
spec=importlib.util.spec_from_file_location('b29',Path(__file__).with_name('build-female-next-r0029-native-eye-interface.py'));q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
b=q.b;R=b.R;S=b.S;ROOT_E=R/'Evidence/character-female-next/r0030-eye-optics';LABEL='b' if '--linear-iris' in sys.argv else 'a';E=ROOT_E/LABEL;E.mkdir(parents=True,exist_ok=True)
SRC=q.OUT;OUT=S/('aevrynd-female-next-r0030-b-linear-iris-optics.blend' if LABEL=='b' else 'aevrynd-female-next-r0030-a-layered-eye-optics.blend');SEG=128
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def read(n):return json.loads((E/n).read_text(encoding='utf8'))
def material(name,color,rough):
    m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;return m,p
def own_iris():
    n=1024;a=(np.arange(n,dtype='f4')+.5)/n*2-1;x,z=np.meshgrid(a,a);r=np.hypot(x,z);theta=np.arctan2(z,x);fib=np.zeros_like(r)
    for f,w,phase in ((37,.11,.3),(83,.10,1.7),(157,.07,2.1),(283,.025,.8)):
        fib+=w*np.sin(theta*f+5*np.sin(r*8+phase)+r*23)
    mix=np.clip((r-.28)/.62,0,1);inner=np.array((.14,.061,.019),dtype='f4');outer=np.array((.047,.032,.017),dtype='f4');col=inner[None,None,:]*(1-mix[...,None])+outer[None,None,:]*mix[...,None];col*=np.clip(1+fib[...,None],.55,1.5)
    collarette=.43+.018*np.sin(theta*9)+.009*np.sin(theta*23);crypt=np.exp(-((r-collarette)/.028)**2)*(.5+.5*np.sin(theta*47+r*10));col*=1-.23*crypt[...,None];col*=1-.60*np.clip((r-.88)/.12,0,1)[...,None]
    if LABEL=='b':col=np.where(col<=.0031308,12.92*col,1.055*np.power(np.maximum(col,0),1/2.4)-.055)
    rgba=np.concatenate((col,np.ones_like(r)[...,None]),axis=-1).astype('f4');im=bpy.data.images.new('AFN30_OwnBrownIris',width=n,height=n,alpha=False);im.colorspace_settings.name='sRGB';im.pixels.foreach_set(rgba.ravel());im.filepath_raw=str(S/('textures/aevrynd-r0030-b-own-iris.png' if LABEL=='b' else 'textures/aevrynd-r0030-own-iris.png'));Path(im.filepath_raw).parent.mkdir(exist_ok=True);im.file_format='PNG';im.save();im.pack();im['origin']='Own analytic radial fibres, irregular collarette and limbus, no imported image.';im['linear_to_srgb_encoded']=LABEL=='b';return im
def materials(im):
    sclera,p=material('AFN30_OffWhiteSclera',(.50,.53,.50),.28);p.inputs['Coat Weight'].default_value=.10;p.inputs['Coat Roughness'].default_value=.07
    attr=sclera.node_tree.nodes.new('ShaderNodeAttribute');attr.attribute_name='AFN30_ScleraColor';sclera.node_tree.links.new(attr.outputs['Color'],p.inputs['Base Color'])
    iris,p=material('AFN30_BrownIris',(.10,.05,.02),.40);tex=iris.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;iris.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);p.inputs['Specular IOR Level'].default_value=.25
    pupil,p=material('AFN30_PupilBacking',(.0008,.0006,.0004),.6);p.inputs['Specular IOR Level'].default_value=.03
    cornea,p=material('AFN30_CorneaSingleInterface',(1,1,1),.025);p.inputs['Transmission Weight'].default_value=1;p.inputs['IOR'].default_value=1.376
    if hasattr(cornea,'use_raytrace_refraction'):cornea.use_raytrace_refraction=True
    cornea.thickness_mode='SLAB';cornea.node_tree.nodes.get('Material Output').inputs['Thickness'].default_value=0
    return {'Sclera':sclera,'Cornea':cornea,'Iris':iris,'Pupil':pupil}
def make(name,v,faces,mat,center,uv_radius=None,normals=None):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(v,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);bpy.data.collections['AFN30_EYES'].objects.link(o);mesh.materials.append(mat)
    o.parent=bpy.data.objects[b.BODY];o.matrix_world=Matrix.Identity(4)
    for p in mesh.polygons:p.use_smooth=True
    if normals is not None:mesh.normals_split_custom_set_from_vertices(normals)
    if uv_radius:
        uv=mesh.uv_layers.new(name='AFN30_RadialUV')
        for p in mesh.polygons:
            for li,vi in zip(p.loop_indices,p.vertices):uv.data[li].uv=(.5+.5*(v[vi][0]-center[0])/uv_radius,.5+.5*(v[vi][2]-center[2])/uv_radius)
    o['AFN30_component']=name.split('_')[-1];o['AFN30_static_only']=True;return o
def clip_globe(v,t,normals,cut,front):
    points=[];normal=[];faces=[];lookup={};rim=[]
    def point(item):
        key,p,n=item
        if key not in lookup:lookup[key]=len(points);points.append(p.tolist());normal.append((n/np.linalg.norm(n)).tolist())
        return lookup[key]
    for tri in t:
        src=[(('v',int(i)),v[i],normals[i]) for i in tri];out=[]
        for a,c in zip(src,src[1:]+src[:1]):
            ai=(a[1][1]<=cut) if front else (a[1][1]>=cut);ci=(c[1][1]<=cut) if front else (c[1][1]>=cut)
            if ai:out.append(a)
            if ai!=ci:
                alpha=(cut-a[1][1])/(c[1][1]-a[1][1]);p=a[1]+alpha*(c[1]-a[1]);p[1]=cut;n=a[2]+alpha*(c[2]-a[2]);key=('e',*sorted((a[0][1],c[0][1])));out.append((key,p,n))
        if len(out)>=3:
            ids=[point(i) for i in out]
            for i in range(1,len(ids)-1):faces.append((ids[0],ids[i],ids[i+1]))
    for key,i in lookup.items():
        if key[0]=='e':rim.append(i)
    return points,faces,normal,rim
def annulus(center,outer,pupil,y):
    v=[];faces=[];nr=20
    # Front iris falls posteriorly toward the true pupil aperture. Thickness
    # gives distinct front/back/inner/outer surfaces, no painted pupil disc.
    for back in (False,True):
        for k in range(nr+1):
            radius=outer-(outer-pupil)*k/nr;depth=y+.00040*(1-(radius/outer)**2)+(.00018 if back else 0)
            for j in range(SEG):a=2*math.pi*j/SEG;v.append((center[0]+radius*math.cos(a),depth,center[2]+radius*math.sin(a)))
    half=(nr+1)*SEG
    for back in (False,True):
        shift=half if back else 0
        for k in range(nr):
            for j in range(SEG):
                a=shift+k*SEG+j;c=shift+k*SEG+(j+1)%SEG;d=shift+(k+1)*SEG+(j+1)%SEG;e=shift+(k+1)*SEG+j;f=(a,c,d,e);faces.append(tuple(reversed(f)) if back else f)
    for k in (0,nr):
        for j in range(SEG):
            a=k*SEG+j;c=k*SEG+(j+1)%SEG;f=(a,half+a,half+c,c);faces.append(tuple(reversed(f)) if k==nr else f)
    return v,faces
def disk(center,r,y):
    # Recessed dark backing approximates the unlit eye interior through the
    # actual iris opening; this is not a simulated retina/lens.
    v=[(center[0],y,center[2])]+[(center[0]+r*math.cos(2*math.pi*j/SEG),y,center[2]+r*math.sin(2*math.pi*j/SEG)) for j in range(SEG)];faces=[(0,j+1,(j+1)%SEG+1) for j in range(SEG)];return v,faces
def closeup(label):
    s=bpy.context.scene;c=s.camera;center=(0,-.1125,1.45949);c.location=(0,-.45,1.461);c.rotation_euler=(Vector(center)-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=100;s.render.resolution_x=1400;s.render.resolution_y=650;s.render.filepath=str(E/f'{label}-eyes.png');bpy.ops.render.render(write_still=True);b.setup(s,b.config(s));b.camera('face')
def main():
    assert b.sha(SRC)=='21c543b06ea5e92515294f48d3cb277ccaf1996b18e437dfa0fc1e86d4e8754f'
    save('round-contract.json',{'previousGoalTurn':'progress: native socket static repair accepted, no appearance gain.','source':str(SRC),'sourceSha256':b.sha(SRC),'defect':'New scan head has blank clay eyeballs, no independent optics or visible gaze.','hypothesis':'Separate contour-preserving cornea/sclera plus recessed textured iris and actual pupil aperture create readable living eyes without changing skin, globe envelope, exposure or lights.','candidateCount':1,'geometry':'Clip existing exterior by limbus plane; preserve triangle surface union and source shape. Iris has thickness and pupil is a real hole with recessed dark backing.','reject':['No visible whole-head improvement.','Eye/body intrusion or unsupported interior component crossing.','Oblique/profile optical artifacts, bad limbus join or strong color/material mismatch.'],'resourceCheckpointMinutes':45,'resources':'One Blender/four threads, body677442 evaluated vertices, eight optical meshes, iris1024 image, standard800 head images and1400x650 eye closeup.','limits':'EEVEE single refracting interface approximation, not calibrated human ocular optics. No gaze/blink/rig, wetline/lacrimal tissue, skin or hair changes.'})
    save('primary-reference-notes.json',{'references':[{'url':'https://arxiv.org/abs/1505.05916','title':'Rendering of Eyes for Eye-Shape Registration and Gaze Estimation','use':'First-party paper using controllable eye-region geometry from head scans; motivation only, no paper code/assets imported.'},{'url':'https://docs.blender.org/manual/nl/5.2/render/eevee/material_settings.html','title':'Blender5.2 Materials / Thickness','use':'Zero output thickness disables assumed interior skip distance; single-interface approximation.'},{'url':'https://www.sci.utah.edu/~lefohn/work/eye/irisSynthesis.pdf','title':'An Ocularist’s Approach to Human Iris Synthesis','use':'Search-visible cornea IOR1.376 and iris-layer modeling; full PDF access denied, not claimed fully read or copied.'}],'implementationInference':'Own analytic fibres and annular depth on fixed CC0 globe; default1.376 index and dimensions are engineering assumptions, no subject-specific biometric or physical optics calibration.','noExternalRuntimeDependency':True})
    bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;b.E=E;q.b.E=E;cfg=b.config(s);b.setup(s,cfg);body=bpy.data.objects[b.BODY];body_signature=q.signature(body);q.render('before');closeup('before')
    col=bpy.data.collections.new('AFN30_EYES');s.collection.children.link(col);refcol=bpy.data.collections.new('AFN30_HIDDEN_ORIGINAL_GLOBES');s.collection.children.link(refcol);refcol.hide_render=True;refcol.hide_viewport=True
    fits=json.loads((ROOT_E/'existing-eye-inspection.json').read_text(encoding='utf8'))['eyes'];im=own_iris();mats=materials(im);geometries={}
    for side,fit in fits.items():
        original=bpy.data.objects[fit['name']];v,t=b.evaluated(original,True);n=np.array([list(original.matrix_world.to_3x3().inverted().transposed()@normal.vector) for normal in original.data.vertex_normals]);n/=np.linalg.norm(n,axis=1)[:,None];center=np.array(fit['centerM']);cut=fit['crossSectionPlaneYM'];parts={};rimdata={}
        for component,front in (('Sclera',False),('Cornea',True)):
            vv,tt,nn,rim=clip_globe(v,t,n,cut,front);o=make(f'AFN30_{side}_{component}',vv,tt,mats[component],center,normals=nn);parts[component]=o.name;rimdata[component]={'vertexIndices':rim,'coordinatesM':[vv[i] for i in rim]}
            if component=='Sclera':
                color=o.data.color_attributes.new(name='AFN30_ScleraColor',type='FLOAT_COLOR',domain='POINT')
                for i,p in enumerate(vv):
                    medial=np.clip((center[0]-p[0])*(1 if side=='L' else -1)/.010,0,1);pink=.10*medial;color.data[i].color=(.48+pink,.51-pink*.4,.48-pink*.4,1)
        rim=np.array(rimdata['Cornea']['coordinatesM']);rr=np.linalg.norm(rim[:,[0,2]]-center[[0,2]],axis=1);outer=min(.00565,float(rr.min()+.00025));pupil=.0018;y=cut+.00045
        vv,tt=annulus(center,outer,pupil,y);o=make(f'AFN30_{side}_Iris',vv,tt,mats['Iris'],center,uv_radius=outer);parts['Iris']=o.name
        pupil_depth=y+.00040*(1-(pupil/outer)**2)+.00018+.00022;vv,tt=disk(center,pupil*1.20,pupil_depth);o=make(f'AFN30_{side}_Pupil',vv,tt,mats['Pupil'],center);parts['Pupil']=o.name
        for c in list(original.users_collection):c.objects.unlink(original)
        refcol.objects.link(original);original.hide_render=True;original.hide_set(True);original['AFN30_reference_only']=True
        geometries[side]={'originalObject':fit['name'],'originalSignature':fit['sourceSignature'],'centerM':center.tolist(),'limbusPlaneYM':cut,'limbusRadiusRangeM':[float(rr.min()),float(rr.max())],'irisOuterRadiusM':outer,'irisFrontOuterYM':y,'pupilApertureRadiusM':pupil,'pupilBackingYM':pupil_depth,'parts':parts,'designedSharedBoundary':rimdata,'exterior':'Clipped triangles partition the exact original cornea/globe exterior. New optical meshes use inherited original smooth normals; cornea/sclera share the same calculated cut-edge vertices.'}
    assert q.signature(body)==body_signature;assert b.config(s)==cfg;b.camera('face');s['AFN30_status']='CONTOUR_PRESERVING_LAYERED_OPTICS_STATIC_REVIEW';s['AFN30_optics']='EEVEE single-interface proxy, no calibrated multi-medium lens or wetline';bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save('build-verification.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'output':str(OUT),'outputSha256':b.sha(OUT),'bodyOriginalSignature':body_signature,'bodyGeometryUVTransformExact':True,'skinAndStageUnchanged':True,'geometry':geometries,'irisImage':{'name':im.name,'path':im.filepath_raw,'packed':bool(im.packed_file),'linearToSRGBEncoded':LABEL=='b','origin':'Own analytic mathematical texture, no downloaded image.'},'optics':{'corneaTransmission':1,'corneaIor':1.376,'thicknessMode':'SLAB','outputThicknessM':0,'approximation':'One refracting interface. No aqueous/lens/retinal simulation or physical calibration.'},'missing':['Wetline/lacrimal tissue','Gaze/blink and expressions','Skin/hair/rig/oral/clothing/runtime/LOD/performance']})
    q.render('after');closeup('after');print('R0030_BUILD_DONE',json.dumps({k:{'irisRadiusM':v['irisOuterRadiusM'],'limbusRadiusRangeM':v['limbusRadiusRangeM']} for k,v in geometries.items()}),flush=True)
if __name__=='__main__':main()
