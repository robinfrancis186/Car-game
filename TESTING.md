# Testing

From `web/`, run `npm ci && npm test` with Node.js 20+.

The test chain covers deterministic fixed-step driving/collision/recovery and race gates; both track catalogues; exported GLB scene/rig/camera contracts; both world loaders; audio controls/lifecycle; transit animation; actual game-controller wiring for both tracks; local garage upgrades/ultra boost; detail/LOD budgets; visual-effect state; and UI-controller behavior.

Physics fixtures drive actual routes with bounded inputs. Model metrics are regenerated locally by the tests. Passing fixtures do not guarantee a human will win races or that every untested visual condition is correct. Renderer/DOM/audio stubs are used by portions of the suite: it is not a real GPU, hardware, listening or full end-to-end browser acceptance test.

`npm run build` must also succeed and produces `dist/malabar-hot-coast.html`. Open the game on an actual WebGL2 device, check both tracks/cars, start/finish all modes, drive flyover/highland grade transitions, inspect landmarks, test pause/recovery, audio unlock/mute, and touch layout. V10 GPU/human-driving acceptance and real iOS/listening checks are not claimed by this source upload.

Optional independent C++ driving-model check (the old Unreal scaffold, not the browser physics):

```sh
c++ -std=c++17 tests/test_drive_model.cpp -o /tmp/malabar-drive-test
/tmp/malabar-drive-test
```

Native asset geometry fingerprints were checked after reopening every published `.blend` with Blender 4.3.2. Audit found no packed reference photographs, linked external libraries or embedded scripts in those 24 native source files.
