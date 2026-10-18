"""Replace the complete old mouth bag with a welded, deformable quad annulus.

The cut follows an existing 74-edge outer loop in the *mixed* neutral shape.
Every candidate is saved for reproducibility, regardless of gate outcome.
"""
from pathlib import Path
from collections import defaultdict, Counter
import json, math, hashlib, time
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import closest_point_on_tri

ROOT=Path(r'D:\Download\Aevrynd')
SRC=ROOT/'engine/assets/characters/female-next/source/aevrynd-female-next-r0001-baseline.blend'
OUT=ROOT/'Evidence/character-female-next/r0003-perioral-retopology'
SOURCES=SRC.parent
BODY='AevryndFemaleCC0PalpebralClosure_R1097'
HAIR='AevryndFemaleGradedHairlineGroom_R1081'
OPEN='Aevrynd_MouthOpenTest_R1030'
SMILE='Aevrynd_SmileTest_R1030'
VARIANTS=(('a-contact',.0003),('b-relaxed',.0007),('c-parted',.0012))
FRAMES=(1,20,33,61)
Z=1.387

def mixed(obj):
    keys=obj.data.shape_keys.key_blocks
    p=[v.co.copy() for v in keys[0].data]
    for key in keys[1:]:
        if key.mute: continue
        for i,v in enumerate(key.data): p[i]+=key.value*(v.co-key.relative_key.data[i].co)
    return p

def bary(p,a,b,c):
    v0=b-a; v1=c-a; v2=p-a
    aa=v0.dot(v0); ab=v0.dot(v1); bb=v1.dot(v1)
    den=aa*bb-ab*ab
    if abs(den)<1e-20:return (1.,0.,0.)
    v=(bb*v2.dot(v0)-ab*v2.dot(v1))/den
    w=(aa*v2.dot(v1)-ab*v2.dot(v0))/den
    result=[max(0.,min(1.,q)) for q in (1-v-w,v,w)]
    total=sum(result)
    return tuple(q/total for q in result)

