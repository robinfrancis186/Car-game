"""Generate native UE map/assets from Blender deliverables. Run ONLY inside UE editor.
Source-reviewed against UE 5.6 API, but engine execution is pending hardware/access.
Does not install software, authenticate, download assets or accept licenses.
"""
import json, math, os, re, hashlib
from pathlib import Path
import unreal
ROOT=Path(os.environ.get('MALABAR_ROOT',str(Path(__file__).resolve().parents[4])))
ASSETS=ROOT/'assets';COURSE=json.loads((ASSETS/'course/manifest.json').read_text());ENV=json.loads((ASSETS/'environment/manifest.json').read_text())
TOOLS=unreal.AssetToolsHelpers.get_asset_tools();LIB=unreal.EditorAssetLibrary
ACTORS=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LEVELS=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
MESH_EDITOR=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
REPORT={'status':'in_progress','warnings':[],'assets':[],'actors':0}
# Never discard an unrelated unsaved map when loading/regenerating this owned map.
if unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages():
    raise RuntimeError('Save/close all dirty maps before running the owned-course bootstrap.')
# UE 5.6 defaults can route FBX to Interchange, which ignores legacy FbxImportUI.
# This project deliberately pins the legacy importer for deterministic combine/pivot options.
unreal.SystemLibrary.execute_console_command(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(),'Interchange.FeatureFlags.Import.FBX false')
for folder in ['/Game/Vehicles','/Game/Environment','/Game/Course','/Game/Materials','/Game/Maps','/Game/Audio']:LIB.make_directory(folder)

def import_fbx(file,folder,name,collide=False):
    if not file.is_file():raise FileNotFoundError(file)
    task=unreal.AssetImportTask();task.filename=str(file);task.destination_path=folder;task.destination_name=name;task.automated=True;task.replace_existing=True;task.replace_existing_settings=True;task.save=True
    options=unreal.FbxImportUI();options.automated_import_should_detect_type=False;options.import_as_skeletal=False;options.import_animations=False;options.import_mesh=True
    options.mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH
    options.import_materials=True;options.import_textures=False;options.override_full_name=True
    data=options.static_mesh_import_data;data.combine_meshes=True;data.auto_generate_collision=False
    data.convert_scene=True;data.convert_scene_unit=True;data.force_front_x_axis=False
    data.transform_vertex_to_absolute=True;data.generate_lightmap_u_vs=False
    data.normal_import_method=unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
    task.options=options;task.factory=unreal.FbxFactory();TOOLS.import_asset_tasks([task])
    candidates=[unreal.load_asset(p) for p in task.imported_object_paths]
    meshes=[o for o in candidates if isinstance(o,unreal.StaticMesh)]
    if len(meshes)!=1:raise RuntimeError(f'Expected one combined static mesh from {file}, got {len(meshes)}')
    mesh=meshes[0]
    if not isinstance(mesh.get_editor_property('asset_import_data'),unreal.FbxStaticMeshImportData):
        raise RuntimeError('Legacy FBX importer was not used for '+name)
    desired=folder+'/'+name
    if mesh.get_path_name().split('.')[0]!=desired:
        if LIB.does_asset_exist(desired):raise RuntimeError('Conflicting existing asset '+desired)
        if not LIB.rename_loaded_asset(mesh,desired):raise RuntimeError('Could not rename '+desired)
    if collide:
        body=mesh.get_editor_property('body_setup')
        if body is None:raise RuntimeError('Missing body setup for '+name)
        body.set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    REPORT['assets'].append({'file':str(file.relative_to(ROOT)),'asset':desired,'complex_collision':collide})
    LIB.save_loaded_asset(mesh)
    return mesh

# Original material palette is intentionally rebuilt: Blender procedural nodes are not FBX shaders.
material_cache={}
materials=dict(ENV['materials']);materials.update(COURSE['materials'])
# Basic car palette; material names/values are sourced from Blender build, not Tesla assets.
car_palette=ASSETS/'car/materials.json'
if car_palette.exists():materials.update(json.loads(car_palette.read_text()))

def material_key(name):
    return re.sub(r'[^A-Za-z0-9_]', '_', str(name))

