"""Original 2017 Roadster-inspired fan concept. Run: blender -b --python build_car.py
Meters; +X forward, +Y left, +Z up. No downloaded geometry/textures.
"""
import bpy, bmesh, math, json, os, random
from mathutils import Vector
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'assets'/'car'; OUT.mkdir(parents=True, exist_ok=True)
random.seed(24)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for d in bpy.data.materials: bpy.data.materials.remove(d)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1.0

def mat(name, color, metallic=0, rough=.35, emission=None, transmission=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metallic; p.inputs['Roughness'].default_value=rough
    if transmission: p.inputs['Transmission Weight'].default_value=transmission; p.inputs['IOR'].default_value=1.47
    if emission: p.inputs['Emission Color'].default_value=(*color,1); p.inputs['Emission Strength'].default_value=emission
    return m
paint=mat('Crimson multi-coat | original fan concept',(.42,.008,.019),.7,.22)
p=paint.node_tree.nodes.get('Principled BSDF'); p.inputs['Coat Weight'].default_value=.55; p.inputs['Coat Roughness'].default_value=.13
black=mat('Carbon satin',(.012,.015,.019),.36,.3)
rubber=mat('Tire rubber',(.011,.014,.018),0,.7)
glass=mat('Smoked panoramic glass',(.009,.017,.02),.1,.12,transmission=.28)
alloy=mat('Machined graphite aluminum',(.16,.19,.22),.92,.19)
chrome=mat('Diamond cut rim edges',(.62,.67,.72),1,.19)
brake=mat('Carbon ceramic rotor',(.14,.145,.15),.65,.5)
red=mat('Brake caliper red',(.6,.012,.008),.4,.3)
white=mat('LED ice white',(.7,.91,1),.25,.17,emission=5)
tail=mat('LED ruby red',(.8,.007,.018),.15,.18,emission=4)
leather=mat('Graphite leather',(.035,.04,.047),0,.62)
seam=mat('Warm contrast stitching',(.38,.37,.34),0,.72)
screen=mat('Cockpit black display',(.012,.028,.038),.3,.18,emission=.4)
cyan=mat('Display cyan',(.06,.58,.75),.25,.25,emission=2)
body_parts=[]; wheels={}
root=bpy.data.objects.new('CAR_ROOT',None); bpy.context.collection.objects.link(root)
root['concept']='Original fan-made Roadster-inspired sports car; not Tesla CAD, no affiliation.'
root['fictional_mechanic']='Hidden thruster housings are speculative gameplay hardware, not a production feature.'

def finish(o,name,material,parent=root,smooth=True,body=True):
    o.name=name
    if material:o.data.materials.append(material)
    if smooth and o.type=='MESH':
        for p in o.data.polygons:p.use_smooth=True
    if parent:
        bpy.context.view_layer.update(); mw=o.matrix_world.copy(); o.parent=parent; o.matrix_parent_inverse=parent.matrix_world.inverted(); o.matrix_basis=mw
    if body:body_parts.append(o)
    return o

def mesh(name,vs,fs,material,parent=root,body=True):
    fixed_facing=(name.startswith(('Glass_Side_','A_Pillar_')) and name.endswith('_1')) or (name.startswith('Rear_Buttress_') and name.endswith('_-1'))
    if fixed_facing:fs=[tuple(reversed(f)) for f in fs]
    d=bpy.data.meshes.new(name); d.from_pydata(vs,[],fs); d.update()
    o=bpy.data.objects.new(name,d); bpy.context.collection.objects.link(o)
    res=finish(o,name,material,parent,body=body)
    if fixed_facing:res['outward_normal_fix']=True
    return res

def bevel(o,width=.02,segments=3):
    m=o.modifiers.new('Soft manufactured edges','BEVEL'); m.width=width; m.segments=segments
    return o

def cube(name,loc,scale,material,bev=.02,parent=root,body=True):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    finish(o,name,material,parent,body=body)
    if bev:bevel(o,bev,3)
    return o

def cyl(name,loc,radius,depth,material,rotation=(math.pi/2,0,0),vertices=64,parent=root,body=True):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc,rotation=rotation)
    o=bpy.context.object; finish(o,name,material,parent,body=body); bevel(o,.003,2); return o

def torus(name,loc,major,minor,material,parent=root,body=True):
    bpy.ops.mesh.primitive_torus_add(major_segments=80,minor_segments=14,location=loc,rotation=(math.pi/2,0,0),major_radius=major,minor_radius=minor)
    return finish(bpy.context.object,name,material,parent,body=body)

def project_shell(co,axis,offset=.003):
    v=Vector(co); start=v.copy(); direction=Vector((0,0,0))
    if axis=='top':start.z=3;direction.z=-1
    elif axis=='front':start.x=3;direction.x=-1
    elif axis=='rear':start.x=-3;direction.x=1
    else:start.y=3*(1 if v.y>0 else -1);direction.y=-1 if v.y>0 else 1
    found,hit,normal,_=globals()['body'].ray_cast(start,direction)
    return tuple(hit+normal*offset) if found else co

