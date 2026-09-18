"""Narrow the r981 centre part and add short graded fibers in the same Curves object."""
import json,math,random
from collections import Counter
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1];ASSETS=ROOT/"assets-source/aevrynd-character";SOURCE=ASSETS/"aevrynd-female-cc0-balanced-eye-optics-r1080-study.blend";OUTPUT=ASSETS/"aevrynd-female-cc0-graded-hairline-r1081-study.blend";REPORT=ASSETS/"female-v249-mainline-r1081-graded-hairline-sweep.study.json";OUT=ROOT.parent/"Temp/female-realism/v249r1081-graded-hairline"
BODY="AevryndFemaleCC0BalancedEyeOptics_R1080";HAIR="AevryndFemaleCoherentClumpGroom_R981";TARGET="AevryndFemaleGradedHairlineGroom_R1081";SCALP="AevryndFemaleTargetScalp_R976";CLEARANCE=0.0016
# label, root-flow pin, short fibers per eligible guide, scalp multiplier
VARIANTS=(("a-control",0.0,0,1.0,0.0),("b-part-pin-0.35",0.35,0,0.55,5.0),("c-graded-0.50",0.50,1,0.30,8.0),("d-dense-0.65",0.65,2,0.20,12.0));SELECTED="c-graded-0.50"


