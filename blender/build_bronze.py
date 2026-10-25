"""New reconstruction of the original Bronze Apex coupe from private visual references.
No project-wide reuse license has been selected for original project material;
third-party components retain their stated licenses. No external geometry/photos embedded.
"""
import bpy,math,sys,json,shutil,hashlib,os
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'blender'))
import rebuild_car_helpers as H
OUT=ROOT/'assets/cars/bronze';OUT.mkdir(parents=True,exist_ok=True);WEB=ROOT/'web/public/assets';STAGE=ROOT/'assets/web'
H.reset();paint=H.material('Crimson multi-coat | original fan concept',(.44,.205,.063),.72,.245,coat=.55);carbon=H.material('Bronze Apex | graphite aerodynamic composite',(.013,.018,.021),.38,.3);glass=H.material('Bronze Apex | smoked transparent glass',(.055,.09,.11),.12,.12,alpha=.29);alloy=H.material('Bronze Apex | brushed gunmetal alloy',(.20,.23,.26),.86,.26);rubber=H.material('Bronze Apex | Tire rubber',(.013,.016,.019),.03,.67);interior=H.material('Bronze Apex | charcoal cockpit leather',(.028,.033,.035),.05,.61);white=H.material('Bronze Apex | ice white LED',(.78,.93,1),.08,.2,emit=4);red=H.material('LED ruby red | Bronze Apex rear lamps',(.65,.012,.014),.15,.22,emit=2.0)
root=H.empty('CAR_ROOT');body=H.empty('CarBody',parent=root);wing=H.empty('RearWing',parent=body);hood=H.empty('Hood',(.65,0,.75),body);doors={side:H.empty('Door_Left'if side>0 else'Door_Right',(.65,side*.94,.65),body)for side in(-1,1)};groups=[root,body,wing,hood,*doors.values()];H.CURRENT=body
rows=[(-2.36,.88,.66),(-2.10,1.01,.78),(-1.35,1.055,.85),(-.75,.94,.78),(0,.90,.76),(.65,.95,.76),(1.35,1.04,.85),(1.95,.98,.66),(2.36,.84,.58)]
def dims(x):return H.smooth_interp(rows,x)
def arch(x):
 d=min(abs(x-1.35),abs(x+1.35));return .368+math.sqrt(max(0,.465**2-d*d)) if d<.465 else .19

def top(x,u):
 w,z=dims(x);center=z-(0 if x>2.25 else .03 if abs(x)>2.1 else .12 if abs(x)>1 else .02);zz=center+(z-center)*abs(u)**1.7;return (x,w*u,zz)
N=112;M=26;vs=[];fs=[]
for i in range(N+1):
 x=-2.36+4.72*i/N
 for j in range(M+1):vs.append(top(x,-1+2*j/M))
for i in range(N):
 x=-2.36+4.72*(i+.5)/N
 for j in range(M):
  u=-1+2*(j+.5)/M
  if -.97<x<.56 and abs(u)<.68:continue
  q=i*(M+1)+j;fs.append((q,q+M+1,q+M+2,q+1))
H.mesh('Continuous sculpted bronze shoulder shell',vs,[f for f in fs if sum(vs[i][0]for i in f)/4<=.65],paint,True,normal_hint=(0,0,1));H.CURRENT=hood;H.mesh('Distinct shaped bronze hood',vs,[f for f in fs if sum(vs[i][0]for i in f)/4>.65],paint,True,normal_hint=(0,0,1));H.CURRENT=body
for side in(-1,1):
 sv=[];sf=[];df=[]
 for i in range(113):
  x=-2.36+4.72*i/112;w,z=dims(x);lo=arch(x)
  for j in range(8):b=j/7;sv.append((x,side*(w-.048*math.sin(math.pi*b)),lo+(z-lo)*b))
 for i in range(112):
  for j in range(7):q=i*8+j;f=(q,q+8,q+9,q+1);(df if -.82<sum(sv[k][0]for k in f)/4<.66 else sf).append(f)
 H.mesh('Sculpted wheel arch side shell '+str(side),sv,sf,paint,True,normal_hint=(0,side,0));H.CURRENT=doors[side];H.mesh('Separate closed door outer panel '+str(side),sv,df,paint,True,normal_hint=(0,side,0));H.CURRENT=body
 # Real rolled arch lip and dark inner return, leaving wheel/steering swept volume free.
 for axle in(-1.35,1.35):
  pts=[]
  for k in range(37):
   a=math.pi*k/36;x=axle+.465*math.cos(a);w,z=dims(x);pts.append((x,side*(w+.003),.368+.465*math.sin(a)))
  H.line('Precision fender rolled edge',pts,.009,paint,6)
  H.panel('Dark wheel well inner lip',lambda a,b:(lambda theta,x:(x,side*(dims(x)[0]-.035*b),.368+.463*math.sin(theta)))(math.pi*a,axle+.463*math.cos(math.pi*a)),36,2,carbon,(0,side,0))
 H.line('Carbon sill blade '+str(side),[(-.84,side*.966,.18),(-.40,side*.93,.155),(.55,side*.948,.17),(.87,side*.99,.20)],.025,carbon,6)
 # Angular side intake is a recessed three-dimensional mouth behind the door.
 pts=[(-.84,side*.95,.66),(-.41,side*.915,.45),(-.57,side*.935,.25),(-.88,side*.962,.27)]
 H.mesh('Deep side cooling intake',pts,[(0,1,2,3)],carbon,False,normal_hint=(0,side,0));H.line('Raised intake shoulder',[pts[0],(-.63,side*.966,.49),pts[1]],.014,paint,6)
 for k in range(4):H.line('Intake internal turning vane',[(-.81+k*.055,side*.952,.31),(-.75+k*.055,side*.94,.49)],.006,alloy,4)
 H.line('Door precision shut line',[(-.73,side*.95,.69),(-.82,side*.96,.28),(.64,side*.95,.27),(.70,side*.94,.68)],.0028,carbon,4)
 H.box('Flush door release',(-.45,side*.958,.647),(.115,.011,.022),carbon,.006)
 H.line('Mirror aerodynamic support',[(.47,side*.78,.78),(.36,side*1.065,.87)],.016,carbon,6);H.box('Bronze mirror cap',(.33,side*1.115,.889),(.22,.125,.065),paint,.026);H.box('Mirror rear optical face',(.224,side*1.115,.888),(.005,.106,.043),alloy,.01)
