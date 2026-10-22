import bpy
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];D=R/'assets/infrastructure/vehicles'
# Organize editable source into separate named collections and non-overlapping layout.
bpy.ops.wm.open_mainfile(filepath=str(D/'transit_vehicles.blend'))
for name in ('CoastMetroTrain','WaterTransitFerry'):
 root=bpy.data.objects[name];co=bpy.data.collections.new(name+' editable parts');bpy.context.scene.collection.children.link(co)
 for o in [root]+list(root.children_recursive):
  for c in list(o.users_collection):c.objects.unlink(o)
  co.objects.link(o)
bpy.data.objects['WaterTransitFerry'].location.y=18
bpy.ops.wm.save_as_mainfile(filepath=str(D/'transit_vehicles.blend'))
# Only presentation lighting changes. Actual exported geometry is unchanged.
bpy.ops.wm.open_mainfile(filepath=str(D/'coast_metro_train_preview.blend'))
bpy.data.objects['Cab soft fill'].data.energy=0
sc=bpy.context.scene;sc.render.filepath=str(D/'coast_metro_train_preview_front.png');bpy.ops.render.render(write_still=True)
cam=sc.camera;cam.location=(37,-19,11);cam.data.ortho_scale=25;cam.rotation_euler=(Vector((20,0,2))-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(D/'coast_metro_train_preview_cab.png');bpy.ops.render.render(write_still=True)
print('TRANSIT_FINAL_PREVIEWS_READY')
