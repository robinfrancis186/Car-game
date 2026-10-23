/** Version-pinned race rule. No client can request or extend a host interruption. */
export const TIMING_POLICY=Object.freeze({serverInterruption:'bounded-v1',stallDetectMs:250,resyncStableMs:500,maxInterruptionMs:2000,maxInterruptions:3,maxInterruptedMs:5000});