def curve(name,coords,radius,material,parent=root,body=True,cyclic=False):
    if name.startswith(('Hood_Shutline','Rear_Deck_Seam','Headlamp_')):
        coords=[project_shell(p,'top',.003 if 'LED' not in name else .024) for p in coords]
    elif name.startswith('Door_Seam'):
        coords=[project_shell(p,'side',.002) for p in coords]
    elif name.startswith('Front_Lower_Intake'):
        coords=[project_shell(p,'front',.007) for p in coords]
    elif name.startswith('Tail_Light'):
        coords=[project_shell(p,'rear',.004 if 'LED' not in name else .030) for p in coords]
    d=bpy.data.curves.new(name,'CURVE'); d.dimensions='3D'; d.resolution_u=12
    s=d.splines.new('BEZIER'); s.bezier_points.add(len(coords)-1)
    for p,co in zip(s.bezier_points,coords):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    s.use_cyclic_u=cyclic; d.bevel_depth=radius;d.bevel_resolution=3;d.use_fill_caps=True
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);finish(o,name,material,parent,body=body);return o

def surf(name,rows,material,thickness=.008,subdiv=2):
    vs=[p for row in rows for p in row]; n=len(rows[0]);fs=[]
    for i in range(len(rows)-1):
        for j in range(n-1):a=i*n+j;fs.append((a,a+1,a+n+1,a+n))
    o=mesh(name,vs,fs,material)
    if subdiv:
        m=o.modifiers.new('Curved surface','SUBSURF');m.levels=subdiv;m.render_levels=subdiv
    if thickness:m=o.modifiers.new('Panel thickness','SOLIDIFY');m.thickness=thickness
    return o

# Smooth longitudinal monocoque loft: curved hood, broad rear shoulders and low nose.
sections=[(-2.23,.70,.55),(-2.12,.87,.68),(-1.85,1.03,.80),(-1.35,1.08,.84),(-.85,.955,.83),(-.3,.91,.76),(.3,.92,.77),(.82,.965,.78),(1.35,1.08,.77),(1.85,1.00,.70),(2.14,.83,.59),(2.25,.62,.48)]
# Closed ring shape around each station. Top crowned, waist taut, bottom tucked.
ring=[(0,1),(.45,.995),(.79,.965),(.96,.87),(1,.65),(.99,.35),(.91,0),(.6,-.04),(0,-.04),(-.6,-.04),(-.91,0),(-.99,.35),(-1,.65),(-.96,.87),(-.79,.965),(-.45,.995)]
vs=[]
for x,w,z in sections:
    for yf,zf in ring:
        shoulder=max(.195*math.exp(-((x-1.35)/.63)**2),.115*math.exp(-((x+1.35)/.63)**2))*abs(yf)**2*max(0,zf)
        flank=1-.075*math.exp(-(x/.88)**4) if abs(zf-.35)<.01 else (1+.025*math.exp(-(x/.88)**4) if abs(zf)<.01 else 1)
        vs.append((x,w*yf*flank,.255+(z-.255)*zf+shoulder))
fs=[];n=len(ring)
for i in range(len(sections)-1):
    for j in range(n):a=i*n+j;b=i*n+(j+1)%n;fs.append((a,b,b+n,a+n))