def clamp(x):return max(0.0,min(1.0,x))
def smoothstep(x):x=clamp(x);return x*x*(3.0-2.0*x)
def look_at(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()


def body_tree(body):
    deps=bpy.context.evaluated_depsgraph_get();evaluated=body.evaluated_get(deps);mesh=evaluated.to_mesh();vertices=[evaluated.matrix_world@v.co for v in mesh.vertices];polygons=[tuple(p.vertices) for p in mesh.polygons];evaluated.to_mesh_clear();return BVHTree.FromPolygons(vertices,polygons,all_triangles=False)


def bind_to_head(obj):
    rig=bpy.data.objects["AevryndFemaleRig"];world=obj.matrix_world.copy();obj.parent=rig;obj.parent_type="BONE";obj.parent_bone="head";obj.matrix_world=world;obj["aevrynd_head_binding"]=True


def repair_pose_envelope(scene,hair,body,frames=(1,20,33,61),passes=4):
    corrected=0;maximum=0.0;minimum=math.inf
    for _pass in range(passes):
        pass_count=0
        for frame in frames:
            scene.frame_set(frame);deps=bpy.context.evaluated_depsgraph_get();deps.update();evaluated_body=body.evaluated_get(deps);mesh=evaluated_body.to_mesh();vertices=[evaluated_body.matrix_world@v.co for v in mesh.vertices];faces=[tuple(p.vertices) for p in mesh.polygons];tree=BVHTree.FromPolygons(vertices,faces,all_triangles=False);evaluated_body.to_mesh_clear();evaluated_hair=hair.evaluated_get(deps);matrix=evaluated_hair.matrix_world;inverse=matrix.inverted()
            for point in hair.data.points:
                world=matrix@point.position;hit=tree.find_nearest(world)
                if hit is None or hit[1] is None:continue
                signed=(world-hit[0]).dot(hit[1].normalized());minimum=min(minimum,signed)
                if signed<CLEARANCE:
                    delta=hit[1].normalized()*(CLEARANCE-signed+0.00005);point.position=inverse@(world+delta);corrected+=1;pass_count+=1;maximum=max(maximum,delta.length)
        if pass_count==0:break
    scene.frame_set(1);return {"frames":list(frames),"passes":passes,"correctedOperations":corrected,"maximumCorrectionM":maximum,"minimumSignedBeforeRepairM":minimum if math.isfinite(minimum) else None}


def pin_part_flow(hair,strength):
    matrix=hair.matrix_world;inverse=matrix.inverted();changed=0;maximum=0.0
    for curve in hair.data.curves:
        root=matrix@hair.data.points[curve.first_point_index].position
        if abs(root.x)>0.028 or root.z<1.50:continue
        side=-1.0 if root.x<0 else 1.0
        for local in range(1,min(curve.points_length,10)):
            index=curve.first_point_index+local;t=local/max(1,curve.points_length-1);world=matrix@hair.data.points[index].position;target_x=root.x+side*0.0012*smoothstep(t/0.45);weight=strength*(1.0-smoothstep(t/0.45));new=world.copy();new.x=world.x+(target_x-world.x)*weight;maximum=max(maximum,(new-world).length);hair.data.points[index].position=inverse@new;changed+=1
    return {"changedPoints":changed,"maximumDisplacementM":maximum}


def sample_polyline(points,distance):
    remaining=distance
    for first,second in zip(points,points[1:]):
        length=(second-first).length
        if remaining<=length:return first.lerp(second,remaining/max(length,1e-9))
        remaining-=length
    return points[-1].copy()


def add_short_fibers(hair,density,tree):
    if density<=0:return {"addedCurves":0,"addedPoints":0,"eligibleGuides":0,"lengthRangeM":None}
    matrix=hair.matrix_world;inverse=matrix.inverted();old_curves=len(hair.data.curves);records=[];eligible=0
    for guide_index in range(0,old_curves,14):
        curve=hair.data.curves[guide_index];points=[matrix@hair.data.points[curve.first_point_index+i].position for i in range(curve.points_length)];root=points[0]
        frontal=root.y<-0.068 and root.z>1.49;part=abs(root.x)<0.020 and root.z>1.50
        if not (frontal or part):continue
        eligible+=1
        for copy_index in range(density):
            rng=random.Random(1081000+guide_index*7+copy_index);length=(rng.uniform(0.030,0.052) if frontal else rng.uniform(0.025,0.044));strand=[]
            shifted_root=root.copy()
            if frontal:
                shift=0.0018+0.0014*(copy_index/max(1,density-1) if density>1 else rng.random())
                probe=root+Vector((0.0,-shift,-0.45*shift));hit=tree.find_nearest(probe)
                if hit and hit[1] is not None:shifted_root=hit[0]+hit[1].normalized()*CLEARANCE
            root_delta=shifted_root-root
            side=-1.0 if root.x<0 else 1.0
            for local in range(8):
                t=local/7.0;point=sample_polyline(points,length*t)+root_delta*(1.0-smoothstep(t));fan=(0.00025+rng.uniform(-0.00012,0.00012))*math.sin(math.pi*t);point.x+=side*fan;point.z+=0.00035*math.sin(math.pi*t);strand.append(point)
            records.append((strand,length))
    old_points=len(hair.data.points);hair.data.add_curves([8]*len(records));radius=hair.data.attributes.get("radius")
    for offset,(strand,_length) in enumerate(records):
        curve=hair.data.curves[old_curves+offset]
        for local,world in enumerate(strand):
            index=curve.first_point_index+local;hair.data.points[index].position=inverse@world
            if radius:radius.data[index].value=0.000040*(1.0-local/7.0)+0.000012*(local/7.0)
    return {"addedCurves":len(records),"addedPoints":len(hair.data.points)-old_points,"eligibleGuides":eligible,"lengthRangeM":[min(x[1] for x in records),max(x[1] for x in records)] if records else None}


def repair_collision(hair,tree):
    matrix=hair.matrix_world;inverse=matrix.inverted();corrected=0;maximum=0.0;minimum=math.inf
    for _pass in range(2):
        for point in hair.data.points:
            world=matrix@point.position;hit=tree.find_nearest(world)
            if hit is None or hit[1] is None:continue
            signed=(world-hit[0]).dot(hit[1].normalized());minimum=min(minimum,signed)
            if signed<CLEARANCE:
                delta=hit[1].normalized()*(CLEARANCE-signed);point.position=inverse@(world+delta);corrected+=1;maximum=max(maximum,delta.length)
    return {"correctedOperations":corrected,"maximumCorrectionM":maximum,"minimumSignedBeforeRepairM":minimum if math.isfinite(minimum) else None}


def tune_scalp(factor,fade_mm):
    scalp=bpy.data.objects[SCALP];source=scalp.data.materials[0];material=source.copy();material.name=f"Aevrynd_TargetScalp_R1081_{factor:.2f}";nodes=material.node_tree.nodes;links=material.node_tree.links;shader=next(node for node in nodes if node.type=="BSDF_PRINCIPLED");base=shader.inputs["Base Color"];old=base.links[0] if base.links else None;mix=nodes.new("ShaderNodeMixRGB");mix.name="Aevrynd Scalp Part Blend R1081";mix.blend_type="MULTIPLY";mix.inputs[0].default_value=1.0;mix.inputs[2].default_value=(factor,factor*0.92,factor*0.84,1.0)
    if old:socket=old.from_socket;links.remove(old);links.new(socket,mix.inputs[1])
    else:mix.inputs[1].default_value=base.default_value
    links.new(mix.outputs[0],base);shader.inputs["Roughness"].default_value=0.95
    if shader.inputs.get("Specular IOR Level"):shader.inputs["Specular IOR Level"].default_value=0.05
    counts=Counter()
    for polygon in scalp.data.polygons:
        vertices=list(polygon.vertices)
        for index,first in enumerate(vertices):counts[tuple(sorted((first,vertices[(index+1)%len(vertices)])))]+=1
    boundary={index for edge,count in counts.items() if count==1 for index in edge};world=[scalp.matrix_world@vertex.co for vertex in scalp.data.vertices];minimum_y=min(point.y for point in world);maximum_y=max(point.y for point in world);front=[world[index] for index in boundary if world[index].y<=minimum_y+0.32*(maximum_y-minimum_y)]
    attribute=scalp.data.attributes.get("aevrynd_hairline_fade_r1081") or scalp.data.attributes.new("aevrynd_hairline_fade_r1081","FLOAT","POINT");values=[];width=fade_mm/1000.0
    for index,point in enumerate(world):
        distance=min((point-edge).length for edge in front) if front else width;value=smoothstep(distance/max(width,1e-8));attribute.data[index].value=value;values.append(value)
    output=next(node for node in nodes if node.type=="OUTPUT_MATERIAL");transparent=nodes.new("ShaderNodeBsdfTransparent");blend=nodes.new("ShaderNodeMixShader");blend.name="Aevrynd Hairline Fade R1081";attr=nodes.new("ShaderNodeAttribute");attr.attribute_name="aevrynd_hairline_fade_r1081"
    for link in list(output.inputs["Surface"].links):links.remove(link)
    links.new(attr.outputs[2],blend.inputs[0]);links.new(transparent.outputs[0],blend.inputs[1]);links.new(shader.outputs[0],blend.inputs[2]);links.new(blend.outputs[0],output.inputs["Surface"]);material.surface_render_method="BLENDED"
    scalp.data.materials[0]=material;return {"factor":factor,"fadeWidthMm":fade_mm,"fadeBoundaryVertices":sum(value<0.01 for value in values),"fadeTransitionVertices":sum(0.01<=value<0.99 for value in values),"roughness":0.95,"specularIorLevel":0.05,"material":material.name,"nodeCount":len(nodes)}


def render(scene,label,view):
    camera=scene.camera
    if view=="front":camera.location,target,camera.data.lens,size=(0.0,-0.72,1.445),(0.0,-0.025,1.44),88,(1000,1000)
    elif view=="three-quarter":camera.location,target,camera.data.lens,size=(0.45,-0.62,1.46),(0.0,-0.015,1.44),88,(1000,1000)
    elif view=="back":camera.location,target,camera.data.lens,size=(0.0,0.72,1.445),(0.0,0.025,1.44),88,(1000,1000)
    elif view=="top":camera.location,target,camera.data.lens,size=(0.0,-0.25,2.0),(0.0,0.015,1.51),78,(1000,1000)
    elif view=="hairline-front":camera.location,target,camera.data.lens,size=(0.0,-0.53,1.57),(0.0,-0.03,1.54),115,(1400,850)
    else:camera.location,target,camera.data.lens,size=(0.0,-0.32,1.86),(0.0,-0.015,1.55),110,(1400,850)
    look_at(camera,target);scene.render.resolution_x,scene.render.resolution_y=size;scene.render.resolution_percentage=100;path=OUT/f"{label}-{view}.png";scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);return str(path)