def make_material(name,values):
    safe=material_key(name)[:80]+'_'+hashlib.sha1(name.encode()).hexdigest()[:6]
    path='/Game/Materials/'+safe
    if LIB.does_asset_exist(path):
        m=unreal.load_asset(path);unreal.MaterialEditingLibrary.delete_all_material_expressions(m)
    else:
        m=TOOLS.create_asset(safe,'/Game/Materials',unreal.Material,unreal.MaterialFactoryNew())
    if not m:raise RuntimeError('Cannot create material '+name)
    two_sided=any(token in name.lower() for token in ['leaf','frond','grass','glass','water','ocean','foam'])
    m.set_editor_property('two_sided',two_sided)
    color=values.get('base_color',[.2,.2,.2,1])
    node=unreal.MaterialEditingLibrary.create_material_expression(m,unreal.MaterialExpressionConstant3Vector,-450,-100)
    node.set_editor_property('constant',unreal.LinearColor(*color[:3],1))
    unreal.MaterialEditingLibrary.connect_material_property(node,'',unreal.MaterialProperty.MP_BASE_COLOR)
    for field,pin,y in [('roughness',unreal.MaterialProperty.MP_ROUGHNESS,70),('metallic',unreal.MaterialProperty.MP_METALLIC,150)]:
        n=unreal.MaterialEditingLibrary.create_material_expression(m,unreal.MaterialExpressionConstant,-250,y);n.set_editor_property('r',float(values.get(field,.5 if field=='roughness' else 0)))
        unreal.MaterialEditingLibrary.connect_material_property(n,'',pin)
    if 'glass' in name.lower():
        m.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT)
        opacity=unreal.MaterialEditingLibrary.create_material_expression(m,unreal.MaterialExpressionConstant,-250,230)
        opacity.set_editor_property('r',.18)
        unreal.MaterialEditingLibrary.connect_material_property(opacity,'',unreal.MaterialProperty.MP_OPACITY)
        REPORT['warnings'].append(name+': translucent .18-opacity glass; validate cockpit visibility/reflections in UE')
    unreal.MaterialEditingLibrary.recompile_material(m);LIB.save_loaded_asset(m);return m

def palette(mesh):
    for i,slot in enumerate(mesh.get_editor_property('static_materials')):
        name=str(slot.get_editor_property('imported_material_slot_name'))
        match=next((key for key in materials if material_key(key)==material_key(name)), None)
        if match is not None:
            if match not in material_cache:material_cache[match]=make_material(match,materials[match])
            mesh.set_material(i,material_cache[match])
        else:
            REPORT['warnings'].append(f'Unmatched material slot {mesh.get_name()}[{i}]: {name}; imported fallback retained')
    LIB.save_loaded_asset(mesh)

def place(mesh,label,xyz=(0,0,0),yaw=0,scale=1,collision=True):
    # Blender right-handed East/North/Up -> Unreal left-handed X/-Y/Z.
    x,y,z=xyz
    a=ACTORS.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(x*100,-y*100,z*100),unreal.Rotator(0,-yaw,0))
    if not a:raise RuntimeError('Failed spawning '+label)
    a.set_actor_label(label);c=a.static_mesh_component;c.set_static_mesh(mesh)
    c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS if collision else unreal.CollisionEnabled.NO_COLLISION)
    c.set_collision_profile_name('BlockAll' if collision else 'NoCollision')
    a.set_actor_scale3d(unreal.Vector(scale,scale,scale));REPORT['actors']+=1;return a

# Explicit components preserve independent steering and rolling axes.
car_files={'CarBody':'SM_CarBody.fbx','Wheel_FL':'SM_Wheel_Front_Left.fbx','Wheel_FR':'SM_Wheel_Front_Right.fbx','Wheel_RL':'SM_Wheel_Rear_Left.fbx','Wheel_RR':'SM_Wheel_Rear_Right.fbx'}
car_meshes={}
for name,file in car_files.items():car_meshes[name]=import_fbx(ASSETS/'car'/file,'/Game/Vehicles',name);palette(car_meshes[name])
# Fail loudly if scale/axis is wrong rather than generating a plausible but broken map.
bounds=car_meshes['CarBody'].get_bounding_box();extent=bounds.max-bounds.min
if not(400<extent.x<520 and 150<extent.y<250 and 70<extent.z<180):
    raise RuntimeError(f'Car import axis/scale mismatch, cm bounds={extent}. Verify FBX front axis in UE before continuing.')
props={}
for name,data in ENV['assets'].items():
    if name in {'RoadSegment','BeachSandPatch','OceanPatch'}:continue
    props[name]=import_fbx(ASSETS/'environment'/data['fbx'],'/Game/Environment',name,collide=name in {'KeralaHouse','SeaWallRock','FishingBoat'})
    palette(props[name])