fs += [tuple(reversed(range(n))),tuple(range((len(sections)-1)*n,len(sections)*n))]
body=mesh('Body_SculptedShell',vs,fs,paint)
bm=bmesh.new();bm.from_mesh(body.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free()
sub=body.modifiers.new('Continuous sculpted body','SUBSURF');sub.levels=3;sub.render_levels=3
bpy.context.view_layer.objects.active=body;bpy.ops.object.modifier_apply(modifier=sub.name)
# Cut all four open wheel arches into actual geometry.
for x,label in [(1.35,'F'),(-1.35,'R')]:
    for sign,side in [(1,'L'),(-1,'R')]:
        bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=.391,depth=.72,location=(x,sign*.98,.368),rotation=(math.pi/2,0,0))
        cut=bpy.context.object;mod=body.modifiers.new('Wheel arch '+label+side,'BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut;mod.solver='EXACT'
        bpy.context.view_layer.objects.active=body;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
# Open the cockpit beneath the glass so the seats, RHD wheel and console are truly visible.
bpy.ops.mesh.primitive_cube_add(size=1,location=(-.18,0,1.0));cut=bpy.context.object;cut.scale=(1.58,1.29,1.10)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
bevel(cut,.13,5);bpy.context.view_layer.objects.active=cut;bpy.ops.object.modifier_apply(modifier=cut.modifiers[0].name)
mod=body.modifiers.new('Real open cockpit','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut;mod.solver='EXACT'
bpy.context.view_layer.objects.active=body;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
bevel(body,.007,3)
cube('Cockpit_Floor',(-.18,0,.435),(1.55,1.27,.045),black,.05)
for side in [-1,1]:cube('Interior_Door_Card_'+str(side),(-.18,side*.66,.63),(1.42,.055,.30),leather,.045)
# Carbon undertray, aero splitter and sills.
undertray=cube('Undertray',(-.05,0,.255),(3.72,1.49,.08),black,.06)
# Four real clearance cutouts: the original rectangular tray touched front tires at full lock.
bpy.context.view_layer.objects.active=undertray
for mod in list(undertray.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
for wx in [-1.35,1.35]:
    for side in [-1,1]:
        bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=.425,depth=.95,location=(wx,side*.924,.368),rotation=(math.pi/2,0,0));cut=bpy.context.object
        mod=undertray.modifiers.new('Full-lock tire clearance','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut;mod.solver='EXACT'
        bpy.context.view_layer.objects.active=undertray;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)

# Swept front splitter loft
surf('Front_Splitter', [[(1.72,-.86,.26),(1.87,0,.24),(1.72,.86,.26)],[(2.20,-.83,.25),(2.30,0,.23),(2.20,.83,.25)]],black,.025,2)
for s in [-1,1]:
    curve('Carbon_SideSill_'+str(s),[(-.92,s*.91,.27),(-.3,s*.92,.245),(.45,s*.935,.245),(.92,s*.94,.28)],.024,black)
    # Side panel door outline and flush handle.
    curve('Door_Seam_'+str(s),[(-.96,s*.96,.71),(-.85,s*.935,.42),(-.65,s*.914,.32),(.45,s*.927,.32),(.69,s*.95,.43),(.72,s*.953,.70)],.0025,black)
    cube('Flush_Door_Handle_'+str(s),(-.55,s*.946,.738),(.16,.014,.025),alloy,.009)
    # Side camera / mirror stalk and streamlined housing.
    curve('Mirror_Stalk_'+str(s),[(.47,s*.74,.91),(.43,s*1.02,.91)],.016,black)
    mir=cube('Mirror_Housing_'+str(s),(.40,s*1.09,.932),(.24,.15,.09),paint,.042)
    cube('Mirror_Glass_'+str(s),(.32,s*1.104,.935),(.012,.12,.054),chrome,.02)
# Hood shut-lines and shoulder highlights.
for s in [-1,1]:
    curve('Hood_Shutline_'+str(s),[(.70,s*.65,.774),(1.16,s*.65,.758),(1.68,s*.61,.711),(2.00,s*.46,.634)],.0035,black)
    curve('Rear_Deck_Seam_'+str(s),[(-1.02,s*.69,.828),(-1.60,s*.72,.813),(-1.96,s*.63,.729)],.0035,black)
# Parametric greenhouse with shared boundaries, not shrinking subdivided slabs.
# Every lower glass boundary follows the actual shell; all glass interfaces share vertices in space.
def bottom_front(u):
    x=.68-.03*(1-u*u); y=.70*u
    return Vector(project_shell((x,y,.8),'top',.005))
def top_front(u):return Vector((.02-.015*(1-u*u),.59*u,1.15+.018*(1-u*u)))
def roof_point(t,u):return Vector((.02-.69*t-.015*(1-u*u),(.59+.04*t)*u,1.15+.060*math.sin(math.pi*t)+.018*(1-u*u)))
def bottom_rear(u):
    x=-1.02-.02*(1-u*u);y=.74*u
    return Vector(project_shell((x,y,.82),'top',.005))
wind=[]
for i in range(17):
    t=i/16;row=[]
    for j in range(25):
        u=j/12-1;p=bottom_front(u).lerp(top_front(u),t);p.x-=.025*math.sin(math.pi*t)*(1-u*u);row.append(tuple(p))
    wind.append(row)
surf('Glass_Windshield',wind,glass,.003,0)
roof=[[tuple(roof_point(i/20,j/12-1)) for j in range(25)] for i in range(21)]
surf('Glass_Targa_Roof',roof,glass,.003,0)
rear=[]
for i in range(13):
    t=i/12;rear.append([tuple(roof_point(1,j/12-1).lerp(bottom_rear(j/12-1),t)) for j in range(25)])
surf('Glass_Rear',rear,glass,.003,0)
for sign in [-1,1]:
    def side_bottom(t):
        x=.68-1.70*t;y=sign*(.70+.10*math.sin(math.pi*t)+.04*t)
        return Vector(project_shell((x,y,.8),'top',.006))
    rows=[]
    for i in range(25):
        t=i/24;lo=side_bottom(t);hi=roof_point(t,sign);row=[]
        for j in range(9):
            v=j/8;p=lo.lerp(hi,v);p.y+=sign*.008*math.sin(math.pi*v);row.append(tuple(p))
        rows.append(row)
    surf('Glass_Side_'+str(sign),rows,glass,.003,0)
    front=[tuple(bottom_front(sign).lerp(top_front(sign),i/12)) for i in range(13)]
    upper=[tuple(roof_point(i/24,sign)) for i in range(25)]
    back=[tuple(roof_point(1,sign).lerp(bottom_rear(sign),i/12)) for i in range(13)]
    lower=[tuple(side_bottom(i/24)) for i in range(25)]
    # Thin integrated pillar ribbons. Flat surfaces avoid an external tubular rollcage appearance.
    rows=[]
    for p0 in front:
        p=Vector(p0);rows.append([tuple(p+Vector((-.014,sign*.007,0))),tuple(p+Vector((.014,sign*.007,0)))])
    surf('A_Pillar_'+str(sign),rows,paint,.004,0)
    rows=[]
    for p0 in back:
        p=Vector(p0);rows.append([tuple(p+Vector((-.018,sign*.007,0))),tuple(p+Vector((.018,sign*.007,0)))])
    surf('Rear_Buttress_'+str(sign),rows,paint,.004,0)
    curve('Roof_Rail_'+str(sign),upper,.008,black)
    curve('Window_Lower_Belt_'+str(sign),lower,.006,paint)
    curve('Window_Front_Seal_'+str(sign),front,.004,black)
    curve('Window_Rear_Seal_'+str(sign),back,.004,black)
# Contoured bucket seats: shaped shells, sculpted pads, shoulder wings and real harness apertures.
alcantara=mat('Seat center microsuede',(.019,.022,.026),0,.88)
display_white=mat('Instrument soft white',(.55,.72,.78),0,.5,emission=.8)
def seat_width(t):
    return .19+.057*math.sin(math.pi*min(t/.88,1))-.065*max(0,(t-.73)/.27)
def seat_back(t,v,sy,offset=0):
    return (-.56-.21*t+.10*abs(v)**2*(.2+.8*math.sin(math.pi*t))+offset,sy+seat_width(t)*v,.49+.62*t)
def apply_all(o):
    bpy.context.view_layer.objects.active=o
    for m in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=m.name)
for side in [-1,1]:
    sy=side*.36;tag=str(side)
    base=surf('Seat_BaseShell_'+tag, [[(.05-.63*t,sy+.224*v,.455+.085*abs(v)**4+.025*math.sin(math.pi*t)) for v in [-1+j/10 for j in range(21)]] for t in [i/20 for i in range(21)]],black,.018,0)
    surf('Seat_BasePad_'+tag, [[(.025-.56*t,sy+.175*v,.478+.018*math.sin(math.pi*t)+.018*abs(v)**3) for v in [-1+j/8 for j in range(17)]] for t in [i/20 for i in range(21)]],alcantara,.018,0)
    for edge in [-1,1]:
        surf('Seat_ThighBolster_'+tag+'_'+str(edge), [[(.02-.58*t,sy+edge*(.16+.067*u),.49+.067*math.sin(math.pi*u)+.025*math.sin(math.pi*t)) for u in [j/8 for j in range(9)]] for t in [i/16 for i in range(17)]],leather,.015,0)
    shell=surf('Seat_BackShell_'+tag, [[seat_back(t,v,sy) for v in [-1+j/12 for j in range(25)]] for t in [i/28 for i in range(29)]],black,.018,0)
    pad=surf('Seat_BackPad_'+tag, [[seat_back(t,.66*v,sy,.026+.013*(1-v*v)) for v in [-1+j/10 for j in range(21)]] for t in [.045+i*.915/28 for i in range(29)]],alcantara,.018,0)
    for edge in [-1,1]:
        surf('Seat_ShoulderBolster_'+tag+'_'+str(edge), [[seat_back(t,edge*(.66+.33*u),sy,.018+.055*math.sin(math.pi*u)*math.sin(math.pi*t)) for u in [j/8 for j in range(9)]] for t in [.07+i*.75/24 for i in range(25)]],leather,.021,0)
        curve('Seat_Stitch_Back_'+tag+'_'+str(edge),[seat_back(t,edge*.64,sy,.046) for t in [.09+i*.84/18 for i in range(19)]],.0012,seam)
        curve('Seat_Stitch_Base_'+tag+'_'+str(edge),[(.005-.53*t,sy+edge*.17,.488+.018*math.sin(math.pi*t)+.018) for t in [i/14 for i in range(15)]],.0012,seam)
    # Rounded twin harness slots really pass through both the shell and center upholstery.
    for ob in [shell,pad]:apply_all(ob)
    for offset in [-.075,.075]:
        bpy.ops.mesh.primitive_cube_add(size=1,location=(-.70,sy+offset,.958));cut=bpy.context.object;cut.scale=(.22,.050,.028);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);bevel(cut,.010,3);apply_all(cut)
        for ob in [shell,pad]:
            mod=ob.modifiers.new('Harness through-slot','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut;mod.solver='EXACT';bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(cut,do_unlink=True)
    for ob in [shell,pad]:
        bm=bmesh.new();bm.from_mesh(ob.data)
        for edge in bm.edges:
            if len(edge.link_faces)==2 and edge.calc_face_angle()>.70:edge.smooth=False
        bm.to_mesh(ob.data);bm.free()
# Sculpted dashboard with a curved top, separate instrument pod and continuous vent band.
ys=[-.64+i*.08 for i in range(17)]
surf('Dashboard_Top', [[(.53-.29*t,y,.785+.035*math.sin(math.pi*t)-.017*abs(y/.64)**2) for y in ys] for t in [i/8 for i in range(9)]],leather,.025,0)
surf('Dashboard_Face', [[(.24+.025*t,y,.79-.10*t-.017*abs(y/.64)**2) for y in ys] for t in [i/5 for i in range(6)]],black,.02,0)
curve('Dashboard_Seam',[(.232,y,.792-.017*abs(y/.64)**2) for y in ys],.0015,seam)
for side in [-1,1]:
    cube('Dashboard_Vent_'+str(side),(.218,side*.52,.758),(.016,.17,.047),rubber,.01)
    for j in range(4):cube('Dashboard_VentFin_'+str(side)+'_'+str(j),(.205,side*.52,.744+j*.009),(.008,.15,.003),alloy,.001)
    curve('Interior_Door_Pull_'+str(side),[(-.22,side*.63,.72),(-.10,side*.61,.75),(.03,side*.63,.74)],.012,black)
# Center console with genuine cup recesses, not raised markers.
console=cube('Center_Console',(-.1,0,.57),(.9,.20,.26),black,.045);apply_all(console)
for x in [-.33,-.12]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=40,radius=.046,depth=.12,location=(x,0,.70));cut=bpy.context.object;mod=console.modifiers.new('Cup recess','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut;bpy.context.view_layer.objects.active=console;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
    bpy.ops.mesh.primitive_torus_add(major_segments=48,minor_segments=8,major_radius=.047,minor_radius=.0025,location=(x,0,.702));finish(bpy.context.object,'Interior_Cup_Rim_'+str(x),alloy)
for face in console.data.polygons:face.use_smooth=False
# Physical screens and original vector interface. Static parked-state graphics, not live game telemetry.
cube('Display_Cluster_Housing',(.278,-.38,.872),(.08,.34,.13),black,.024)
cube('Display_Cluster_Face',(.236,-.38,.872),(.003,.302,.096),screen,.012)
cube('Display_Main_Housing',(.205,.055,.726),(.028,.39,.238),black,.013)
cube('Display_Main_Face',(.188,.055,.726),(.003,.353,.202),screen,.008)
from mathutils import Matrix
text_orientation=Matrix(((0,0,-1),(-1,0,0),(0,1,0))).to_euler()
def label(name,words,loc,size,material=display_white):
    font=bpy.data.curves.new(name,'FONT');font.body=words;font.align_x='CENTER';font.align_y='CENTER';font.size=size;font.extrude=.00015;font.resolution_u=5
    ob=bpy.data.objects.new(name,font);bpy.context.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=text_orientation;finish(ob,name,material);return ob
label('Display_Text_Speed','000',(.232,-.38,.883),.054)
label('Display_Text_Units','km/h',(.232,-.38,.851),.016)
label('Display_Text_Ready','READY',(.232,-.485,.883),.014,cyan)
label('Display_Text_Charge','92%',(.232,-.276,.883),.017,cyan)
label('Display_Text_Map_Title','COASTAL ROUTE',(.184,.055,.807),.016)
label('Display_Text_Map_ETA','ARRIVAL 03:24',(.184,.055,.644),.012)
for i in range(4):
    curve('Display_Grid_StreetH_'+str(i),[(.184,-.10,.665+i*.037),(.184,.205,.665+i*.037)],.00065,display_white)
    curve('Display_Grid_StreetV_'+str(i),[(.184,-.08+i*.085,.66),(.184,-.08+i*.085,.788)],.00065,display_white)
curve('Display_Map_Route',[(.180,.15,.673),(.180,.085,.696),(.180,.085,.745),(.180,.015,.763),(.180,-.065,.785)],.0027,cyan)
mesh('Display_Map_Position',[(.177,.15,.678),(.177,.159,.666),(.177,.141,.666)],[(0,1,2)],white)
# Right-hand-drive steering column and independently animated hand wheel in the editable source.
column=cyl('Steering_Column',(.25,-.38,.827),.027,.20,black,rotation=(0,math.pi/2,0))
hand_pivot=bpy.data.objects.new('Interior_Steering_Pivot',None);bpy.context.collection.objects.link(hand_pivot);hand_pivot.parent=root;hand_pivot.location=(.16,-.38,.827)
bpy.ops.mesh.primitive_torus_add(major_segments=64,minor_segments=12,major_radius=.137,minor_radius=.016,location=(.16,-.38,.827),rotation=(0,math.pi/2,0));finish(bpy.context.object,'Steering_Wheel_RHD',leather,hand_pivot)
cube('Steering_Hub',(.16,-.38,.827),(.05,.115,.065),black,.018,hand_pivot)
for side in [-1,1]:curve('Steering_Spoke_'+str(side),[(.16,-.38,.827),(.16,-.38+side*.12,.854)],.014,alloy,hand_pivot)
curve('Steering_Lower_Spoke',[(.16,-.38,.805),(.16,-.38,.697)],.015,black,hand_pivot)
for f,a in [(1,0),(31,.4),(61,0),(91,-.4),(121,0)]:hand_pivot.rotation_euler.x=a*3.2;hand_pivot.keyframe_insert(data_path='rotation_euler',frame=f)

# Front bumper intakes and slim swept LED signatures.
for s in [-1,1]:
    # User-reference-inspired triangular inset lamp, not a curved bumper moustache.
    a=Vector((1.64,s*.89,0));b=Vector((2.09,s*.78,0));c=Vector((2.05,s*.59,0));N=12;vs=[];ix={};fs=[]
    for i in range(N+1):
        for j in range(N+1-i):
            p=a*(1-i/N-j/N)+b*(i/N)+c*(j/N);ix[i,j]=len(vs);vs.append(project_shell(p,'top',.005))
    for i in range(N):
        for j in range(N-i):
            fs.append((ix[i,j],ix[i+1,j],ix[i,j+1]))
            if j<N-i-1:fs.append((ix[i+1,j],ix[i+1,j+1],ix[i,j+1]))
    if s==1:fs=[tuple(reversed(f)) for f in fs]
    mesh('Headlamp_Inset_'+str(s),vs,fs,black)
    sig=[project_shell((2.09-.04*t,s*(.78-.19*t),0),'top',.013) for t in [.08,.3,.55,.82]]
    curve('LampSignature_'+str(s),sig,.005,white)
    for i,(xx,yy) in enumerate([(1.88,.80),(1.94,.73),(1.995,.65)]):
        pt=project_shell((xx,s*yy,0),'top',.014)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=1,location=pt);o=bpy.context.object;o.scale=(.027,.019,.008)
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);finish(o,'Projector_LED_'+str(s)+'_'+str(i),white)
    # Compact front-haunch outlet follows the concave flank, as in the supplied red reference.
    pts=[project_shell((.98,s*.98,.735),'side',.004),project_shell((.77,s*.98,.70),'side',.004),project_shell((.84,s*.98,.65),'side',.004)]
    mesh('Front_Haunch_Vent_'+str(s),pts,[(2,1,0) if s>0 else (0,1,2)],black)
    # lower brake-cooling intakes
    cube('Front_Corner_Intake_'+str(s),(2.128,s*.59,.375),(.06,.22,.105),black,.045)
    for k in range(3):cube('Intake_Fin_'+str(s)+'_'+str(k),(2.165,s*.59,.35+k*.025),(.015,.17,.007),alloy,.003)
