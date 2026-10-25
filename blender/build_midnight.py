"""Original Midnight Meridian GT reconstruction; no logo, downloaded mesh or photo texture.
Reference silhouette interpreted as an independent fictional luxury hypercar.
No project-wide reuse license selected by owner. Rebuild, not recovered V12 hashes.
"""
import bpy,bmesh,math,json,sys,shutil,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'blender'));import rebuild_car_helpers as h
O=R/'assets/cars/midnight';W=R/'assets/web';P=R/'web/public/assets'
for p in(O,W,P):p.mkdir(parents=True,exist_ok=True)
h.reset();root=h.empty('CAR_ROOT');body=h.empty('CarBody',parent=root);groups=[root,body];h.CURRENT=body
paint=h.material('Crimson multi-coat | original fan concept',(.018,.042,.095),.76,.245,coat=.6)
carbon=h.material('Midnight satin carbon structure',(.008,.012,.017),.36,.3)
glass=h.material('Midnight clear smoke glazing',(.052,.079,.105),.12,.12,alpha=.26,coat=.3)
alloy=h.material('Midnight champagne forged alloy',(.52,.40,.22),.85,.23)
rubber=h.material('Tire rubber | original project',(.009,.011,.013),.02,.78)
white=h.material('Midnight cool running lights',(.72,.87,1),.1,.2,emit=3)
red=h.material('Midnight rear vermilion lights',(.8,.008,.013),.1,.22,emit=2.7)
interior=h.material('Midnight espresso leather',(.04,.027,.019),.03,.58)
accent=h.material('Midnight coastal cyan lower accents',(.008,.23,.34),.58,.27)
# Smooth, broad muscular shell, intentionally unlike the angular Bronze/Vermilion bodies.
rows=[(-2.35,.88,.70,.10),(-2.07,1.015,.73,.16),(-1.35,1.09,.735,.20),(-.72,1.015,.735,.09),(0,.985,.715,.065),(.75,1.015,.715,.11),(1.35,1.075,.69,.205),(1.90,1.03,.625,.15),(2.20,.955,.575,.09),(2.36,.84,.52,.07)]
def spec(x):return h.smooth_interp(rows,x)
def top(x,y):
 w,zc,lift=spec(x);q=min(1,abs(y)/w);return zc+.025*math.sin(math.pi*q)+lift*q*q-.045*q**8
vs=[];xs=[-2.35+4.71*i/86 for i in range(87)];N=28
for x in xs:
 w,zc,li=spec(x)
 for j in range(17):
  y=w*math.cos(math.pi*j/16);vs.append((x,y,top(x,y)))
 for j in range(1,12):
  a=math.pi*j/12;y=-w*math.cos(a);z=.285-(.065*math.sin(a));vs.append((x,y,z))
fs=[]
for i in range(len(xs)-1):
 for j in range(N):fs.append((i*N+j,i*N+(j+1)%N,(i+1)*N+(j+1)%N,(i+1)*N+j))
