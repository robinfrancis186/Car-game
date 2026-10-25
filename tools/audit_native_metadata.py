"""Read-only Blender source metadata inventory. Run with --disable-autoexec."""
import bpy,pathlib,json,re,hashlib
R=pathlib.Path(__file__).resolve().parents[1];out=[]
for p in sorted((R/'assets').rglob('*.blend')):
 if any(s in p.name.lower()for s in('preview','runtime_roundtrip','helper_smoke')):continue
 before=hashlib.sha256(p.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(p),load_ui=False,use_scripts=False);matches=[]
 for col in ('objects','meshes','materials','scenes','collections','worlds','images','node_groups','texts'):
  for item in getattr(bpy.data,col):
   for k in item.keys():
    v=str(item[k])
    if re.search(r'\bCC0\b|public.domain dedication',k+' '+v,re.I):matches.append([col,item.name,k,v])
   if col=='texts' and re.search(r'\bCC0\b|public.domain dedication',item.as_string(),re.I):matches.append(['text',item.name,item.as_string()])
 images=[{'name':i.name,'source':i.source,'packed':bool(i.packed_file),'filename':pathlib.Path(i.filepath).name}for i in bpy.data.images if i.type not in {'RENDER_RESULT','COMPOSITING'}]
 assert before==hashlib.sha256(p.read_bytes()).hexdigest(),'Read-only audit changed source'
 out.append({'path':str(p.relative_to(R)),'sha256':before,'grant_matches':matches,'images':images,'linked_libraries':[x.name for x in bpy.data.libraries],'embedded_text_names':[x.name for x in bpy.data.texts]})
(R/'tests/recovery/native_metadata_final.json').write_text(json.dumps(out,indent=2)+'\n');assert not any(x['grant_matches']for x in out);print('PASS_NATIVE_METADATA',len(out),'primary scenes; zero original-asset hidden grant tags; source hashes unchanged.')
