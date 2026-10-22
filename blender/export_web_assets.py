"""Optimize original Blender environment and OSM-derived course for Three.js.
Preserves originals; emits merged-per-material GLBs without external codecs.
Run blender -b --factory-startup -t 4 --python blender/export_web_assets.py
"""
import bpy, json, math, shutil, hashlib, sys, struct
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/web';PUBLIC=ROOT/'web/public/assets'
OUT.mkdir(parents=True,exist_ok=True);PUBLIC.mkdir(parents=True,exist_ok=True)
STAGE_ONLY='--stage-only' in sys.argv
TERRAIN_ONLY='--terrain-only' in sys.argv
ENV=ROOT/'assets/environment/Kerala_Coastal_Assets.blend';COURSE=ROOT/'assets/course/Kappil_Coast.blend'
REPORT={'generator':'blender/export_web_assets.py','blender':bpy.app.version_string,'units':'meters','axes':'glTF/Three.js +X = Blender +X; Three +Y = Blender +Z; Three -Z = Blender +Y. Do not rotate the loaded root again.','material_policy':'Simple original PBR palette. Palm leaf hues baked as vertex color into one leaf material. No external textures or runtime compression decoder needed.','environment_provenance':'Original Blender geometry; see assets/environment/LICENSE.txt. Original high-detail assets preserved.','course_provenance':'OSM-derived course geometry: © OpenStreetMap contributors, ODbL. See references/route/README.md. Artistic road width, elevation, furniture.','assets':{},'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ENV,COURSE) if p.exists()}}

def tri_count(o):return sum(len(p.vertices)-2 for p in o.data.polygons)
def clean_mat(src,key,leaf=False):
    name='WEB_'+key
    m=bpy.data.materials.get(name)
    if m:return m
    m=bpy.data.materials.new(name);m.use_nodes=True
    node=m.node_tree.nodes.get('Principled BSDF');old=src.node_tree.nodes.get('Principled BSDF') if src and src.use_nodes else None
    color=old.inputs['Base Color'].default_value[:] if old else (.3,.3,.3,1)
    node.inputs['Base Color'].default_value=(1,1,1,1) if leaf else color
    node.inputs['Roughness'].default_value=old.inputs['Roughness'].default_value if old else .65
    node.inputs['Metallic'].default_value=old.inputs['Metallic'].default_value if old else 0
    m.diffuse_color=(1,1,1,1) if leaf else color
    m.use_backface_culling=not (leaf or 'Leaf' in key or 'Grass' in key)
    if leaf:
        v=m.node_tree.nodes.new('ShaderNodeVertexColor');v.layer_name='LeafTint';m.node_tree.links.new(v.outputs['Color'],node.inputs['Base Color'])
    return m

def export_merged(name,source,ratios,skip=None,leafmerge=False,provenance='original'):
    bpy.ops.object.select_all(action='DESELECT')
    coll=bpy.data.collections.new('WEB_TMP_'+name);bpy.context.scene.collection.children.link(coll)
    temporary=[];groups={};source_tris=sum(tri_count(o) for o in source)
    for original in source:
        if skip and skip(original):continue
        o=original.copy();o.data=original.data.copy();o.parent=None;o.matrix_world=original.matrix_world.copy();coll.objects.link(o);temporary.append(o)
        bpy.context.view_layer.objects.active=o;o.select_set(True)
        for mod in list(o.modifiers):
            try:bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception:pass
        ratio=ratios(o) if callable(ratios) else ratios
        if ratio<.999 and tri_count(o)>24:
            mod=o.modifiers.new('Web_LOD_Decimate','DECIMATE');mod.decimate_type='COLLAPSE';mod.ratio=max(.005,ratio);mod.use_collapse_triangulate=True
            try:bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception as e:print('DECIMATE_WARNING',o.name,e)
        o.select_set(False)
        for poly in o.data.polygons:
            if poly.area<1e-10:continue
            src=o.data.materials[poly.material_index] if len(o.data.materials)>poly.material_index else None
            matname=src.name if src else 'Default'
            isleaf=leafmerge and matname.startswith('Coconut_Leaf')
            key='Palm_LeafColor' if isleaf else matname
            if key not in groups:groups[key]={'verts':[],'faces':[],'smooth':[],'colors':[],'map':{},'mat':clean_mat(src,key,isleaf),'leaf':isleaf}
            g=groups[key];face=[]
            for vi in poly.vertices:
                vk=(o.name,vi)
                if vk not in g['map']:
                    g['map'][vk]=len(g['verts']);g['verts'].append(tuple(o.matrix_world@o.data.vertices[vi].co))
                face.append(g['map'][vk])
            g['faces'].append(tuple(face));g['smooth'].append(poly.use_smooth)
            col=src.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value[:] if src and src.use_nodes else (.1,.3,.03,1)
            g['colors'].append(col)
    for o in temporary:bpy.data.objects.remove(o,do_unlink=True)
    root=bpy.data.objects.new(name,None);coll.objects.link(root);root.select_set(True)
    meshes=[]
    for key,g in groups.items():
        if not g['faces']:continue
        me=bpy.data.meshes.new(name+'_'+key);me.from_pydata(g['verts'],[],g['faces']);me.update()
        o=bpy.data.objects.new(name+'_'+key,me);coll.objects.link(o);o.parent=root;o.data.materials.append(g['mat']);o.select_set(True);meshes.append(o)
        for p,s in zip(me.polygons,g['smooth']):p.use_smooth=s
        if g['leaf']:
            attr=me.color_attributes.new(name='LeafTint',type='BYTE_COLOR',domain='CORNER')
            for p,col in zip(me.polygons,g['colors']):
                for li in p.loop_indices:attr.data[li].color=col
    bpy.context.view_layer.objects.active=root
    output=OUT/(name+'.glb')
    bpy.ops.export_scene.gltf(filepath=str(output),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_materials='EXPORT',export_normals=True,export_texcoords=True,export_cameras=False,export_lights=False)
    points=[Vector(v) for g in groups.values() for v in g['verts']]
    bounds={'min':[min(v[k] for v in points) for k in range(3)],'max':[max(v[k] for v in points) for k in range(3)]}
    data=output.read_bytes();length,kind=struct.unpack_from('<II',data,12);doc=json.loads(data[20:20+length])
    primitives=sum(len(m['primitives']) for m in doc.get('meshes',[]))
    triangles=sum(doc['accessors'][p['indices']]['count']//3 for m in doc.get('meshes',[]) for p in m['primitives'] if 'indices'in p)
    REPORT['assets'][name]={'file':name+'.glb','bytes':len(data),'triangles':triangles,'source_triangles':source_tris,'mesh_nodes':len(doc.get('meshes',[])),'draw_primitives':primitives,'materials':len(doc.get('materials',[])),'source_bounds_blender_m':bounds,'provenance':provenance,'sha256':hashlib.sha256(data).hexdigest()}
    if not STAGE_ONLY:shutil.copy2(output,PUBLIC/output.name)
    print('WEB_ASSET',name,triangles,'triangles',primitives,'draws',len(data),'bytes')
    for o in list(coll.objects):bpy.data.objects.remove(o,do_unlink=True)
    bpy.data.collections.remove(coll)

if '--course-only' in sys.argv or TERRAIN_ONLY:
    if (OUT/'environment_web_manifest.json').exists():
        old=json.loads((OUT/'environment_web_manifest.json').read_text());REPORT['assets']=old.get('assets',{})
else:
    bpy.ops.wm.open_mainfile(filepath=str(ENV));bpy.context.window.scene=bpy.data.scenes['Asset_Library']
    ENV_NAMES=['CoconutPalm_A','CoconutPalm_B','KeralaHouse','FishingBoat','RoadReflector','RoadSegment','BeachSandPatch','OceanPatch','TropicalGrass','SeaWallRock']
    def palm_ratio(o):
        n=o.name
        if 'FrondLeaflets' in n:return .16
        if 'FrondStem' in n:return .18
        if 'Trunk' in n:return .28
        if 'Coconut' in n:return .20
        return .5
    for name in ENV_NAMES:
        collection=bpy.data.collections[name];source=[o for o in collection.objects if o.type=='MESH']
        if name.startswith('CoconutPalm'):
            export_merged(name,source,palm_ratio,lambda o:'LeafScars' in o.name,True)
            export_merged(name+'_LOD1',source,lambda o:.035 if 'FrondLeaflets' in o.name else .12,lambda o:any(s in o.name for s in ('LeafScars','Coconut_','CrownSpear')),True)
        else:
            ratio={'KeralaHouse':.34,'FishingBoat':.44,'RoadReflector':.32,'RoadSegment':.55,'BeachSandPatch':.12,'OceanPatch':.15,'TropicalGrass':.5,'SeaWallRock':.45}[name]
            export_merged(name,source,ratio)
# Consume only own base course meshes, never embedded preview car or prop instances.
if COURSE.exists():
    bpy.ops.wm.open_mainfile(filepath=str(COURSE))
    groups={'Course_Road':[],'Course_Terrain':[],'Course_Water':[],'Course_Furniture':[]}
    for o in bpy.context.scene.objects:
        if o.type!='MESH':continue
        n=o.name
        if n.startswith(('Road_','CenterDash')):key='Course_Road'
        elif n.startswith(('Arabian_Sea','OSM_Water_','Surf')):key='Course_Water'
        elif n.startswith(('Coastal_Terrain','Beach','WetSand')):key='Course_Terrain'
        elif n.startswith(('Gate_','Bridge_','Flyover_')):key='Course_Furniture'
        else:continue
        groups[key].append(o)
    for name,source in groups.items():
        if TERRAIN_ONLY and name!='Course_Terrain':continue
        export_merged(name,source,1 if name!='Course_Furniture' else (lambda o:1 if o.name.startswith('Flyover_') else .42),provenance='OSM-derived + original artistic additions; ODbL attribution required')
    src=json.loads((ROOT/'assets/course/manifest.json').read_text())
    converted={k:v for k,v in src.items() if k not in ('prop_instances','checkpoints_m','course_meshes','axes','route_points_m')}
    converted.update({k:v for k,v in src.get('world',{}).items() if k in ['districts','transit_routes','collision_file','fictional_geography_notice']})
    converted['collision_file']=src.get('collision_file',src.get('world',{}).get('collision_file'))
    converted['axes']='Three.js X east, Y up, -Z north. Meters. glTF assets already converted.'
    converted['prop_instances']=[{**{k:v for k,v in p.items() if k not in ('location_m','yaw_deg')},'position':[p['location_m'][0],p['location_m'][2],-p['location_m'][1]],'yaw_rad':math.radians(p['yaw_deg'])} for p in src['prop_instances']]
    converted['checkpoints']=[[p[0],p[2],-p[1]] for p in src['checkpoints_m']]
    converted['route_points']=[[p[0],p[2],-p[1]] for p in src.get('route_points_m',[])]
    converted['course_meshes']=[{'name':n,'file':n+'.glb','collision':next((m['collision'] for m in src['course_meshes'] if m['name']==n),n!='Course_Water')} for n in groups]
    converted['coordinate_conversion_note']='Positions [x,y,z] Blender -> [x,z,-y] Three. Blender yaw around +Z -> same positive yaw around Three +Y. Base road is at Three y=.18 with the authored graded flyover in elevation_profile. Use route_points plus elevated_corridors and the authored furniture/infrastructure proxies for runtime physics.'
    (OUT/'course_runtime.json').write_text(json.dumps(converted,indent=2))
    if not STAGE_ONLY:shutil.copy2(OUT/'course_runtime.json',PUBLIC/'course_runtime.json')
REPORT['total_bytes']=sum(a['bytes'] for a in REPORT['assets'].values());REPORT['total_triangles']=sum(a['triangles'] for a in REPORT['assets'].values())
(OUT/'environment_web_manifest.json').write_text(json.dumps(REPORT,indent=2))
if not STAGE_ONLY:shutil.copy2(OUT/'environment_web_manifest.json',PUBLIC/'environment_web_manifest.json')
print('WEB_EXPORT_COMPLETE',len(REPORT['assets']),REPORT['total_bytes'])
