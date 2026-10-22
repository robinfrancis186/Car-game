# Malabar Hot Coast — sound design

## Runtime implementation

`src/audio.js` is an original, sample-free Web Audio synthesizer. It makes no
network requests and contains no Tesla recordings, commercial music, or
third-party audio clips. Its EV and thruster sounds are designed for this arcade
game; they are not measured or verified reproductions of a production Roadster.

The mix uses these separate layers:

| Layer | Driving input / treatment |
| --- | --- |
| EV drive | Fundamental, harmonic and inverter-like whine; smoothly follows speed and throttle load, quieter in flight |
| Tires | Filtered rolling noise, rougher off-road texture, steering/braking-dependent friction and skid tone; silent friction when airborne |
| Air | Speed-dependent wind with a filtered, stereo noise bed |
| Coast | Slowly changing surf and foam, plus very quiet occasional synthetic bird-like calls at low speed |
| Regular boost | A restrained rushing layer; suppressed rather than stacked when ultra is active |
| Ultra boost | A short rising electrical/pressure activation cue, then separate air, low-body and turbine-like layers; release fades smoothly |
| Thrusters | Low thruster body and high-pressure hiss, with short attack and release |
| Police | Two-layer wail, nearest active unit, distance attenuation, stereo direction and bounded Doppler |
| Impacts / landings | Filtered contact crack, low thud and brief bodywork partials for severe contact; loudness follows real simulation impulse / mass and closing speed, with event-ID deduplication |
| Race cues | Short original tones for countdown, go, checkpoint, finish/escape and failure |

All continuous parameters use smoothing. A master fade removes clicks on mute,
menu and pause. Native `DynamicsCompressorNode` provides additional peak control;
the intended mix already has conservative headroom before compression. One-shot
voices are capped at 12 and disconnect after ending. Noise loops are seeded and
their endpoints are joined. No artificial combustion RPM or gear-shift audio is
used for the EV.

## Integration contract

```js
import { GameAudio } from './audio.js';
const audio = new GameAudio();

// Call in Start, Resume or unmute click/touch/keyboard handlers, not on page load.
await audio.resume();
audio.enabled = true;

// Run every animation frame, including menu/pause, so fades and state stay current.
audio.update(model, elapsedSeconds, { menu, paused, input, dt });

// At application teardown:
audio.dispose();
```

Also call `update()` synchronously when pausing on `blur` / `visibilitychange`.
A hidden tab may stop animation frames before its next frame; scheduling the
master fade in the event handler prevents audio continuing in the background.

`input.throttle` is signed and `input.brake` is Boolean. Positions/speed are in
metres / metres per second. Player heading is radians, with +X forward and +Z
to the driver's right at heading zero. Police units may set `active:false` or
`siren:false`; `model.wanted` must be positive for pursuit audio. Events have
monotonically increasing `id` and a `type`; contact and landing may include
`intensity` in the range 0–1. A new model or a new countdown resets deduplication.
Muted and paused events are consumed rather than played later.

V10 uses `player.ultraBoosting` separately from `player.boosting` and accepts the
`ultra-start` event. A rising-edge fallback supports older controllers, with
same-frame deduplication so the activation cue plays only once. Starting ultra
while muted or paused does not queue a cue for resume. `ultra-ended` is represented
by the sustained mix fading out; rejected `ultra-unavailable` requests produce no
misleading activation sound.

For physical contacts, `impulse` is in N·s, `player.mass` is kg and `closingSpeed`
is m/s. The bounded perceptual mapping uses impulse / mass (felt velocity change)
plus closing speed. `intensity` is only a fallback for contacts without those
measurements, such as some overhead collisions. Landings use `verticalSpeed`
when present. This is game sound design, not a calibrated crash-acoustics model.
Recovery / roadside-assist teleports do not create fake landing thuds.

Audio unlock failure is nonfatal. `audio.diagnostics` exposes availability,
context state, gesture-unlock status, enabled/active state, voice count and mix
targets. Missing Web Audio support leaves the game playable without sound.
`dispose()` is idempotent and does not close an externally injected context.

## Verification performed