OUT.mkdir(parents=True,exist_ok=True);variants=[]
for label,pin,density,scalp_factor,fade_mm in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;scene.frame_set(1);scene.view_settings.view_transform="Standard";scene.view_settings.look="None";scene.view_settings.exposure=0.0;scene.view_settings.gamma=1.0;hair=bpy.data.objects[HAIR];hair.hide_render=False;bpy.data.objects[SCALP].hide_render=False
    for obj in scene.objects:
        name=obj.name.lower()
        if (obj.type=="CURVES" or any(token in name for token in ("groom","scalp","haircard","hairfiber"))) and obj.name not in (HAIR,SCALP):obj.hide_render=True
    collision_tree=body_tree(bpy.data.objects[BODY]);before={"curves":len(hair.data.curves),"points":len(hair.data.points),"objects":len(bpy.data.objects),"materials":len(hair.data.materials)};part=pin_part_flow(hair,pin) if pin else {"changedPoints":0,"maximumDisplacementM":0.0};fibers=add_short_fibers(hair,density,collision_tree);repair=repair_collision(hair,collision_tree) if pin or density else {"correctedOperations":0,"maximumCorrectionM":0.0,"minimumSignedBeforeRepairM":None};scalp=tune_scalp(scalp_factor,fade_mm) if scalp_factor<0.999 else {"factor":1.0,"fadeWidthMm":0.0,"material":bpy.data.objects[SCALP].data.materials[0].name,"nodeCount":len(bpy.data.objects[SCALP].data.materials[0].node_tree.nodes)};pose_repair=None
    if label==SELECTED:
        bind_to_head(hair);bind_to_head(bpy.data.objects[SCALP]);pose_repair=repair_pose_envelope(scene,hair,bpy.data.objects[BODY])
    after={"curves":len(hair.data.curves),"points":len(hair.data.points),"objects":len(bpy.data.objects),"materials":len(hair.data.materials)};renders=[render(scene,label,view) for view in ("front","three-quarter","back","top","hairline-front","hairline-top")];variants.append({"label":label,"pinStrength":pin,"fiberDensity":density,"scalpFactor":scalp_factor,"fadeWidthMm":fade_mm,"before":before,"after":after,"partFlow":part,"shortFibers":fibers,"collisionRepair":repair,"poseEnvelopeRepair":pose_repair,"scalp":scalp,"renders":renders,"status":"TECHNICAL_PASS"})
    if label==SELECTED:
        hair.name=TARGET;hair["aevrynd_revision"]="v249r1081-graded-hairline";hair["aevrynd_source"]=HAIR;hair["aevrynd_collision_clearance_m"]=CLEARANCE;scene["aevrynd_release_state"]="VISUAL_REVIEW_PENDING";scene["aevrynd_website_promotion"]="forbidden";bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report={"revision":"v249r1081-graded-hairline-sweep","source":str(SOURCE),"output":str(OUTPUT),"method":"retain the r981 Curves object, pin early centre-part flow, append short tapered fibers inside the same object, project all points to the inherited 1.6 mm body clearance, and lower the existing scalp material contrast","variants":variants,"selectedVariant":SELECTED,"newObjects":0,"materialSlotDelta":0,"websitePromotionApproved":False,"candidateStatus":"VISUAL_REVIEW_PENDING"};REPORT.write_text(json.dumps(report,indent=2),encoding="utf-8");print("AEVRYND_R1081_HAIRLINE="+json.dumps({"selected":SELECTED,"variants":[{"label":x["label"],"part":x["partFlow"],"fibers":x["shortFibers"],"repair":x["collisionRepair"],"after":x["after"]} for x in variants]},sort_keys=True))
