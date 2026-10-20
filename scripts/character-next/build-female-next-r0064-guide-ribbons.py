"""Explicit complete wavy-bob guide/ribbon authoring on the r60 woman.

Control polygons are authored per anatomical region. Only the initial growth
row is attached to the real scalp; free lengths are not projected onto it.
Opaque first preview judges shape only, not finished hair or physical strands.
"""
from pathlib import Path
import bpy,numpy as np,json,math,time,importlib.util,hashlib,sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0064-guide-ribbons';E.mkdir(parents=True,exist_ok=True)
SRC=S/'aevrynd-female-next-r0060-b-limit-surface-assembly-study.blend';OUT=S/'aevrynd-female-next-r0064-a-authored-ribbon-blockout.blend'
def module(n,p):
    s=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
g=module('guide64base','build-female-next-r0061-surface-flow-groom.py');shade=module('guide64render','shade-female-next-r0061-physical-hair.py')
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unit(v):return v/max(np.linalg.norm(v),1e-20)

def polygons():
    rows=[]
    def add(name,region,points,width,layer=0):rows.append({'name':name,'region':region,'points':points,'widthM':width,'layer':layer})
    # Left-of-centre part terminates at mid crown. Forehead/eyes remain open.
    for i,y in enumerate((-.083,-.062,-.040,-.018)):
        add('R_front_sweep_'+str(i),'front',[
            (-.016,y,1.555),(.020,y-.005,1.571-i*.002),(.064,y-.006,1.550-i*.003),(.087,y-.004,1.509),(.097,y-.003,1.460),(.106,y+.002,1.407-i*.002),(.094,y+.010,1.369),(.103,y+.017,1.342-i*.004),(.091,y+.018,1.326-i*.003)],.023,0)
    for i,y in enumerate((-.086,-.061,-.036,-.011)):
        add('L_front_sweep_'+str(i),'front',[
            (-.022,y,1.552),(-.048,y-.003,1.558-i*.002),(-.076,y-.008,1.525),(-.092,y-.007,1.476),(-.103,y-.002,1.425),(-.091,y+.002,1.389),(-.104,y+.011,1.355),(-.093,y+.018,1.333+i*.002)],.022,0)
    # Independent crown-to-back guides: no part continued down the nape.
    for i,x in enumerate((-.060,-.040,-.020,0.,.020,.040,.060)):
        add('crown_back_'+str(i),'crown',[
            (x,.004,1.550-abs(x)*.15),(x,.033,1.557-abs(x)*.10),(x*1.23,.062,1.531),(x*1.43,.079,1.489),(x*1.53,.087,1.440),(x*1.47+.004,.092,1.397),(x*1.53-.004,.078,1.361),(x*1.43+.003,.076,1.338+(i%3)*.003),(x*1.34,.061,1.323+(i%2)*.004)],.027,0)
    # Ear-back side layers sit outside the pinna and flow into the back.
    for side in (-1,1):
        for i,y in enumerate((-.040,-.015,.010,.029)):
            add(('L' if side<0 else 'R')+'_ear_back_'+str(i),'side',[
                (side*.055,y,1.529),(side*.081,y+.006,1.515),(side*.094,y+.013,1.478),(side*.108,y+.014,1.433),(side*.100,y+.016,1.390),(side*.111,y+.020,1.358),(side*.099,y+.018,1.329+(i%2)*.005)],.024,1)
    for i,x in enumerate((-.065,-.043,-.021,0.,.021,.043,.065)):
        add('nape_under_'+str(i),'nape',[
            (x,.027,1.494),(x*1.08,.066,1.478),(x*1.16,.075,1.437),(x*1.22+.004,.080,1.398),(x*1.15-.004,.070,1.365),(x*1.20+.003,.069,1.340),(x*1.1,.054,1.319+(i%3)*.004)],.025,0)
    # Two shorter face-framing pieces; their ends stay lateral to the eyes.
    for side in (-1,1):
        add(('L' if side<0 else 'R')+'_face_frame','fringe',[
            (side*.014,-.100,1.536),(side*.028,-.126,1.539),(side*.051,-.139,1.518),(side*.067,-.134,1.492),(side*.079,-.121,1.468),(side*.088,-.107,1.446),(side*.080,-.092,1.427)],.012,2)
    return rows