surf('Front_Lower_Intake',[[project_shell((2.3,y,z+.02*abs(y)/.8),'front',.004) for y in [-.8+i*.05 for i in range(33)]] for z in [.33,.40]],rubber,.002,0)
# Tail light band, rear diffuser and deployable spoiler aesthetic.
curve('Tail_Light_Housing',[(-2.132,-.74,.655),(-2.21,-.42,.608),(-2.234,0,.593),(-2.21,.42,.608),(-2.132,.74,.655)],.025,black)
curve('Tail_Light_LED',[(-2.143,-.74,.657),(-2.22,-.42,.611),(-2.244,0,.596),(-2.22,.42,.611),(-2.143,.74,.657)],.009,tail)
for s in [-1,1]:
    curve('Tail_Light_Sweep_'+str(s),[(-2.14,s*.74,.658),(-1.94,s*.86,.714)],.011,tail)
surf('Rear_Deck_Spoiler',[[(-1.92,-.80,.765),(-2.02,0,.716),(-1.92,.80,.765)],[(-2.03,-.81,.785),(-2.13,0,.739),(-2.03,.81,.785)]],paint,.018,2)
cube('Rear_Diffuser',(-2.09,0,.30),(.30,1.46,.16),black,.035)
for y in [-.61,-.32,0,.32,.61]:cube('Diffuser_Fin_'+str(y),(-2.05,y,.23),(.39,.018,.15),black,.01)
# Fictional retractable thruster outlets. Explicitly labelled in manifest/root, not real production equipment.
for s in [-1,1]:
    c=cyl('FICTIONAL_Thruster_Outer_'+str(s),(-2.145,s*.56,.415),.075,.055,alloy,rotation=(0,math.pi/2,0))
    c=cyl('FICTIONAL_Thruster_Dark_Core_'+str(s),(-2.18,s*.56,.415),.055,.014,black,rotation=(0,math.pi/2,0))
    c=cyl('FICTIONAL_Thruster_Aperture_'+str(s),(-2.19,s*.56,.415),.021,.015,cyan,rotation=(0,math.pi/2,0))