# Front hexagonal intake, separate true throat and bumper rim.
outline=[(-.59,.22),(.59,.22),(.75,.35),(.58,.52),(-.58,.52),(-.75,.35)]
outer=[(-.80,.17),(.80,.17),(.87,.34),(.84,.58),(-.84,.58),(-.87,.34)];fv=[(x,y,z)for x in(2.29,2.365)for ring in(outer,outline)for y,z in ring];ff=[]
for i in range(6):
 j=(i+1)%6;ff.extend([(i,j,j+6,i+6),(i+12,i+18,j+18,j+12),(i,i+12,j+12,j),(i+6,j+6,j+18,i+18)])
H.mesh('Contoured hollow nose fascia ring',fv,ff,paint,True,bevel=.008)
vs=[(x,y,z)for x in(2.325,2.18)for y,z in outline];faces=[(i,(i+1)%6,(i+1)%6+6,i+6)for i in range(6)];H.mesh('Deep six sided front grille throat',vs,faces,carbon,False);H.mesh('Dark grille rear',[(2.178,y,z)for y,z in outline],[tuple(range(6))],carbon,False,normal_hint=(1,0,0));H.line('Hexagonal bronze grille rolled rim',[(2.34,y,z)for y,z in outline+[outline[0]]],.021,paint,6)
for yy in range(-10,11):H.line('Grille vertical fine mesh',[(2.195,yy*.052,.245),(2.195,yy*.052,.49)],.003,alloy,4)
for zz in range(5):H.line('Grille horizontal fine mesh',[(2.196,-.55,.25+zz*.052),(2.196,.55,.25+zz*.052)],.003,alloy,4)
for side in(-1,1):
 H.mesh('Recessed angled headlight housing',[(2.376,side*.64,.55),(2.376,side*.835,.55),(2.376,side*.835,.37),(2.376,side*.67,.37)],[(0,1,2,3)],carbon,False,normal_hint=(1,0,0))
 for y,z,r in[(.735,.49,.039),(.828,.49,.026)]:
  H.cylinder('Headlight projector bezel',(2.382,side*y,z),r+.013,.016,alloy,'X',28);H.cylinder('Headlight projector lens',(2.394,side*y,z),r,.008,white,'X',28)
 for k in range(6):H.cylinder('Signature six LED running lamp',(2.389,side*(.674+k*.029),.395+k*.002),.009,.012,white,'X',12)
 H.mesh('Lower brake cooling duct',[(2.34,side*.68,.26),(2.33,side*.88,.30),(2.36,side*.89,.18),(2.37,side*.72,.18)],[(0,1,2,3)],carbon,False,normal_hint=(1,0,0))
 # Hood extraction troughs with raised surrounding crease and sunk black floor.
 pts=[(1.0,side*.34,.757),(1.80,side*.59,.69),(2.04,side*.59,.619),(1.43,side*.40,.70)]
 H.mesh('Triangular hood extraction recess',pts,[(0,1,2,3)],carbon,False,normal_hint=(0,0,1));H.line('Hood extraction sharp edge',[pts[0],pts[1],pts[2]],.012,paint,5)
 for k in range(5):
  x=1.33+k*.105;y=side*(.385+k*.027);z=.739-k*.012;H.line('Hood cooling louver',[(x,y-.035,z),(x+.07,y+.035,z-.008)],.007,alloy,4)