def patch_boundary(obj, coords):
    mesh=obj.data; edgefaces=defaultdict(list); selected=set()
    for f in mesh.polygons:
        ids=list(f.vertices)
        for a,b in zip(ids,ids[1:]+ids[:1]):edgefaces[tuple(sorted((a,b)))].append(f.index)
        c=sum((coords[i] for i in ids),Vector())/len(ids)
        if c.y<-.105 and (c.x/.05)**2+((c.z-Z)/.03)**2<1: selected.add(f.index)
    adj=defaultdict(list)
    for (a,b),faces in edgefaces.items():
        if sum(i in selected for i in faces)==1:adj[a].append(b);adj[b].append(a)
    comps=[];todo=set(adj)
    while todo:
        stack=[next(iter(todo))];comp=set()
        while stack:
            i=stack.pop()
            if i in comp:continue
            comp.add(i);stack.extend(adj[i])
        todo-=comp;comps.append(comp)
    outer=max(comps,key=lambda c:max(abs(coords[i].x) for i in c))
    if not all(len(adj[i])==2 for i in outer):raise RuntimeError('Non-regular outer boundary')
    cut={e for e,F in edgefaces.items() if set(e)<=outer and sum(i in selected for i in F)==1}
    start=min(outer,key=lambda i:abs(coords[i].x-.05)+abs(coords[i].z-Z))
    order=[start];previous=None;current=start
    while True:
        nxt=next(i for i in adj[current] if i!=previous)
        if nxt==start:break
        order.append(nxt);previous,current=current,nxt
        if len(order)>len(outer):raise RuntimeError('Open boundary walk')
    if sum(coords[i].z for i in order[1:len(order)//2])<sum(coords[i].z for i in order[len(order)//2:]):
        order=[order[0]]+list(reversed(order[1:]))
    seed=next(i for i in selected if any(v in outer for v in mesh.polygons[i].vertices))
    removed=set();stack=[seed]
    while stack:
        f=stack.pop()
        if f in removed:continue
        removed.add(f);ids=list(mesh.polygons[f].vertices)
        for a,b in zip(ids,ids[1:]+ids[:1]):
            edge=tuple(sorted((a,b)))
            if edge not in cut:stack.extend(edgefaces[edge])
    if not 1000<len(removed)<2200:raise RuntimeError('Unsafe removal extent '+str(len(removed)))
    return order,removed

def construct(obj,gap):
    mesh=obj.data;coords=mixed(obj);keys=mesh.shape_keys.key_blocks
    order,removed=patch_boundary(obj,coords)
    retained=[f for f in mesh.polygons if f.index not in removed]
    used=sorted({i for f in retained for i in f.vertices});mapping={old:i for i,old in enumerate(used)}
    points=[coords[i].copy() for i in used]
    samples=[((i,),(1.,)) for i in used]
    source_faces=[f for f in mesh.polygons if f.index in removed]
    tris=[];triuv=[];uv=mesh.uv_layers.active
    for f in source_faces:
        ids=list(f.vertices);loops=list(f.loop_indices)
        for j in range(1,len(ids)-1):
            tris.append((ids[0],ids[j],ids[j+1]));triuv.append([uv.data[loops[q]].uv.copy() for q in (0,j,j+1)])
    tree=BVHTree.FromPolygons(coords,tris,all_triangles=True)
    newuv={};ringmeta={};rings=[[mapping[i] for i in order]]
    angle=[math.atan2((coords[i].z-Z)/.03,coords[i].x/.05) for i in order]
    descriptors=[('skin25',.25),('skin55',.55),('skin80',.8),('vermilion',1.),('roll',None),('margin',None),('inner',None),('vestibule',None),('cavity',None),('rear',None)]
    for name,blend in descriptors:
        ring=[]
        for k,t in enumerate(angle):
            c=math.cos(t);s=math.sin(t);ss=math.copysign(abs(s)**.8,s)
            cupid=.0008*math.exp(-((abs(c)-.32)/.19)**2)-.00035*math.exp(-(c/.13)**2)
            outer=Vector((.035*c,-.1395-.0033*abs(s),Z+(.0078 if s>=0 else .0088)*ss+(cupid if s>0 else 0.)))
            margin=Vector((.031*c,-.1400-.0034*abs(s),Z+gap*.5*ss+(.0005*math.exp(-((abs(c)-.32)/.2)**2) if s>0 else -.00015*abs(s))))
            if blend is not None:p=coords[order[k]].lerp(outer,blend)
            elif name=='roll':p=outer.lerp(margin,.48);p.y-=.0013*abs(s)
            elif name=='margin':p=margin
            elif name=='inner':p=margin+Vector((0.,.0024,0.))
            elif name=='vestibule':p=Vector((.030*c,-.132,Z+.0030*ss))
            elif name=='cavity':p=Vector((.027*c,-.120,Z+.0085*ss))
            else:p=Vector((.022*c,-.108,Z+.009*ss))
            hit=tree.find_nearest(p);tri=tris[hit[2]];w=bary(hit[0],*(coords[i] for i in tri))
            idx=len(points);points.append(p);samples.append((tri,w));ring.append(idx)
            newuv[idx]=sum((u*v for u,v in zip(triuv[hit[2]],w)),Vector((0.,0.)))
            ringmeta[idx]=(t, min(1.,blend) if blend is not None else 1.,name)
        rings.append(ring)
    faces=[[mapping[i] for i in f.vertices] for f in retained]
    faceuv=[[uv.data[j].uv.copy() for j in f.loop_indices] for f in retained]
    face_materials=[f.material_index for f in retained]
    for ri in range(len(rings)-1):
        a,b=rings[ri],rings[ri+1]
        for j in range(len(order)):
            n=(j+1)%len(order);face=(a[j],a[n],b[n],b[j]);faces.append(face)
            faceuv.append([newuv.get(i,Vector((0.,0.))) for i in face]);face_materials.append(0 if ri<7 else len(mesh.materials))
    faces.append(list(reversed(rings[-1])));faceuv.append([newuv[i] for i in faces[-1]]);face_materials.append(len(mesh.materials))
    # Fill the first boundary UV corners from their original incident face.
    old_uv={}
    for f in retained:
        for i,li in zip(f.vertices,f.loop_indices):old_uv.setdefault(mapping[i],uv.data[li].uv.copy())
    for fi in range(len(retained),len(faces)):
        for j,i in enumerate(faces[fi]):
            if i in old_uv:faceuv[fi][j]=old_uv[i]
    newmesh=bpy.data.meshes.new('AFN_R0003_WeldedPerioral')
    newmesh.from_pydata(points,[],faces);newmesh.update()
    for m in mesh.materials:newmesh.materials.append(m)
    oral=bpy.data.materials.new('AFN_R0003_OralTissue');oral.use_nodes=True
    shader=next(n for n in oral.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled');shader.inputs['Base Color'].default_value=(.07,.008,.009,1.);shader.inputs['Roughness'].default_value=.42
    newmesh.materials.append(oral)
    for p,mi in zip(newmesh.polygons,face_materials):p.material_index=mi;p.use_smooth=True
    newlayer=newmesh.uv_layers.new(name=uv.name)
    for p,U in zip(newmesh.polygons,faceuv):
        for li,value in zip(p.loop_indices,U):newlayer.data[li].uv=value
    for attr in mesh.attributes:
        if attr.domain!='POINT' or attr.name.startswith('.') or attr.name=='position':continue
        if attr.data_type not in ('FLOAT','FLOAT_COLOR'):continue
        dest=newmesh.attributes.new(attr.name,attr.data_type,'POINT')
        for i,(ids,weights) in enumerate(samples):
            if attr.data_type=='FLOAT':dest.data[i].value=sum(attr.data[j].value*w for j,w in zip(ids,weights))
            else:dest.data[i].color=tuple(sum(attr.data[j].color[a]*w for j,w in zip(ids,weights)) for a in range(4))
    # Recalculate winding before creating shape keys. BMesh's key correction
    # would otherwise apply the mixed-versus-Basis offset a second time.
    bm=bmesh.new();bm.from_mesh(newmesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(newmesh);bm.free();newmesh.update()
    group_names=[g.name for g in obj.vertex_groups]
    newobj=obj.copy();newobj.data=newmesh;newobj.name='AevryndFemaleNextPerioral_R0003'
    bpy.data.collections['AFN_BODY'].objects.link(newobj)
    # Blender clears group definitions when the copied object receives a new mesh.
    newobj.vertex_groups.clear()
    for name in group_names:newobj.vertex_groups.new(name=name)
    for i,(ids,weights) in enumerate(samples):
        assignments=defaultdict(float)
        for old,w in zip(ids,weights):
            for g in mesh.vertices[old].groups:assignments[g.group]+=g.weight*w
        for group,value in assignments.items():
            if value>1e-8:newobj.vertex_groups[group].add([i],value,'REPLACE')
    # Transfer every key as a delta. Solve new Basis so current identity matches the authored neutral.
    deltas={key.name:[] for key in keys[1:]}
    bases=[]
    for i,(ids,weights) in enumerate(samples):
        active=Vector()
        for key in keys[1:]:
            delta=sum(((key.data[j].co-keys[0].data[j].co)*w for j,w in zip(ids,weights)),Vector())
            if i in ringmeta and key.name in (OPEN,SMILE):
                t,blend,name=ringmeta[i];c=math.cos(t);s=math.sin(t)
                if key.name==OPEN:analytic=Vector((-.0007*c,.0004*abs(s),(.002 if s>=0 else -.006)*abs(s)**.8))
                else:analytic=Vector((.0025*c,.0004*abs(c),.0020*abs(c)**2))
                delta=delta.lerp(analytic,blend)
            deltas[key.name].append(delta)
            if not key.mute:active+=delta*key.value
        bases.append(points[i]-active)
    basis=newobj.shape_key_add(name='Basis')
    for i,p in enumerate(bases):basis.data[i].co=p
    for key in keys[1:]:
        newkey=newobj.shape_key_add(name=key.name);newkey.value=key.value;newkey.mute=key.mute
        newkey.slider_min=key.slider_min;newkey.slider_max=key.slider_max
        for i,delta in enumerate(deltas[key.name]):newkey.data[i].co=bases[i]+delta
    newmesh.update()
    after=mixed(newobj)
    retained_error=max((after[mapping[i]]-coords[i]).length for i in used)
    authored_error=max((after[i]-points[i]).length for i in range(len(points)))
    if max(retained_error,authored_error)>.000001:raise RuntimeError('Mixed-coordinate reconstruction changed retained geometry')
    obj.hide_render=True;obj.hide_viewport=True
    newobj['aevrynd_revision']='female-next-r0003';newobj['aevrynd_release_state']='UNREVIEWED_STUDY'
    return newobj,{'boundaryVertices':len(order),'removedFaces':len(removed),'removedUnusedVertices':len(mesh.vertices)-len(used),'newVertices':len(points)-len(used),'newQuadFaces':(len(rings)-1)*len(order),'oldVertexCount':len(mesh.vertices),'newVertexCount':len(newmesh.vertices),'oldPolygonCount':len(mesh.polygons),'newPolygonCount':len(newmesh.polygons),'sourceShapeKeys':len(keys),'resultShapeKeys':len(newobj.data.shape_keys.key_blocks),'neutralGapM':gap,'maximumRetainedMixedErrorM':retained_error,'maximumAuthoredMixedErrorM':authored_error}

def collision(body,frame):
    bpy.context.scene.frame_set(frame);dg=bpy.context.evaluated_depsgraph_get();dg.update();ev=body.evaluated_get(dg);mesh=ev.to_mesh()
    verts=[ev.matrix_world@v.co for v in mesh.vertices];mesh.calc_loop_triangles();tris=[tuple(t.vertices) for t in mesh.loop_triangles]
    tree=BVHTree.FromPolygons(verts,tris,all_triangles=True)
    local=[t for t in tris if all(abs(verts[i].x)<.065 and 1.34<verts[i].z<1.43 and verts[i].y<-.07 for i in t)]
    mouthtree=BVHTree.FromPolygons(verts,local,all_triangles=True)
    pairs=[(a,b) for a,b in mouthtree.overlap(mouthtree) if a<b and set(local[a]).isdisjoint(local[b])]
    result={'mouthNonAdjacentTrianglePairs':len(pairs),'sampleMouthPairs':pairs[:8],'layers':{}}
    for name in (HAIR,'Brow_L','Brow_R','Brow_L_Density','Brow_R_Density'):
        obj=bpy.data.objects[name].evaluated_get(dg)
        coords=[p.position for p in obj.data.points] if obj.type=='CURVES' else [v.co for v in obj.data.vertices]
        values=[];bad=[]
        for i,p in enumerate(coords):
            world=obj.matrix_world@p;hit=tree.find_nearest(world)
            if hit[1] is None:continue
            value=(world-hit[0]).dot(hit[1].normalized());values.append(value)
            if value<0 and len(bad)<8:bad.append({'index':i,'signedM':value,'world':list(world)})
        result['layers'][name]={'pointsTested':len(values),'minimumSignedClearanceM':min(values),'negativePoints':sum(v<0 for v in values),'belowMinus50Micrometres':sum(v<-.00005 for v in values),'negativeSamples':bad}
    ev.to_mesh_clear();return result

def render(body,label,view,pose='neutral'):
    scene=bpy.context.scene;scene.frame_set(1)
    keys=body.data.shape_keys.key_blocks;keys[OPEN].value=1. if pose=='open' else 0.;keys[SMILE].value=1. if pose=='smile' else 0.
    camera=scene.camera
    views={'face':((0.,-.64,1.47),(0.,-.035,1.445),100,(1200,1000)), 'oblique':((.26,-.62,1.48),(0.,-.035,1.445),100,(1200,1000)), 'mouth':((0.,-.43,1.391),(0.,-.115,1.386),135,(1100,720)), 'mouth-oblique':((.105,-.43,1.391),(0.,-.115,1.386),135,(1100,720))}
    camera.location,target,camera.data.lens,size=views[view];camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.resolution_x,scene.render.resolution_y=size;scene.render.resolution_percentage=100
    path=OUT/f'{label}-{view}-{pose}.png';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    return str(path)

OUT.mkdir(parents=True,exist_ok=True)
variants=[]
for label,gap in (('baseline',None),)+VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene;scene.frame_set(1);body=bpy.data.objects[BODY]
    if gap is not None:body,edit=construct(body,gap)
    else:edit=None
    audits={str(f):collision(body,f) for f in FRAMES}
    expressions={}
    for pose,key in (('open',OPEN),('smile',SMILE)):
        body.data.shape_keys.key_blocks[key].value=1.;expressions[pose]=collision(body,1);body.data.shape_keys.key_blocks[key].value=0.
    scene.frame_set(1);bpy.context.view_layer.update()
    renders=[render(body,label,v) for v in ('face','oblique','mouth','mouth-oblique')]
    renders += [render(body,label,'mouth',p) for p in ('open','smile')]
    body.data.shape_keys.key_blocks[OPEN].value=0.;body.data.shape_keys.key_blocks[SMILE].value=0.
    output=None
    if gap is not None:
        scene['aevrynd_revision']='female-next-r0003-'+label;scene['aevrynd_release_state']='STUDY_NOT_PROMOTED';scene['aevrynd_website_promotion']='forbidden'
        output=SOURCES/f'aevrynd-female-next-r0003-{label}-study.blend';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(output))
    variants.append({'label':label,'edit':edit,'frameAudit':audits,'expressionAudit':expressions,'renders':renders,'output':str(output) if output else None,'sourceSha256':hashlib.sha256(output.read_bytes()).hexdigest() if output else None})
    (OUT/'female-next-r0003-perioral.report.json').write_text(json.dumps({'revision':'female-next-r0003','source':str(SRC),'variants':variants,'status':'VISUAL_REVIEW_PENDING','enginePromotionApproved':False,'websitePromotionApproved':False,'enginePerformance':{'status':'NOT_TESTED','cpuMs':None,'gpuMs':None,'memoryBytes':None}},indent=2)+'\n',encoding='utf-8')
    print('AFN_R0003_VARIANT='+json.dumps({'label':label,'edit':edit,'frameMouthPairs':{f:a['mouthNonAdjacentTrianglePairs'] for f,a in audits.items()},'expressionMouthPairs':{p:a['mouthNonAdjacentTrianglePairs'] for p,a in expressions.items()},'negativeHairAndBrows':sum(x['negativePoints'] for a in list(audits.values())+list(expressions.values()) for x in a['layers'].values())}),flush=True)
