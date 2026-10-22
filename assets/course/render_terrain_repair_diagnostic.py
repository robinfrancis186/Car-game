"""Asset-space diagnostic, not a browser screenshot or performance test."""
from pathlib import Path
import importlib.util,json
import os
os.environ["MPLCONFIGDIR"]="/tmp/kerala-matplotlib-cache"
os.environ["XDG_CACHE_HOME"]="/tmp/kerala-font-cache"
for cache in [os.environ["MPLCONFIGDIR"],os.environ["XDG_CACHE_HOME"]]:Path(cache).mkdir(parents=True,exist_ok=True)
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.ticker import MultipleLocator
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('coverage',Path(__file__).with_name('audit_terrain_coverage.py'));a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
old=a.glb_triangles(ROOT/'assets/course/terrain_before_repair.glb');new=a.glb_triangles(ROOT/'assets/web/Course_Terrain.glb');water=a.glb_triangles(ROOT/'assets/web/Course_Water.glb');road=a.glb_triangles(ROOT/'assets/web/Course_Road.glb');before=json.loads((ROOT/'assets/course/terrain_coverage_baseline.json').read_text());after=json.loads((ROOT/'assets/course/terrain_coverage_repaired.json').read_text());center=np.array(next(r['point'] for r in after['records'] if r['s']==2200 and r['lateral']==7));center[2]*=-1
fig,axes=plt.subplots(1,2,figsize=(12,6));fig.subplots_adjust(bottom=.14,top=.80,left=.06,right=.99,wspace=.22);fig.patch.set_facecolor('#f6f2e8')
for ax,tris,data,title in zip(axes,[old,new],[before,after],['Before: missing ground exposes lower sky','Repaired: continuous dry land, exact lake holes']):
 ax.set_facecolor('#bb936d')
 def draw(t,color,zorder):
  xy=t[:,:,[0,2]].copy();xy[:,:,1]*=-1;ax.add_collection(PolyCollection(xy,facecolors=color,edgecolors='none',zorder=zorder))
 ground=np.all(np.abs(tris[:,:,1]+.04)<1e-5,axis=1);draw(tris[ground],'#72835a',1);draw(tris[~ground],'#cbb685',2);draw(water,'#4e9096',3);draw(road,'#4c5352',4)
 for r in data['records']:
  if not r['expected_dry_land'] or abs(r['s']-2200)>125:continue
  p=r['point'];ax.scatter(p[0],-p[2],s=16,c='#d7f5ce' if r['terrain_hit'] else '#ed6249',edgecolors='#273a31',linewidths=.25,zorder=5)
 ax.set_xlim(center[0]-210,center[0]+210);ax.set_ylim(center[2]-210,center[2]+210);ax.set_aspect('equal');ax.set_title(title,fontsize=11,fontweight='bold',pad=12);ax.set_xlabel('Local east (m)');ax.set_ylabel('Local north (m)');ax.grid(alpha=.1);ax.xaxis.set_major_locator(MultipleLocator(100))
fig.suptitle('Kappil Coast · route s ≈ 2,200 m\nActual GLB geometry projection; pale dots = ground hit, red dots = missing ground',fontsize=13,fontweight='bold');fig.text(.5,.012,'Technical top-down diagnostic — not a game screenshot. OSM-derived geography © OpenStreetMap contributors / ODbL.',ha='center',fontsize=8,color='#4b5148')
fig.savefig(ROOT/'assets/web/terrain_repair_diagnostic.png',dpi=150,facecolor=fig.get_facecolor())
print('DIAGNOSTIC_READY')
