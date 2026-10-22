import {createService} from './service.mjs';
import {renderOptions} from './ingress.mjs';
const options=renderOptions();
const app=await createService(options);
console.log(`Kerala Roadster ${options.publicOrigin?'PUBLIC EXPERIMENTAL':'LOCAL'} ALPHA ready on port ${app.port}; 2 stock cars, no contact, no accounts or payouts`);
let stopping=false;
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,async()=>{if(stopping)return;stopping=true;await app.close();process.exit(0);});
