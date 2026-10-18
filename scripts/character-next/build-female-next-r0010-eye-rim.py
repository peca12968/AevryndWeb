"""Skin-bound tapered lashes and a wet eyelid surface region, not floating tubes."""
import bpy, math, json, hashlib, random, importlib.util, sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
R=Path(r'D:\Download\Aevrynd'); E=R/'Evidence/character-female-next/r0010-eye-rim'; E.mkdir(parents=True,exist_ok=True)
SRC=R/'engine/assets/characters/female-next/source/aevrynd-female-next-r0009-a-slab-thickness-study.blend'
spec=importlib.util.spec_from_file_location('eyes',Path(__file__).with_name('build-female-next-r0006-native-eyes.py'))
stage=importlib.util.module_from_spec(spec); spec.loader.exec_module(stage); stage.E=E

def front(tree,x,z):
    return tree.ray_cast(Vector((x,-.3,z)),Vector((0.,1.,0.)),.4)

def trace_rims(tree):
    result={}
    for side,sign in [('L',1),('R',-1)]:
        points={'upper':[],'lower':[]}
        for ix in range(221):
            x=sign*(.0175+ix*.0001)
            samples=[]
            for iz in range(101):
                z=1.453+iz*.00013; p,n,face,d=front(tree,x,z)
                if p and p.y>-.115:samples.append(z)
            if not samples or len(samples)<4:continue
            for part,gap,skin in [('lower',min(samples),min(samples)-.00026),('upper',max(samples),max(samples)+.00026)]:
                p=front(tree,x,skin)[0]
                if not p or p.y>-.115:continue
                for _ in range(17):
                    mid=(gap+skin)/2; hit=front(tree,x,mid)[0]
                    if hit and hit.y<-.115:skin=mid
                    else:gap=mid
                # Remain on the anterior skin side, not the rear socket wall.
                z=skin+(.00012 if part=='upper' else -.00012)
                p,n,face,d=front(tree,x,z)
                if p is not None and p.y<-.115:points[part].append({'point':list(p),'normal':list(n),'triangle':face,'x':abs(x)})
        assert all(len(v)>150 for v in points.values()), {k:len(v) for k,v in points.items()}
        result[side]=points
    return result

def wetline(body,rims):
    pts=[Vector(v['point']) for side in rims.values() for row in side.values() for v in row]
    kd=KDTree(len(pts))
    for i,p in enumerate(pts):kd.insert(p,i)
    kd.balance(); mesh=body.data; attr=mesh.attributes.new('AFN10_WetlineMask','FLOAT','POINT'); weights=[]
    for v in mesh.vertices:
        d=kd.find(body.matrix_world@v.co)[2]; t=max(0.,1.-d/.00065); weights.append(t*t*(3-2*t))
    attr.data.foreach_set('value',weights)
    group=body.vertex_groups.new(name='AFN10_EyelidWetlineRegion')
    for v,w in zip(mesh.vertices,weights):
        if w>.001:group.add([v.index],w,'REPLACE')
    # This is a semantic surface group, never a deform bone.
    m=body.data.materials[0].copy(); m.name='AFN10_SkinWithWetRim'; body.data.materials[0]=m
    nt=m.node_tree; out=next(n for n in nt.nodes if n.bl_idname=='ShaderNodeOutputMaterial'); old=out.inputs['Surface'].links[0].from_socket
    wet=nt.nodes.new('ShaderNodeBsdfPrincipled'); wet.name='AFN10_WetMucosalSurface'; wet.inputs['Base Color'].default_value=(.43,.22,.18,1.)
    wet.inputs['Roughness'].default_value=.23; wet.inputs['Coat Weight'].default_value=.28; wet.inputs['Coat Roughness'].default_value=.10
    a=nt.nodes.new('ShaderNodeAttribute'); a.attribute_name='AFN10_WetlineMask'; a.name='AFN10_AnatomicalRimMask'
    mix=nt.nodes.new('ShaderNodeMixShader'); nt.links.new(a.outputs['Fac'],mix.inputs[0]); nt.links.new(old,mix.inputs[1]); nt.links.new(wet.outputs['BSDF'],mix.inputs[2]); nt.links.new(mix.outputs[0],out.inputs['Surface'])
    return {'affectedVertices':sum(w>.001 for w in weights),'supportRadiusM':.00065,'method':'Smooth point-domain material mask on original skin; no duplicate/floating surface or new rim volume.','semanticGroup':'AFN10_EyelidWetlineRegion'}

