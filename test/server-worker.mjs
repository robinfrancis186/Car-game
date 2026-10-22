import {createService} from '../server/service.mjs';
const app=await createService({raceSlice:{startS:2200,endS:2320},countdownTicks:12,reconnectMs:1000,raceLimitTicks:60*20,resultRetentionMs:30000});
process.send({type:'server-ready',port:app.port,pid:process.pid});
process.on('message',async m=>{if(m.type==='stop'){await app.close();process.exit(0);}});