course_meshes={}
for data in COURSE['course_meshes']:
    course_meshes[data['name']]=import_fbx(ASSETS/'course'/data['file'],'/Game/Course',data['name'],data['collision']);palette(course_meshes[data['name']])
# Only regenerate the explicitly owned map after validating all imports.
map_path='/Game/Maps/KappilCoast'
if LIB.does_asset_exist(map_path):
    if not LEVELS.load_level(map_path):raise RuntimeError('Could not load owned course map')
    for existing in ACTORS.get_all_level_actors():
        if str(existing.get_class().get_name()) not in {'WorldSettings','Brush'}:ACTORS.destroy_actor(existing)
else:
    if not LEVELS.new_level(map_path):raise RuntimeError('Could not create owned KappilCoast map')
for data in COURSE['course_meshes']:place(course_meshes[data['name']],data['name'],collision=data['collision'])
for i,p in enumerate(COURSE['prop_instances']):
    place(props[p['asset']],f"{p['asset']}_{i:04}",p['location_m'],p['yaw_deg'],p['scale'],p['asset'] in {'KeralaHouse','SeaWallRock','FishingBoat'})
# Build the checkpoint director and start transform from the same manifest as rendered gates.
cls=unreal.load_class(None,'/Script/KeralaRacing.CoastalRaceDirector')
if cls is None:raise RuntimeError('Compile KeralaRacingEditor module before bootstrapping')
director=ACTORS.spawn_actor_from_class(cls,unreal.Vector())
checkpoints=[unreal.Vector(p[0]*100,-p[1]*100,p[2]*100) for p in COURSE['checkpoints_m']]
director.set_editor_property('checkpoints',checkpoints);director.set_actor_label('Kappil_TimeTrial_Director')
p0,p1=checkpoints[:2];yaw=math.degrees(math.atan2(p1.y-p0.y,p1.x-p0.x))
ACTORS.spawn_actor_from_class(unreal.PlayerStart,p0+unreal.Vector(0,0,75),unreal.Rotator(0,yaw,0))
# Dynamic lighting, explicit exposure, coastal haze. These need GPU look-development validation.
sun=ACTORS.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,1000),unreal.Rotator(-28,-135,0))
sun.light_component.set_editor_property('intensity',4.0);sun.light_component.set_editor_property('light_color',unreal.Color(255,231,192,255))
sun.light_component.set_editor_property('atmosphere_sun_light',True)
ACTORS.spawn_actor_from_class(unreal.SkyAtmosphere,unreal.Vector())
sky=ACTORS.spawn_actor_from_class(unreal.SkyLight,unreal.Vector(0,0,500));sky.light_component.set_editor_property('intensity',.8);sky.light_component.set_editor_property('real_time_capture',True)
ACTORS.spawn_actor_from_class(unreal.ExponentialHeightFog,unreal.Vector(0,0,-100))
# Import original synthesized audio; not a recorded Tesla motor.
for name in ['EV_Loop','Coastal_Ambience']:
    file=ASSETS/'audio'/(name+'.wav')
    task=unreal.AssetImportTask();task.filename=str(file);task.destination_path='/Game/Audio';task.destination_name=name;task.automated=True;task.replace_existing=True;task.replace_existing_settings=True;task.save=True;TOOLS.import_asset_tasks([task])
    sound=unreal.load_asset('/Game/Audio/'+name)
    if not sound:raise RuntimeError('Audio import failed: '+name)
    sound.set_editor_property('looping',True);LIB.save_loaded_asset(sound)
    if name=='Coastal_Ambience':
        ambient=ACTORS.spawn_actor_from_class(unreal.AmbientSound,unreal.Vector());ambient.audio_component.set_sound(sound);ambient.audio_component.set_volume_multiplier(.18);ambient.audio_component.set_editor_property('auto_activate',True)
if not LEVELS.save_current_level():raise RuntimeError('Map save failed')
LIB.save_directory('/Game',only_if_is_dirty=True,recursive=True)
REPORT['status']='content_generated_NOT_playtested'
REPORT['warnings'].append('Verify car front +X, wheel axle Y, scale, route/checkpoint alignment, material appearance and collision in PIE before packaging.')
(ROOT/'logs/unreal_bootstrap_report.json').write_text(json.dumps(REPORT,indent=2))
unreal.log('MALABAR: generated content. Run the manual acceptance checklist; this log is not gameplay verification.')