# All four fully articulated assemblies. Steer around local Z, spin around local Y.
for wx,axle in [(1.35,'Front'),(-1.35,'Rear')]:
  for sign,side in [(1,'Left'),(-1,'Right')]:
    key=axle+'_'+side; center=(wx,sign*.924,.368)
    pivot=bpy.data.objects.new('Steer_'+key,None);bpy.context.collection.objects.link(pivot);pivot.parent=root;pivot.location=center;pivot.empty_display_size=.14
    spin=bpy.data.objects.new('Spin_'+key,None);bpy.context.collection.objects.link(spin);spin.parent=pivot;spin.empty_display_size=.12
    parts=[]
    def add(o):parts.append(o);return o
    yout=center[1]+sign*.127
    # Radial tire section, true rounded shoulder across 25 cm width.
    profile=[(-.127,.267),(-.14,.286),(-.142,.322),(-.119,.353),(-.08,.363),(0,.366),(.08,.363),(.119,.353),(.142,.322),(.14,.286),(.127,.267)]
    verts=[];faces=[];radials=96
    for yo,r in profile:
      for i in range(radials):a=2*math.pi*i/radials;verts.append((wx+r*math.sin(a),center[1]+yo,.368+r*math.cos(a)))
    for j in range(len(profile)-1):
      for i in range(radials):a=j*radials+i;b=j*radials+(i+1)%radials;faces.append((a,b,b+radials,a+radials))
    add(mesh('Tire_'+key,verts,faces,rubber,spin,False))
    # Three recessed circumferential grooves and 36 discrete shoulder sipes each side.
    for gy in [-.074,0,.074]:add(torus('Tread_Groove_'+key+'_'+str(gy),(wx,center[1]+gy,.368),.365,.0022,black,spin,False))
    for ss in [-1,1]:
      for i in range(32):
        a=2*math.pi*i/32; coords=[]
        for gy in [.087,.105,.12]:
          r=.362-(gy-.087)*.35;aa=a+(gy-.087)*1.8*ss
          coords.append((wx+r*math.sin(aa),center[1]+ss*gy,.368+r*math.cos(aa)))
        add(curve('Tire_Sipe_'+key+'_'+str(ss)+'_'+str(i),coords,.0015,black,spin,False))
    barrel=add(cyl('Wheel_Barrel_'+key,center,.268,.215,alloy,parent=spin,body=False))
    # Manufactured rim barrel is an open tube; caps would wrongly hide drilled rotors/calipers.
    bm=bmesh.new();bm.from_mesh(barrel.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if len(f.verts)>4],context='FACES');bm.to_mesh(barrel.data);bm.free()
    rotor=add(cyl('Brake_Rotor_'+key,(wx,center[1]+sign*.09,.368),.218,.018,brake,parent=spin,body=False))
    bpy.context.view_layer.objects.active=rotor
    for modifier in list(rotor.modifiers):bpy.ops.object.modifier_apply(modifier=modifier.name)
    drill_cutters=[]
    for r in [.13,.174,.20]:
      for i in range(16):
        a=2*math.pi*(i+(r*7)%1)/16
        bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=.0042,depth=.045,location=(wx+r*math.sin(a),center[1]+sign*.09,.368+r*math.cos(a)),rotation=(math.pi/2,0,0));drill_cutters.append(bpy.context.object)
    bpy.ops.object.select_all(action='DESELECT')
    for cutter in drill_cutters:cutter.select_set(True)
    bpy.context.view_layer.objects.active=drill_cutters[0];bpy.ops.object.join();cutter=bpy.context.object
    modifier=rotor.modifiers.new('48 actual through-drilled apertures','BOOLEAN');modifier.operation='DIFFERENCE';modifier.object=cutter;modifier.solver='EXACT'
    bpy.context.view_layer.objects.active=rotor;bpy.ops.object.modifier_apply(modifier=modifier.name);bpy.data.objects.remove(cutter,do_unlink=True)
    for face in rotor.data.polygons:face.use_smooth=False # Machined planar faces must not average normals with hole walls.
    # Caliper is fixed to steering pivot, deliberately not to spin child.
    c=cube('Brake_Caliper_'+key,(wx-.175,center[1]+sign*.112,.405),(.075,.04,.18),red,.022,pivot,False)
    add(torus('Rim_Outer_Lip_'+key,(wx,yout,.368),.258,.010,chrome,spin,False))
    add(torus('Rim_Inner_Lip_'+key,(wx,yout-sign*.025,.368),.242,.006,alloy,spin,False))
    add(cyl('Center_Hub_'+key,(wx,yout,.368),.058,.027,alloy,parent=spin,body=False))
    add(cyl('Center_Cap_'+key,(wx,yout+sign*.018,.368),.032,.006,black,parent=spin,body=False))
    # Five paired turbine spokes: broad tapered aero sections, swept on outer edge.
    for i in range(5):
      a=2*math.pi*i/5
      for split in [-1,1]:
        def p(r,aa,yo):return(wx+r*math.sin(aa),yo,.368+r*math.cos(aa))
        a0=a+split*.075;a1=a+split*.13+.17
        front=yout+sign*.003;back=yout-sign*.026
        v=[p(.052,a0-.10,front),p(.052,a0+.10,front),p(.249,a1+.055,front),p(.249,a1-.055,front),p(.052,a0-.10,back),p(.052,a0+.10,back),p(.249,a1+.055,back),p(.249,a1-.055,back)]
        o=mesh('Forged_Spoke_'+key+'_'+str(i)+'_'+str(split),v,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],alloy,spin,False);bevel(o,.004,2);add(o)
      a2=a+.15;add(cyl('Lug_'+key+'_'+str(i),(wx+.042*math.sin(a2),yout+sign*.017,.368+.042*math.cos(a2)),.0055,.006,chrome,vertices=12,parent=spin,body=False))
    # Sidewall embossed-style stripe, remains subtle.
    add(torus('Sidewall_Ring_'+key,(wx,center[1]+sign*.143,.368),.306,.0018,alloy,spin,False))
    wheels[key]={'steer':pivot,'spin':spin,'parts':parts,'center':center,'radius':.366,'caliper':c}