`node tests/audio.test.mjs` passes 30 deterministic control / integration tests: unavailable
API, unlock, mute/pause/menu, siren attenuation/pan/reset, grounded skid,
event deduplication, muted-event discard, restart/countdown, bounded voices,
landing deduplication, recovery versus landing, reverse drive load, unlock retry,
finite parameters, deterministic seamless stereo noise and cleanup. V10 adds
regular/ultra separation, activation-event/rising-edge deduplication, silent
activation discard, sustained release, actual impulse scaling, mixed burst
limits, terminal-state suppression, explicit lost-ground-contact handling and
same-model Explore restart without a countdown. Restart disconnects old cue tails.
Three tests use the actual V10 `GameModel` to verify its ultra activation/expiry,
pause/recovery/restart and real capsule-contact impulse reaching the audio module.
These tests use a stub context, so they do not establish audible quality.

The actual synthesis module is also rendered through the MIT-licensed
`web-audio-engine` 0.13.4 test tool into
`../assets/audio/malabar_v10_ultra_crash_NOT_GAMEPLAY.wav`. The adjacent
`v10_audio_signal_validation.json` contains measured levels, segment metrics and
the exact audio source SHA-256.
This is a **software-rendered sound-design demonstration, not gameplay capture**.
The software engine does not implement `DynamicsCompressorNode`; it passes that
node through. Its metrics therefore check pre-compressor headroom, not native
browser compression. The demonstration is not loaded by the game and does not
increase the game download.

To reproduce this optional render (the package is a test-only dependency):

```sh
npm install --prefix /tmp/kerala-audio-tools web-audio-engine@0.13.4 \
  --ignore-scripts --no-audit --no-fund --cache /tmp/kerala-npm-cache
node tests/render-audio-demo.mjs
```

Set `AUDIO_ENGINE` to an alternative absolute package path if needed.

### Demonstration timeline

| Seconds | Segment |
| --- | --- |
| 0–1.5 | Menu silence |
| 1.5–4.5 | Countdown |
| 4.5–8 | EV acceleration |
| 8–11 | Regular boost at a fixed speed/load |
| 11–14 | Ultra activation and sustain at the same speed/load |
| 14–16 | Braking, skid and rough surface |
| 16–19 | Low, medium, then high physical-impulse contacts |
| 19–22 | Police siren crossing the stereo field |
| 22–25 | Thruster flight |
| 25–26 | Landing |
| 26–28 | Pause fade and silence |
| 28–30 | Muted ultra activation: deliberately silent |
| 30–32 | Resume ultra sustain without replaying activation |
| 32–34 | Coast |
| 34–37 | Conservative stress case: ultra, thrust, skid, close siren and repeated hard contacts together |
| 37–39 | Final pause fade and silence |

The stress case deliberately combines states more aggressively than normal
gameplay. Signal assertions require zero nonfinite / clipped samples, bounded
voices, silence after pause/mute fades, a distinct stronger ultra sustain and a
stronger transient for higher physical impulse. The latest measured values are
in the JSON, rather than an unverified claim about how pleasant it sounds.

### Browser / listening checks still required

- A fresh browser must stay silent before a start gesture; Start must unlock
  sound without an uncaught error. Repeat on iOS Safari hardware.
- Mute, pause, tab-background pause, resume, restart and return to menu must not
  leave a siren or thruster sounding. Check repeated rapid transitions.
- In pursuit, distance and left/right direction should be perceptible without
  masking steering/skid feedback. No-police scenarios must have no siren.
- Assess comfort, tonal balance, transients and fatigue with actual headphones
  and phone speakers, then adjust levels if necessary.
- Check native browser compressor output and audio CPU use during a full race.

No auditory listening review or device-specific performance result is implied
by the numerical tests above.

## Technical references

- [MDN: AudioContext.resume](https://developer.mozilla.org/en-US/docs/Web/API/AudioContext/resume)
- [MDN: DynamicsCompressorNode](https://developer.mozilla.org/en-US/docs/Web/API/DynamicsCompressorNode)
- [web-audio-engine source and rendering API](https://github.com/mohayonao/web-audio-engine)

The test engine is not bundled in the browser build. Its MIT package license is
preserved in the test installation; all runtime audio synthesis in `src/audio.js`
was authored for this project.