H.line('Low front carbon splitter',[(2.28,-.92,.156),(2.42,-.70,.145),(2.45,0,.14),(2.42,.70,.145),(2.28,.92,.156)],.025,carbon,6)
# Cohesive greenhouse: sloped screen, real roof and distinct rear quarter panes.
H.panel('Single curved front windshield',lambda a,b:(.67-.77*a,.665*(1-.085*a)*(2*b-1),.762+.495*a+.022*math.sin(math.pi*b)),18,18,glass,(1,0,1))
H.panel('Bronze hardtop crown',lambda a,b:(-.10-.79*a,.607*(2*b-1),1.258+.047*math.sin(math.pi*a)-.035*(2*b-1)**2),18,20,paint,(0,0,1))
H.panel('Recessed rear engine window',lambda a,b:(-.89-.62*a,.60*(1-.15*a)*(2*b-1),1.245-.47*a+.013*math.sin(math.pi*b)),14,14,glass,(-1,0,1))
for side in(-1,1):
 win=[(.63,side*.667,.755),(-.10,side*.60,1.245),(-.85,side*.60,1.245),(-1.10,side*.67,.785)]
 H.mesh('Recessed side glazing',win,[(0,1,2,3)],glass,True,normal_hint=(0,side,0));H.line('Slim continuous greenhouse frame',win+[win[0]],.015,paint,7);H.line('Slim quarter glass division',[(-.71,side*.606,1.236),(-.81,side*.654,.79)],.009,carbon,5)
 H.line('Rear flying buttress shoulder',[(-.88,side*.61,1.245),(-1.18,side*.70,1.04),(-1.65,side*.82,.83)],.025,paint,7)
 H.line('Hood front screen seam',[(.67,side*.667,.767),(.68,side*.40,.752),(.68,0,.75)],.003,carbon,4)
# Rear fascia, circular lamps and diffuser, split quad exhausts.
H.box('Tail fascia main dark recess',(-2.365,0,.52),(.045,1.65,.27),carbon,.045)
for side in(-1,1):
 for yy in(.56,.74):H.cylinder('Round rear lamp recess',(-2.40,side*yy,.58),.071,.018,carbon,'X',32);H.torus('Round ruby tail lamp',(-2.415,side*yy,.58),.049,.011,red,'X',32,8)
 for yy in(.27,.43):H.cylinder('Exhaust machined surround',(-2.413,side*yy,.31),.047,.08,alloy,'X',28);H.cylinder('Exhaust dark open throat',(-2.459,side*yy,.31),.035,.006,carbon,'X',24)
H.box('Rear carbon diffuser floor',(-2.12,0,.155),(.49,1.77,.038),carbon,.01)
for yy in(-.77,-.48,0,.48,.77):H.box('Diffuser vertical strake',(-2.10,yy,.23),(.57,.018,.14),carbon,.005)
H.CURRENT=wing
for side in(-1,1):H.box('Rear wing sculpted support',(-1.94,side*.57,.91),(.09,.046,.24),carbon,.01)
H.box('Fixed aero wing carbon plane',(-1.98,0,1.04),(.34,1.92,.035),carbon,.015)
for side in(-1,1):H.box('Bronze wing end plate',(-1.97,side*.97,1.055),(.37,.022,.095),paint,.015)
H.CURRENT=body;H.cockpit(paint,carbon,glass,alloy,interior,white);rig=H.build_wheels(root,groups,paint,alloy,rubber,'Bronze Apex',spokes=5)
H.CURRENT=None;bpy.context.view_layer.update()
manifest={'id':'bronze','name':'BRONZE APEX','reconstruction':'New original geometry reconstructed 2026-10-23 from visual references; not the missing former V12 bytes.','source':'blender/build_bronze.py','license':'No project-wide reuse license has been selected for original project material; third-party components retain their stated licenses.','axes':'Blender X forward,Y left,Z up; GLB X forward,Y up,-Z left.','steer_limit_rad':.45,'wheel_radius_m':.366,'boost_mounts_three':[[-2.4,.26,-.56],[-2.4,.26,.56]],'fixed_wing':'RearWing','paint_material':paint.name}
H.export_glb(groups,STAGE/'car_bronze.glb',manifest);shutil.copy2(STAGE/'car_bronze.glb',WEB/'car_bronze.glb');(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'bronze_apex.blend'),compress=True)
print('BRONZE_EXPORTED',manifest['triangles'],manifest['draw_calls'],flush=True)
# Preview rendering is intentionally separate: render_rebuilt_car.py loads the actual GLB.