# Build animation demonstration in original file. Pose at frame 1 remains neutral for export.
for key,d in wheels.items():
    d['spin'].rotation_mode='XYZ';d['spin'].rotation_euler[1]=0;d['spin'].keyframe_insert(data_path='rotation_euler',frame=1)
    d['spin'].rotation_euler[1]=math.tau*2;d['spin'].keyframe_insert(data_path='rotation_euler',frame=121)
    if key.startswith('Front'):
        for f,a in [(1,0),(31,.40),(61,0),(91,-.40),(121,0)]:
            d['steer'].rotation_euler[2]=a;d['steer'].keyframe_insert(data_path='rotation_euler',frame=f)
for ob in bpy.data.objects:
    if ob.animation_data and ob.animation_data.action:
        for fc in ob.animation_data.action.fcurves:
            for kp in fc.keyframe_points:kp.interpolation='LINEAR'
scene.frame_start=1;scene.frame_end=121;scene.render.fps=30;scene.frame_set(1)
# Convert curves before interchange export so all panel seams and tread details travel.
for o in list(bpy.data.objects):
    if o.type in {'CURVE','FONT'}:
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
# Mesh audit and interchange.
manifest={'asset':'Original 2017 Roadster-inspired fan concept','unit':'meter','forward':'+X','left':'+Y','up':'+Z','created_with':'Blender '+bpy.app.version_string,'license':'Original geometry and procedural materials supplied for this project. Tesla trademarks/design rights remain with their owners; no endorsement.','visual_revision':'user-red-reference-2', 'police_lightbar_mount_height_m':1.232, 'fictional_rear_fx_sockets_blender_m':[[-2.30,-.56,.415],[-2.30,.56,.415]], 'visual_reference':'User-supplied red Roadster photograph: triangular projector lamps, pronounced front haunches, concave flanks. Original approximation, not a scan.', 'production_claims':'Not Tesla CAD or an engineering model. Thrusters are fictional gameplay hardware.','fbx_export':{'axis_forward':'X','axis_up':'Z','apply_unit_scale':True,'body_origin_m':[0,0,0],'wheel_exports_centered':True},'wheel_radius_m':.366,'wheelbase_m':2.7,'wheel_centers':{k:list(v['center']) for k,v in wheels.items()},'wheel_controls':{'steer_axis':'local Z','spin_axis':'local Y','steer_names':[v['steer'].name for v in wheels.values()],'spin_names':[v['spin'].name for v in wheels.values()]},'objects':[]}
for o in bpy.data.objects:
    if o.type=='MESH':manifest['objects'].append({'name':o.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'parent':o.parent.name if o.parent else None})