fs.extend([tuple(reversed(range(N))),tuple((len(xs)-1)*N+j for j in range(N))]);shell=h.mesh('Midnight rounded monocoque with actual apertures',vs,fs,paint,True)
def safe_cut(cut,name):
 bm=bmesh.new();bm.from_mesh(shell.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(shell.data);bm.free();h.cut(shell,cut,name)
# Genuine arch openings, enough longitudinal room for the declared steering envelope.
for x in[-1.35,1.35]:
 for side in[-1,1]:safe_cut(h.cylinder('Temporary wheel clearance cutter',(x,side*.99,.368),.435,1.15,carbon,'Y',72),'True wheel arch opening')
# Open cabin, sculpted side doors and open front storage well, not black stickers.
safe_cut(h.box('Temporary open passenger cell',(-.24,0,1.15),(1.92,1.42,1.18),carbon,0),'Passenger cell opening')
for side in[-1,1]:safe_cut(h.box('Temporary door aperture',(.0025,side*1.0,.79),(1.605,.55,.92),carbon,0),'Actual independent door opening')
hoodoutline=[(.86,-.57),(1.74,-.49),(2.06,-.37),(2.06,.37),(1.74,.49),(.86,.57)]
safe_cut(h.prism('Temporary front luggage aperture',hoodoutline,.46,1.6,carbon),'Front luggage well aperture')
# Front deep three-part cooling mouth, central curved grille stays physically recessed.
safe_cut(h.box('Temporary front air opening',(2.36,0,.415),(.45,1.72,.29),carbon,0),'Open front intake band')
be=shell.modifiers.new('Small radiused cut sheet edges','BEVEL');be.width=.005;be.segments=2;be.limit_method='ANGLE';be.angle_limit=.6;be.harden_normals=True
# Floor plate has shaped wheel relief so it cannot intersect rotating/steering tires.
outline=[(2.29,-.80),(1.81,-.78),(1.79,-.48),(.90,-.48),(.85,-.86),(-.85,-.86),(-.91,-.48),(-1.79,-.48),(-1.84,-.80),(-2.32,-.80),(-2.32,.80),(-1.84,.80),(-1.79,.48),(-.91,.48),(-.85,.86),(.85,.86),(.90,.48),(1.79,.48),(1.81,.78),(2.29,.80)]
h.prism('Sculpted carbon undertray',outline,.208,.244,carbon)
# Real storage well behind the opening bonnet.
h.box('Frunk fitted floor',(1.32,0,.465),(1.11,.86,.04),carbon,.02)
for y in[-.44,.44]:h.box('Frunk lined side wall',(1.32,y,.56),(1.12,.035,.20),carbon,.015)
for x in[.78,1.86]:h.box('Frunk lined bulkhead',(x,0,.56),(.035,.88,.20),carbon,.015)
# A separate rising bonnet with sculpted flowing crest and matching narrow shut lines.
hood=h.empty('Hood',(.77,0,.76),body);groups.append(hood);h.CURRENT=hood
def hoodfn(t,u):
 x=.82+1.30*t;ww=.625-.20*t**1.8;y=(2*u-1)*ww;return(x,y,top(x,y)+.016+.021*math.sin(math.pi*t)*(1-(2*u-1)**2))
o=h.panel('Sculpted opening midnight bonnet',hoodfn,24,18,paint);so=o.modifiers.new('Bonnet inner sheet thickness','SOLIDIFY');so.thickness=.014
for side in[-1,1]:
 h.line('Bonnet dark shut line',[hoodfn(i/32,0 if side<0 else 1)for i in range(33)],.0023,carbon,5)
 pts=[]
 for i in range(22):
  t=i/21;x=.85+1.10*t;y=side*(.40-.17*t);pts.append((x,y,top(x,y)+.036+.017*math.sin(math.pi*t)))
 h.line('Raised flowing hood crease',pts,.010,paint,7)
 h.line('Inset hood cooling slit',[(.91,side*.47,top(.91,.47)+.022),(1.26,side*.44,top(1.26,.44)+.022),(1.55,side*.38,top(1.55,.38)+.022)],.012,carbon,7)
h.CURRENT=body
# Curved front grille perimeter, deep dark intake volumes and restrained satin ribs.
h.box('Deep front intake interior',(2.182,0,.407),(.04,1.66,.255),carbon,.008)
for side in[-1,1]:
 h.box('Front vertical intake divider',(2.30,side*.335,.405),(.22,.052,.27),paint,.018)
 for j in range(5):h.box('Front intake internal cooling fin',(2.235,side*(.43+j*.077),.412),(.11,.014,.205),carbon,.004)
# Arched opening, deliberately unbranded and not the reference manufacturer's exact outline.
arch=[(2.405,-.265,.275),(2.405,-.265,.48)]+[(2.405,.265*math.cos(math.pi-i*math.pi/24),.48+.245*math.sin(math.pi-i*math.pi/24))for i in range(25)]+[(2.405,.265,.275),(2.405,-.265,.275)]
h.line('Continuous central arch grille surround',arch,.018,alloy,8)
for j in range(13):
 y=-.23+j*.038;zmax=.48+.22*math.sqrt(max(0,1-(y/.245)**2));h.line('Unbranded vertical grille fluting',[(2.386,y,.29),(2.386,y,zmax)],.005,carbon,5)
for z in[.32,.38,.44,.50,.56,.62]:
 ww=.235 if z<.48 else .235*math.sqrt(max(0,1-((z-.48)/.24)**2));h.line('Grille inset transverse texture',[(2.38,-ww,z),(2.38,ww,z)],.0035,carbon,5)
for side in[-1,1]:
 h.prism('Cyan front floating splitter',[(2.44,side*.29),(2.44,side*.85),(2.23,side*1.02),(1.98,side*1.04),(2.05,side*.84),(2.22,side*.29)],.218,.25,accent)
 # Raised slim running lamp arches above each front fender.
 pts=[]
 for i in range(23):
  t=i/22;x=1.42+.73*t;y=side*(.81-.14*t);pts.append((x,y,top(x,y)+.020))
 h.line('Long sculpted headlamp black socket',pts,.018,carbon,8)
 h.line('Thin luminous horseshoe companion lamp',[(x,y,z+.023)for x,y,z in pts],.009,white,6)
 for t in[.18,.35,.52,.69]:
  x=1.42+.73*t;y=side*(.81-.14*t);h.box('Inset precision headlamp module',(x,y,top(x,y)+.029),(.055,.027,.017),white,.006)
# Cab glazing shares exact edges and a deep painted roof, avoiding floating disconnected windows.
def wind(t,u):
 q=2*u-1;x=.76*(1-t)-.26*t;w=.71*(1-t)+.64*t;z=(top(.76,.71*q)+.018)*(1-t)+(1.265-.037*q*q)*t+.035*math.sin(math.pi*t);return(x-.025*math.sin(math.pi*t)*(1-q*q),q*w,z)
def roof(t,u):
 q=2*u-1;return(-.26-.67*t,q*(.64+.025*t),1.265-.026*t-.037*q*q+.016*math.sin(math.pi*t))
def rear(t,u):
 q=2*u-1;x=-.93-.63*t;w=.665+.15*t;return(x,q*w,(1.239-.037*q*q)*(1-t)+(top(-1.56,.815*q)+.016)*t)
h.panel('Curved clear front windshield',wind,20,20,glass)
h.panel('Continuous painted grand sport roof',roof,16,20,paint)
h.panel('Rear transparent engine canopy',rear,12,20,glass)
for side in[-1,1]:
 h.line('Sculpted A pillar',[wind(t/24,1 if side>0 else 0)for t in range(25)],.014,paint,8)
 h.line('Continuous roof edge',[roof(t/18,1 if side>0 else 0)for t in range(19)],.013,paint,8)
 h.line('Rear glazing boundary',[rear(t/18,1 if side>0 else 0)for t in range(19)],.013,paint,8)
 # Substantial painted C-pillar and hallmark curved side channel, with no reference logo.
 v=[roof(1,1 if side>0 else 0),rear(1,1 if side>0 else 0),(-1.68,side*1.055,.87),(-1.02,side*1.07,.87)]
 h.mesh('Wide sculpted rear buttress',v,[(0,1,2,3)],paint,True,normal_hint=(0,side,0))
 pts=[]
 for i in range(25):
  t=i/24;pts.append((-1.04-.35*math.sin(math.pi*t)*(1-t)+.25*t,side*(.80+.22*math.sin(math.pi*t)),1.20-.82*t))
 h.line('Swept C-shaped rear shoulder highlight',pts,.035,paint,8)
 h.mesh('Recessed side cooling channel',[(-.83,side*1.022,.80),(-1.04,side*1.07,.77),(-.93,side*1.025,.42),(-.84,side*1.02,.34)],[(0,1,2,3)],carbon,False,normal_hint=(0,side,0))
 h.prism('Cyan swept sill',[(.84,side*.98),(.84,side*1.055),(-.86,side*1.065),(-.96,side*.99)],.25,.30,accent)
 # Independent conventional doors, glTF opening axis +Y on right / -Y on left.
 tag='Left'if side>0 else'Right';hinge=h.empty('DoorHinge_'+tag,(.802,side*1.024,.77),body);door=h.empty('Door_'+tag,parent=hinge);groups.extend([hinge,door]);h.CURRENT=door
 def doorfn(t,u,side=side):
  x=.792-1.572*t;z=.335+(.76-.335)*u;w=spec(x)[0];return(x,side*(w+.003-.018*(1-u)**2),z)
 o=h.panel('Sculpted '+tag+' door skin',doorfn,20,10,paint,(0,side,0));so=o.modifiers.new('Door skin real thickness','SOLIDIFY');so.thickness=.018
 def sidewindow(t,u,side=side):
  xb=.76-1.69*t-.025*(1-t);yb=.71+.08*t;zb=top(xb,yb)+.018;xt=-.26-.67*t-.025*(1-t);yt=.64+.025*t;zt=1.228-.026*t+.016*math.sin(math.pi*t);return(xb*(1-u)+xt*u,side*(yb*(1-u)+yt*u+.018*math.sin(math.pi*u)),zb*(1-u)+zt*u)
 h.panel('Flush transparent '+tag+' door window',sidewindow,20,8,glass,(0,side,0))
 # The real painted upper door shoulder bridges the outer skin to the inset glazing.
 def shoulderfn(t,u,side=side):
  xo=.792-1.572*t;xi=min(xo,.735);q=(.735-xi)/1.665;inner=.71+.08*q;outer=spec(xo)[0]+.003;return(xo*(1-u)+xi*u,side*(outer*(1-u)+inner*u),.76*(1-u)+(top(xi,inner)+.016)*u+.012*math.sin(math.pi*u))
 h.panel('Painted '+tag+' door shoulder',shoulderfn,16,4,paint)
 h.line('Door lower window seal',[sidewindow(i/24,0)for i in range(25)],.006,carbon,6)
 h.line('Door flowing exterior shut line',[doorfn(0,1),doorfn(0,0),doorfn(1,0),doorfn(1,1)],.0025,carbon,5)
 h.box('Flush luxury door handle',(-.55,side*(spec(-.55)[0]+.017),.705),(.15,.018,.020),carbon,.006)
 h.line('Aerodynamic mirror stem',[(.49,side*.80,.865),(.42,side*1.02,.90)],.015,carbon,7)
 h.box('Sculpted mirror shell',(.43,side*1.08,.929),(.255,.16,.082),paint,.032)
 h.box('Mirror rear face',(.297,side*1.08,.929),(.008,.123,.047),glass,.013)
 # Inner panel is visible in the inspection open-door view.
 h.box('Door interior leather panel',(-.04,side*.925,.53),(1.31,.04,.31),carbon,.035)
 h.line('Door interior pull',[(-.25,side*.900,.58),(.02,side*.900,.58)],.018,carbon,8)
 h.CURRENT=body
# Detailed two-seat cockpit beneath genuine transparent glazing.
h.cockpit(paint,carbon,glass,alloy,interior,white)
# Engine bay grille lies behind cabin, visible through rear glass.
for y in[-.54,-.27,0,.27,.54]:h.box('Longitudinal engine cover cooling rib',(-1.75,y,.783),(.52,.032,.055),carbon,.01)
h.box('Rear deep cooling facade',(-2.355,0,.535),(.048,1.77,.40),carbon,.02)
for side in[-1,1]:
 h.line('Swept rear LED ribbon',[(-2.39,side*.10,.761),(-2.39,side*.64,.765),(-2.34,side*.88,.73)],.014,red,7)
 h.torus('Rear exhaust machined rim',(-2.395,side*.62,.375),.064,.007,alloy,'X',32,7)
 h.cylinder('Rear exhaust dark depth',(-2.39,side*.62,.375),.056,.045,carbon,'X',32)
for y in[-.76,-.45,0,.45,.76]:
 h.mesh('Rear diffuser vertical vane',[(-2.42,y,.22),(-1.94,y,.25),(-1.94,y,.36),(-2.42,y,.39)],[(0,1,2,3)],carbon,False,normal_hint=(0,1,0));carbon['double_sided']=True
# Fixed rear wing only. No active AeroWing_Hinge is exported.
wing=h.empty('RearWing',parent=body);groups.append(wing);h.CURRENT=wing
for side in[-1,1]:h.box('Fixed wing support',(-1.96,side*.64,.965),(.11,.035,.34),carbon,.012)
h.box('Swept fixed rear aerofoil',(-2.03,0,1.148),(.40,2.03,.055),carbon,.024)
for side in[-1,1]:
 h.box('Rear wing endplate',(-2.03,side*1.035,1.18),(.42,.029,.12),paint,.012)
 h.CURRENT=wing
 h.line('Subtle wing endplate edging',[(-2.235,side*1.051,1.185),(-1.84,side*1.051,1.185)],.008,paint,6)
 h.CURRENT=wing
h.CURRENT=None
wheelrig=h.build_wheels(root,groups,accent,alloy,rubber,prefix='Midnight',lateral=.924,spokes=6)
root['design']='Original Midnight Meridian GT reconstruction; approximate reference-inspired fictional vehicle, not manufacturer CAD.'
root['provenance']='Original project geometry. Reuse license not selected by owner. References are visual only, not embedded.'
manifest={'id':'midnight','name':'Midnight Meridian GT','reconstructed':True,'generator':'blender/build_midnight.py','native_source':'assets/cars/midnight/Midnight_Meridian_GT.blend','forward':'+X','up':'+Y','left':'-Z','units':'metres','paint_material':paint.name,'wheel_radius_m':.366,'wheelbase_m':2.7,'hub_height_m':.368,'wheel_centers_three':{k:[st.location.x,st.location.z,-st.location.y]for k,st in wheelrig['steers'].items()},'max_steer_rad':.45,'body_visual_envelope':{'roll':.008,'pitch':.005,'heave':.002},'door_open_rad':.70,'door_axes_three':{'Left':[0,-1,0],'Right':[0,1,0]},'hood_open_rad':.60,'hood_axis_three':[0,0,1],'rear_wing':'Fixed RearWing, not animated; supports and blade are one rigid assembly.','boost_mounts_three':[[-2.4,.255,-.56],[-2.4,.255,.56]],'cockpit_eye_three':[-.25,1.045,.36],'provenance':'Original reconstructed project geometry; reuse license not selected by owner. No manufacturer logos, photo textures or downloaded geometry.','limitations':['Fictional design and game mechanics, not a verified manufacturer replica/specification.','Preview is Blender CPU; actual browser integration is a separate test.']}
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(O/'Midnight_Meridian_GT.blend'));h.export_glb(groups,O/'car_midnight.glb',manifest)
sys.path.insert(0,str(O));from clean_export import clean;clean(O/'car_midnight.glb',manifest)
manifest['native_mesh_parts']=len([o for o in bpy.data.objects if o.type=='MESH']);(O/'manifest.json').write_text(json.dumps(manifest,indent=2));print('MIDNIGHT_CANDIDATE',json.dumps(manifest),flush=True)
