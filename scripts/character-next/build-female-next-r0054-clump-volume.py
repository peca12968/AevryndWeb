"""Complete editable quad-clump volume blockout, explicitly an authoring proxy.

Native Skin/Subdivision construction produces separate mesh masses for silhouette
editing. No old r48/r53 guide route, shared exit ring, fibre interpolation,
shader trick or density expansion is used. This is not final physical hair.
"""
from pathlib import Path
import bpy,importlib.util,numpy as np,json,time
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('base54',Path(__file__).with_name('build-female-next-r0053-scalp-foundation.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
b=k.b;f=k.f;E=b.R/'Evidence/character-female-next/r0054-clump-volume';E.mkdir(parents=True,exist_ok=True)
SRC=b.S/'aevrynd-female-next-r0053-authoring-retained.blend'
OUT=b.S/'aevrynd-female-next-r0054-a-clump-volume-blockout.blend'
# Independent artist mass stations on this head, in metres. They specify mesh
# construction only, not final root/strand curves or a validated hair surface.
LEFT=[
 ('front_frame',[[-.004,-.088,1.548],[-.031,-.102,1.550],[-.067,-.092,1.512],[-.086,-.078,1.455],[-.086,-.066,1.391],[-.077,-.055,1.347]],.018,.007),
 ('front_crown',[[-.004,-.067,1.558],[-.039,-.086,1.562],[-.076,-.069,1.518],[-.091,-.057,1.450],[-.091,-.047,1.390],[-.082,-.038,1.351]],.021,.009),
 ('side_crown',[[-.004,-.039,1.562],[-.046,-.046,1.562],[-.082,-.034,1.513],[-.094,-.020,1.448],[-.094,-.012,1.386],[-.082,-.005,1.342]],.023,.010),
 ('side_back',[[-.004,-.010,1.558],[-.046,.004,1.552],[-.080,.019,1.508],[-.092,.031,1.443],[-.089,.039,1.381],[-.076,.042,1.339]],.023,.010),
 ('occipital',[[-.004,.018,1.547],[-.039,.042,1.542],[-.070,.059,1.490],[-.079,.072,1.429],[-.072,.074,1.376],[-.059,.063,1.343]],.025,.011),
 ('rear_centre',[[-.004,.034,1.531],[-.024,.061,1.519],[-.046,.075,1.470],[-.048,.083,1.414],[-.041,.081,1.371],[-.023,.069,1.345]],.024,.011)]

def save(name,row):(E/name).write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def material():
    m=bpy.data.materials.new('AFN54_IDENTICAL_CLAY_PROXY');m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.18,.20,.22,1)
    bs.inputs['Roughness'].default_value=.66;bs.inputs['Metallic'].default_value=0
    bs.inputs['Subsurface Weight'].default_value=0;m.diffuse_color=(.18,.20,.22,1)
    return m

def clump(name,P,width,depth,mat,collection,index,skin):
    # Attach the construction start to the already retained actual scalp. It
    # is a volume centre, not a new follicle or a root moved to hide collision.
    hit=skin.find_nearest(Vector(P[0]));P[0]=np.array(hit[0])+np.array(hit[1])*.003
    mesh=bpy.data.meshes.new('AFN54_'+name);mesh.from_pydata(P.tolist(),[(i,i+1) for i in range(len(P)-1)],[]);mesh.update()
    ob=bpy.data.objects.new(mesh.name,mesh);collection.objects.link(ob)
    for obj in bpy.context.view_layer.objects:obj.select_set(False)
    ob.select_set(True);bpy.context.view_layer.objects.active=ob
    modifier=ob.modifiers.new('AFN54_NativeSkinConstruction','SKIN')
    radii=[]
    for j,vertex in enumerate(mesh.skin_vertices[0].data):
        u=j/(len(P)-1);weight=float(np.interp(u,[0,.18,.55,.82,1],[.35,.90,1,.88,.23]))
        vertex.radius=(width*weight,depth*weight);vertex.use_root=(j==0);radii.append(list(vertex.radius))
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    for face in ob.data.polygons:face.use_smooth=True
    faceSet=ob.data.attributes.new('.sculpt_face_set','INT','FACE');faceSet.data.foreach_set('value',[index+1]*len(ob.data.polygons))
    smooth=ob.modifiers.new('AFN54_EditableQuadSmoothing','SUBSURF');smooth.subdivision_type='CATMULL_CLARK';smooth.levels=2;smooth.render_levels=2
    ob.data.materials.append(mat);ob['aevrynd_layer']='AUTHORING_VOLUME_PROXY_NOT_HAIR'
    ob['scope']='Independent editable quad hair-mass blockout. May overlap other clumps/root skin as a design volume; no physical contact or final strand claim.'
    X,T=b.evaluated(ob,True)
    return {'object':ob.name,'constructionStationsM':P.tolist(),'skinConstructionRadiiM':radii,
            'nativeVertices':len(ob.data.vertices),'nativeQuads':sum(len(p.vertices)==4 for p in ob.data.polygons),
            'nativeFaces':len(ob.data.polygons),'evaluatedTriangles':len(T),'boundsM':[X.min(0).tolist(),X.max(0).tolist()]}

def orthographic(label):
    scene=bpy.context.scene;cam=scene.camera;oldType=cam.data.type
    rows=[]
    for view,position in [('ortho-front',(0,-.9,1.44)),('ortho-profile',(.9,-.02,1.44)),('ortho-back',(0,.9,1.44))]:
        cam.data.type='ORTHO';cam.data.ortho_scale=.44;cam.location=position
        cam.rotation_euler=(Vector((0,-.02,1.44))-cam.location).to_track_quat('-Z','Y').to_euler()
        bpy.context.view_layer.update();scene.render.filepath=str(E/f'{label}-{view}.png');bpy.ops.render.render(write_still=True)
        rows.append({'view':view,'matrix':b.matrix(cam.matrix_world),'orthoScale':cam.data.ortho_scale,'stage':f.v.stage()})
    cam.data.type=oldType;b.camera('face');save(label+'-orthographic.json',rows)

def main():
    tick=time.time();assert b.sha(SRC)=='c293976b2745e372565eb990f2e844a8255f2cdaad8e004563643d0f51c9f537'
    save('round-contract.json',{'revision':'female-next-r0054','previousGoalTurnClassification':'progress: r53 retained64skin/root authoring and corrected native sampling; full old-guide-directed hair shape rejected and history pushedd64bfba. No complete appearance gain.',
        'source':str(SRC),'sourceSha256':b.sha(SRC),'mainDefect':'Coherent natural complete-head hair mass absent; previous route templates produce a scaffold.',
        'referenceDecision':'Professional haircut section/perimeter principles plus Blender separate quad-clump/Skin/Face Sets workflow. Textual sources read; browser screenshot API could not capture the reference photos, so no photo alignment or measured photo silhouette is claimed.',
        'sources':['https://www.samvilla.com/blogs/hair-tutorials/lived-in-precision','https://www.au-be.jp/column/bg9lrse_vnq/','https://studio.blender.org/training/blender-fundamentals-45-lts/using-multiple-objects/','https://studio.blender.org/training/blender-fundamentals-45-lts/fine-control/'],
        'expectedVisibleChange':'12independent closer-fitting crown-to-side/back masses, restrained crown height, continuous rounded outer contour and inward ends; no roof/spikes or common exit ring.',
        'smallTest':'One complete12clump volume blockout in actual full-head/body, ortho and alternate-light views before fibres.',
        'reject':['Roof/scaffold/cap or incoherent perimeter','Primitive sausages cannot define a natural mass','No useful full-head form improvement'],
        'candidateCount':1,'startUTC':'2026-10-19 19:42:36 UTC','checkpointUTC':'2026-10-19 20:27:36 UTC','threads':4,'heavyJobsAtOnce':1,
        'scope':'Editable design proxy only; not final hair, a collision proxy, new physical groom, dynamics or runtime.'})
    bpy.ops.wm.open_mainfile(filepath=str(SRC));before=f.state();domain=bpy.data.objects['AFN53_ANATOMICAL_SCALP']
    V,T=b.evaluated(domain,True);skin=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True)
    collection=bpy.data.collections.new('AFN54_AUTHORING_VOLUME_PROXIES');bpy.context.scene.collection.children.link(collection)
    mat=material();rows=[]
    for side in (-1,1):
        for j,(name,stations,width,depth) in enumerate(LEFT):
            P=np.array(stations,dtype='f8')
            if side==1:
                P[:,0]*=-1;P[:,1]+=.0015*np.linspace(0,1,len(P));P[:,2]+=np.linspace(.0005,.0035 if j<2 else -.0015,len(P))
            rows.append(clump(('L_' if side<0 else 'R_')+name,P,width,depth,mat,collection,len(rows),skin))
    old=bpy.data.objects[k.OLD];old.hide_render=True;old.hide_set(True)
    after=f.state()
    assert all(after['meshes'][name]==row for name,row in before['meshes'].items())
    assert all(after['materials'][name]==row for name,row in before['materials'].items())
    assert after['skinFields']==before['skinFields'] and after['stage']==before['stage'] and after['curves']==before['curves']
    b.camera('face');bpy.context.scene.camera.data.lens=85
    bpy.context.scene['AFN54_status']='CLAY_MASS_BLOCKOUT_PROXY_PENDING_VISUAL_REVIEW_NOT_FINAL_HAIR'
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save('a-build-summary.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'output':str(OUT),'outputSha256':b.sha(OUT),
        'clumps':rows,'originalCharacterGeometrySkinMaterialsHairDataAndStageUnchanged':True,'status':'PROXY_BLOCKOUT_PENDING_VISUAL_REVIEW',
        'noOldGuideRoutesUsed':True,'physicalHairContact':'NOT_TESTED_DESIGN_PROXY','newDenseFibres':0,'seconds':time.time()-tick})
    f.E=E;f.render('a-proxy',('face','oblique','profile'));k.k.k.a.i.ch.review.extras('a-proxy',E);orthographic('a-proxy')
    print('R54_BLOCKOUT_READY',len(rows),time.time()-tick,flush=True)

if __name__=='__main__':main()