manifest['materials']=[{'name':m.name,'base_color':list(m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value),'metallic':m.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value,'roughness':m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value,'transmission':m.node_tree.nodes.get('Principled BSDF').inputs['Transmission Weight'].default_value,'emission_strength':m.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value} for m in bpy.data.materials if m.use_nodes and m.node_tree.nodes.get('Principled BSDF')]
manifest['mesh_count']=len(manifest['objects']);manifest['polygon_count']=sum(o['polygons'] for o in manifest['objects'])
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
(OUT/'materials.json').write_text(json.dumps({m['name']:{k:m[k] for k in ['base_color','roughness','metallic','transmission','emission_strength']} for m in manifest['materials']},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'roadster_concept.blend'))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(OUT/'roadster_concept.glb'),export_format='GLB',use_selection=True,export_animations=True,export_apply=True)
bpy.ops.export_scene.fbx(filepath=str(OUT/'roadster_concept.fbx'),use_selection=True,axis_forward='X',axis_up='Z',apply_unit_scale=True,bake_anim=False,object_types={'MESH','EMPTY'},use_mesh_modifiers=True)
# Export engine-friendly static mesh pieces (body and 4 centered wheels), preserving detailed .blend separately.
export_col=bpy.data.collections.new('ENGINE_EXPORT_TEMP');scene.collection.children.link(export_col)
def joined_export(name,objects,origin):
    copies=[]
    for o in objects:
        if o.type!='MESH':continue
        dup=o.copy();dup.data=o.data.copy();export_col.objects.link(dup);dup.animation_data_clear();mw=o.matrix_world.copy();dup.parent=None;dup.matrix_world=mw;copies.append(dup)
    bpy.ops.object.select_all(action='DESELECT')
    for d in copies:d.select_set(True)
    bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.convert(target='MESH');bpy.ops.object.join();joined=bpy.context.object;joined.name=name
    scene.cursor.location=origin;bpy.ops.object.origin_set(type='ORIGIN_CURSOR');joined.location=(0,0,0)
    bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,axis_forward='X',axis_up='Z',apply_unit_scale=True,bake_anim=False,object_types={'MESH'},use_mesh_modifiers=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT/(name+'.glb')),export_format='GLB',use_selection=True,export_animations=False,export_apply=True)
    bpy.data.objects.remove(joined,do_unlink=True)
