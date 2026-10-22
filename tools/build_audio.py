"""Original synthesized placeholder coastal/motor audio, no sampled recordings."""
import math,random,wave,struct
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]/'assets/audio';OUT.mkdir(parents=True,exist_ok=True)
rate=22050
for name,duration in [('EV_Loop',4),('Coastal_Ambience',12)]:
 random.seed(2026);samples=[];low=0
 for i in range(rate*duration):
  t=i/rate
  if name=='EV_Loop':v=.15*math.sin(2*math.pi*110*t)+.07*math.sin(2*math.pi*220*t)+.025*math.sin(2*math.pi*440*t)
  else:
   low=.94*low+.06*random.uniform(-1,1);v=low*(.6+.25*math.sin(2*math.pi*t/duration))
  samples.append(v)
 # Raised cosine crossfade gives loop endpoints silence, without discontinuity clicks.
 for i in range(int(rate*.08)):
  f=(1-math.cos(math.pi*i/(rate*.08)))/2;samples[i]*=f;samples[-1-i]*=f
 with wave.open(str(OUT/(name+'.wav')),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(b''.join(struct.pack('<h',int(max(-1,min(1,x))*32767)) for x in samples))
print('Original synthesized PCM audio written')
