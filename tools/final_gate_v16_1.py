"""Run a source/geometry/build gate; never publishes or claims browser acceptance."""
from pathlib import Path
import hashlib,json,datetime,subprocess,time
R=Path(__file__).resolve().parents[1];D=R/'tests/v16_1';D.mkdir(exist_ok=True)
def identity():
 paths=[R/'web/index.html']+[p for d in ['web/src','web/public'] for p in (R/d).rglob('*') if p.is_file()]
 return {p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
before=identity();commands=[(['npm','test'],R/'web'),(['npm','run','build'],R/'web'),(['python','tools/audit_runtime_payload.py'],R),(['python','tools/audit_standalone.py'],R)]
rows=[];start=datetime.datetime.now(datetime.timezone.utc).isoformat()
with (D/'full_gate.log').open('w') as log:
 for cmd,cwd in commands:
  log.write('\nCOMMAND '+str(cmd)+'\n');log.flush();t=time.monotonic();p=subprocess.run(cmd,cwd=cwd,stdout=log,stderr=subprocess.STDOUT)
  rows.append({'command':cmd,'cwd':cwd.relative_to(R).as_posix(),'exit_code':p.returncode,'seconds':round(time.monotonic()-t,3)})
  print(json.dumps(rows[-1]),flush=True)
  if p.returncode:break
after=identity();report={'candidate':'V16.1 bounded render diagnostics and surface contrast','started_utc':start,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'result':'PASS' if len(rows)==len(commands) and all(x['exit_code']==0 for x in rows) and before==after else 'FAIL','runtime_unchanged_during_gate':before==after,'commands':rows,'runtime_hashes':after,'scope':'Source/model/actual-GLB/scene-graph/build identity only. No GPU/human/audio-listening claim.'}
(D/'final_gate_receipt.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='runtime_hashes'},indent=2));raise SystemExit(0 if report['result']=='PASS' else 1)