# Calipers fixed to the vehicle for simple static runtime mesh exports. Detailed hierarchy retains steering attachment.
joined_export('SM_CarBody',[o for o in bpy.data.objects if o.type=='MESH' and not any(o in v['parts'] for v in wheels.values())],(0,0,0))
import shutil
shutil.copyfile(OUT/'SM_CarBody.fbx',OUT/'car_body.fbx');shutil.copyfile(OUT/'SM_CarBody.glb',OUT/'car_body.glb')
for key,d in wheels.items():joined_export('SM_Wheel_'+key,d['parts'],d['center'])
bpy.data.collections.remove(export_col)
scene.cursor.location=(0,0,0)
# Studio setup saved separately, never exported as car geometry.
studio=bpy.data.collections.new('STUDIO_ONLY');scene.collection.children.link(studio)
def studio_move(o):
    for c in list(o.users_collection):c.objects.unlink(o)
    studio.objects.link(o)
# Ground and light strips make glossy shapes legible, not photorealism claims.
groundmat=mat('Studio graphite',(.07,.085,.10),.2,.4)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.003));o=bpy.context.object;o.name='StudioGround';o.data.materials.append(groundmat);studio_move(o)
world=bpy.data.worlds.new('Soft studio');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.23,.29,.38,1);world.node_tree.nodes['Background'].inputs[1].default_value=.4
for name,loc,power,size,color in [('Key',(1.2,-3.1,5.0),1800,4.5,(.88,.94,1)),('Rim',(-3.0,1.9,3.3),1600,3.0,(1,.57,.34)),('Fill',(2.8,3.0,2.5),1200,3.5,(.65,.83,1)),('Top',(-.4,0,5),800,2.7,(1,1,1))]:
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='RECTANGLE';d.size=size;d.size_y=size*.55;d.color=color
    o=bpy.data.objects.new(name,d);studio.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,.5))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Camera_Hero');cam=bpy.data.objects.new('Camera_Hero',d);studio.objects.link(cam);cam.location=(5.7,-6.6,3.2);cam.rotation_euler=(Vector((0,0,.62))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=52;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=192;scene.cycles.use_denoising=False;scene.cycles.device='CPU';scene.render.resolution_x=1440;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(OUT/'hero_front.png');scene.render.film_transparent=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'roadster_studio.blend'))
if os.environ.get('CAR_SKIP_RENDER')=='1':
    print('CAR_EXPORTS_DONE_NO_RENDER');raise SystemExit(0)
bpy.ops.render.render(write_still=True)
cam.location=(-5.4,5.9,2.6);cam.rotation_euler=(Vector((-.1,0,.6))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/'hero_rear.png');bpy.ops.render.render(write_still=True)
print('CAR_ASSETS_DONE',json.dumps({'mesh_count':manifest['mesh_count'],'polygon_count':manifest['polygon_count'],'output':str(OUT)}))