def bezier(P,steps=6):
    left=[];right=[]
    for i,p in enumerate(P):
        tangent=(P[min(i+1,len(P)-1)]-P[max(0,i-1)])/ (6 if 0<i<len(P)-1 else 3)
        left.append(p-tangent);right.append(p+tangent)
    result=[]
    for i in range(len(P)-1):
        for t in np.linspace(0,1,steps,endpoint=False):result.append((1-t)**3*P[i]+3*(1-t)**2*t*right[i]+3*(1-t)*t*t*left[i+1]+t**3*P[i+1])
    result.append(P[-1]);return np.array(result),np.array(left),np.array(right)

def material():
    mat=bpy.data.materials.new('AFN64_OPAQUE_SHAPE_REVIEW_ONLY');mat.use_nodes=True;t=mat.node_tree;t.nodes.clear();n=t.nodes.new('ShaderNodeBsdfPrincipled');out=t.nodes.new('ShaderNodeOutputMaterial');t.links.new(n.outputs['BSDF'],out.inputs['Surface']);n.inputs['Base Color'].default_value=(.055,.021,.010,1);n.inputs['Roughness'].default_value=.62;return mat

def build():
    tick=time.time();assert not OUT.exists();assert sha(SRC)==g.SOURCE_SHA
    save('round-contract.json',{'previousGoalTurnClassification':'progress: r63 actual complete crop, seven views, source/history reopen, real self witnesses and three-round review archived and GitHubba95e8d verified; no appearance gain.',
      'sixLines':['Exact r60B complete woman SHA3324231...; no live heavy job or r64 asset at start.','Main: no natural complete hairstyle; secondary flat skin/eye response. Stop rejected scalar comb/lift and isolated solver route.','Deliver an explicit editable complete guide/ribbon wavy-bob shape on the same complete woman; if geometry reads naturally, convert into actual textured hair cards in this source.','Study real front/side/back sectioning and layered perimeter; author front sweeps, ear-back, crown and nape control polygons individually. Only initial growth row attaches to actual scalp.','First cheap opaque complete-head/body views; reject horns, twin shells, missing crown coverage or incoherent perimeter before atlas/physics. Opaque geometry is not realistic hair acceptance.','One heavy job,4threads; diagnosis10min, preview before45min; one candidate, no density/radius/angle sweeps.'],
      'references':[{'url':'https://www.sexyhair.com/wp-content/uploads/2026/02/2026-Transformational-Cutting-Digital-Workbook.pdf','pages':[9,10],'use':'Real haircut front/side/back sectioning, separate fringe/ear-back/crown/nape and layered perimeter. Visual reference only; no images/geometry copied into assets or redistributed.'},{'url':'https://dev.epicgames.com/documentation/en-us/unreal-engine/setting-up-cards-and-meshes-for-grooms-in-unreal-engine','use':'Mesh/texture/guide/LOD representation principles only; no engine/plugin/assets installed or copied.'}],
      'notReused':['r63 paths, lift field and scalp chart','r61 gathered scalp/tie routes','donor Bob or shell clump geometry']})
    bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.scene.frame_set(1);stage=g.k.f.v.stage();body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];levels=[]
    for md in body.modifiers:
        if md.type=='SUBSURF':levels.append((md,md.levels));md.levels=md.render_levels
    bpy.context.view_layer.update();row=g.k.mesh(body);V,T=row['V'],row['T'];ids=np.flatnonzero(np.isin(row['mi'],(4,5))&(V[T,2].min(1)>1.36));tree=BVHTree.FromPolygons(V.tolist(),T[ids].tolist(),all_triangles=True);C=np.array((0.,-.038,1.471))
    def foot(p):
        ray=unit(p-C);h=tree.ray_cast(Vector(C+ray*.4),Vector(-ray),.65);assert h[0] is not None;ti=int(ids[h[2]]);tri=V[T[ti]];w=np.linalg.lstsq((tri[1:]-tri[0]).T,np.array(h[0])-tri[0],rcond=None)[0];bc=np.r_[1-w.sum(),w];assert bc.min()>-1e-4;return bc@tri,ti,bc
    coll=bpy.data.collections.new('AFN64_AUTHORED_HAIR');bpy.context.scene.collection.children.link(coll);mat=material();descriptor=[]
    for index,rec in enumerate(polygons()):
        P=np.array(rec['points'],'f8');root,ti,bc=foot(P[0]);P[0]=root;Q,left,right=bezier(P);name='AFN64_'+rec['name']
        cu=bpy.data.curves.new(name+'_EDIT_GUIDE','CURVE');cu.dimensions='3D';sp=cu.splines.new('BEZIER');sp.bezier_points.add(len(P)-1)
        for p,co,le,ri in zip(sp.bezier_points,P,left,right):p.co=co;p.handle_left_type='FREE';p.handle_right_type='FREE';p.handle_left=le;p.handle_right=ri
        ob=bpy.data.objects.new(name+'_EDIT_GUIDE',cu);coll.objects.link(ob);ob.hide_render=True;ob['scope']='Editable master guide for the paired card, no accepted dynamics.'
        tangent=np.gradient(Q,axis=0);tangent/=np.linalg.norm(tangent,axis=1)[:,None];radial=(Q-C)*np.array((1.,1.,.20));width=np.cross(tangent,radial);width/=np.maximum(np.linalg.norm(width,axis=1),1e-12)[:,None];normal=np.cross(width,tangent);normal/=np.linalg.norm(normal,axis=1)[:,None]
        # Independent authored lengths, layered exits and broad cross-section.
        # Opaque rectangular cards cannot stand in for final fibre appearance.
        s=np.linspace(0,1,len(Q));ww=rec['widthM']*(.84+.16*np.sin(np.pi*s));ww*=1-.25*s**5
        vertices=[];rootrows=[]
        for j in range(len(Q)):
            for c in (-1,0,1):
                pos=Q[j]+width[j]*ww[j]*.5*c+normal[j]*(.0015*(1-c*c)+.002*rec['layer'])*min(1,s[j]*12)
                if j==0:
                    pos,rt,rb=foot(pos);rootrows.append([rt,int(row['nativeTriangleFace'][rt]),*rb])
                vertices.append(pos)
        faces=[(j*3+c,j*3+c+1,(j+1)*3+c+1,(j+1)*3+c) for j in range(len(Q)-1) for c in range(2)]
        me=bpy.data.meshes.new(name+'_CARD');me.from_pydata(vertices,[],faces);me.update();uv=me.uv_layers.new(name='AFN64_CardUV')
        for poly in me.polygons:
            poly.use_smooth=True
            for li in poly.loop_indices:
                vi=me.loops[li].vertex_index;uv.data[li].uv=(vi%3/2,vi//3/(len(Q)-1))
        card=bpy.data.objects.new(name+'_CARD',me);coll.objects.link(card);me.materials.append(mat);card['region']=rec['region'];card['masterGuide']=ob.name;card['scope']='Opaque shape blockout only; 0-thickness mesh, no per-fibre or contact/dynamic acceptance.';card['rootRowsJSON']=json.dumps(rootrows)
        descriptor.append({**rec,'points':P.tolist(),'guideObject':ob.name,'cardObject':card.name,'rootRows':rootrows,'centreRoot':[ti,int(row['nativeTriangleFace'][ti]),*bc],'vertices':len(vertices),'faces':len(faces)})
    old=bpy.data.objects['AFN57_CANONICAL_BOB_GUIDES'];old.hide_render=True;old.hide_set(True)
    for md,level in levels:md.levels=level
    assert g.k.f.v.stage()==stage
    save('a-guide-authoring.json',{'schema':1,'units':'metres','representation':'Explicit Bezier masters and 3-column UV ribbons; opaque shape blockout only','guides':descriptor,'source':str(SRC),'sourceSha256':sha(SRC)})
    settings=shade.settings();g.k.b.camera('face');bpy.context.preferences.filepaths.save_version=0;bpy.context.scene['AFN64_status']='COMPLETE_OPAQUE_RIBBON_SHAPE_BLOCKOUT_NOT_REALISTIC_HAIR';bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save('a-build-summary.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(OUT),'outputSha256':sha(OUT),'guides':len(descriptor),'cards':len(descriptor),'vertices':sum(x['vertices'] for x in descriptor),'quads':sum(x['faces'] for x in descriptor),'settings':settings,'actualHairAppearanceAcceptance':False,'contactOrDynamicsAccepted':False,'secondsBeforePreview':time.time()-tick})
    print('R64_NATIVE_GUIDES_AND_RIBBONS_SAVED',len(descriptor),time.time()-tick,flush=True)

def main():
    g.E=E;g.k.f.E=E;shade.g.E=E
    if '--views' in sys.argv:
        ref=json.loads((E/'a-build-summary.json').read_text());assert sha(OUT)==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(OUT));shade.settings();save('a-extra-view-controls.json',shade.render('a-shape',('oblique','opposite-oblique','alternate-oblique','body-face')));return
    build();save('a-first-view-controls.json',shade.render('a-shape',('face','profile','back')))
if __name__=='__main__':main()