def barycentric(p,a,b,c):
    u=b-a; v=c-a; w=p-a; uu=u.dot(u); uv=u.dot(v); vv=v.dot(v); wu=w.dot(u); wv=w.dot(v); den=uu*vv-uv*uv
    t=(vv*wu-uv*wv)/den; q=(uu*wv-uv*wu)/den
    return (1-t-q,t,q)

def lashes(body,rig,tree,rims,organic=False,label='a-rim-lashes'):
    collection=bpy.data.collections.new('AFN10_LASHES'); bpy.context.scene.collection.children.link(collection)
    mat=bpy.data.materials.new('AFN10_LashKeratin'); mat.use_nodes=True
    bs=next(n for n in mat.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled'); bs.inputs['Base Color'].default_value=(.018,.009,.005,1.); bs.inputs['Roughness'].default_value=.48
    rng=random.Random(1010); objects=[]; bindings=[]
    for side,sign in [('L',1),('R',-1)]:
        for part,count in [('upper',72),('lower',38)]:
            rim=rims[side][part]; verts=[]; faces=[]; hair_weights=[]; span=(rim[0]['x'],rim[-1]['x'])
            clusters=[(.08+.87*(i+.15+rng.random()*.7)/24,rng.uniform(.75,1.14),rng.uniform(-.16,.16)) for i in range(24)] if organic else None
            for index in range(count):
                t=.08+.87*(index+.25+rng.random()*.5)/count
                if organic:
                    ct,cl,tilt=clusters[min(23,index*24//count)]; t=max(.08,min(.95,ct+rng.uniform(-.010,.010)))
                x=span[0]+t*(span[1]-span[0]); sample=min(rim,key=lambda v:abs(v['x']-x))
                # Outer skin side of the rim, away from the exposed globe.
                z=sample['point'][2]+(.00030 if part=='upper' else -.00030); hit,n,ti,d=front(tree,sign*x,z)
                assert hit and hit.y<-.115
                tri=body.data.loop_triangles[ti]; ids=list(tri.vertices); a,b,c=[body.matrix_world@body.data.vertices[i].co for i in ids]; bc=barycentric(hit,a,b,c)
                groups={}
                for vi,w in zip(ids,bc):
                    for g in body.data.vertices[vi].groups:
                        name=body.vertex_groups[g.group].name
                        if name in rig.data.bones:groups[name]=groups.get(name,0.)+w*g.weight
                total=sum(groups.values()); groups={k:v/total for k,v in groups.items() if v>1e-8}
                length=(.0023+.0033*math.sin(math.pi*t)**.8)*rng.uniform(.84,1.10)
                if part=='lower':length*=.52
                if organic:
                    length*=cl*rng.uniform(.80,1.06)
                    if part=='lower':length*=rng.uniform(.65,.95)
                radius=rng.uniform(.000024,.000036); root=hit+n*(radius+.000025); start=len(verts); ring_count=11; radial=6
                points=[]
                for j in range(ring_count):
                    u=j/(ring_count-1); fan=sign*(t-.36)*.40
                    direction=Vector((fan,-.9,(.15+.90*u) if part=='upper' else (-.1-.60*u))).normalized()
                    p=root+direction*(length*u)
                    if organic:
                        lateral=sign*((t-.36)*1.18+tilt)
                        converge=sign*(ct-t)*(span[1]-span[0])*.72*u*u
                        curl=(.14*u+(.52+tilt)*u*u)*(1 if part=='upper' else -.65)
                        p=root+Vector((lateral*length*u+converge,-length*(.88*u-.18*u*u),length*curl))
                    points.append(p)
                for j,p in enumerate(points):
                    tangent=(points[min(j+1,ring_count-1)]-points[max(0,j-1)]).normalized(); axis=tangent.cross(Vector((1,0,0))).normalized(); second=tangent.cross(axis).normalized(); r=radius*(1-j/(ring_count-1))**.75+.000001
                    for k in range(radial):
                        angle=k*math.tau/radial; verts.append(p+r*(math.cos(angle)*axis+math.sin(angle)*second));hair_weights.append(groups)
                for j in range(ring_count-1):
                    for k in range(radial):
                        q=(k+1)%radial; faces.append((start+j*radial+k,start+j*radial+q,start+(j+1)*radial+q,start+(j+1)*radial+k))
                faces.append(tuple(start+k for k in reversed(range(radial)))); faces.append(tuple(start+(ring_count-1)*radial+k for k in range(radial)))
                bindings.append({'object':f'AFN10_{side}_{part}_Lashes','hair':index,'firstVertex':start,'vertices':ring_count*radial,'bodyTriangle':ti,'bodyVertices':ids,'barycentric':bc,'root':list(root),'lengthM':length,'radiusM':radius,'rootSurfaceGapM':radius+.000025,'boneWeights':groups})
            mesh=bpy.data.meshes.new(f'AFN10_{side}_{part}_Lashes'); mesh.from_pydata(verts,[],faces); mesh.update(); mesh.materials.append(mat)
            obj=bpy.data.objects.new(mesh.name,mesh); collection.objects.link(obj); obj.parent=rig; obj['aevrynd_layer']='EYELASHES'; obj['aevrynd_root_binding']='r0010 lash-bindings.json; skin triangle barycentric coordinates'; obj['aevrynd_revision']='female-next-r0010'
            names=sorted({k for g in hair_weights for k in g}); vgroups={k:obj.vertex_groups.new(name=k) for k in names}
            for i,groups in enumerate(hair_weights):
                for name,w in groups.items():vgroups[name].add([i],w,'REPLACE')
            mod=obj.modifiers.new('AFN10_SkinBinding','ARMATURE'); mod.object=rig
            for p in mesh.polygons:p.use_smooth=True
            objects.append(obj)
    (E/(label+'-lash-bindings.json')).write_text(json.dumps(bindings,indent=2)+'\n')
    return objects,bindings

def main(organic=False):
    label='b-organic-lashes' if organic else 'a-rim-lashes'
    bpy.ops.wm.open_mainfile(filepath=str(SRC)); rig=bpy.data.objects['AFN_R0005_Rig']; stage.set_pose(rig,'neutral'); body=bpy.data.objects['AFN_R0008_Body']; m=body.data; m.calc_loop_triangles()
    tree=BVHTree.FromPolygons([body.matrix_world@v.co for v in m.vertices],[tuple(t.vertices) for t in m.loop_triangles],all_triangles=True)
    rims=trace_rims(tree); (E/(label+'-traced-rims.json')).write_text(json.dumps(rims,indent=2)+'\n'); region=wetline(body,rims); parts,bindings=lashes(body,rig,tree,rims,organic,label)
    fits=stage.helper_centres(); images=[stage.render(label,v,fits,'neutral') for v in ('eyes','face','oblique')]
    scene=bpy.context.scene; scene['aevrynd_revision']='female-next-r0010-'+label; scene['aevrynd_release_state']='EYE_RIM_STUDY_PENDING_COLLISION_AND_VISUAL_REVIEW'
    dest=SRC.parent/('aevrynd-female-next-r0010-'+label+'-study.blend'); bpy.context.preferences.filepaths.save_version=0; bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    (E/('female-next-r0010-'+label+'.report.json')).write_text(json.dumps({'revision':'female-next-r0010','variant':label,'organicClumps':organic,'source':str(SRC),'sourceSha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'output':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'hypothesis':'Skin-bound tapered lashes and a narrow wet mucosal region reduce the bare plastic-eye appearance without changing skin or globe geometry.','wetline':region,'lashes':{'objects':[o.name for o in parts],'hairs':len(bindings),'vertices':sum(len(o.data.vertices) for o in parts),'triangles':sum(sum(len(f.vertices)-2 for f in o.data.polygons) for o in parts)},'renders':images,'status':'PENDING_TECHNICAL_VISUAL_REVIEW','remainingLimits':['Caruncle volume not sculpted; do not count rim colour as a caruncle.','No blink or facial keys; lash binding must be regenerated or deformed with the skin when added.','Brow fibres, skin maps and head hair still absent.','Runtime and continuous animation collisions not tested.'],'enginePromotionApproved':False,'websitePromotionApproved':False,'overallCharacterScore':None},indent=2)+'\n')
    print('AFN_R0010_BUILT='+str(dest))

if __name__=='__main__':main('--organic' in sys.argv)
