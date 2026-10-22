# MALABAR — Hot Coast / Highland Run

An original Blender-built, Three.js **arcade racing prototype** with two selectable Kerala-inspired courses, two concept-inspired cars, Sprint / Pursuit / Time Attack races, free Explore, fictional flight, upgrades and synthesized audio.

**[Play the game](https://malabar-hot-coast.robin186x.chatgpt.site)**

This repository contains the frozen **V10 / 0.10.0** game source and original editable asset sources. It is a stylized prototype, not an AAA release, an exact geographic reconstruction or a manufacturer engineering simulation. No Tesla, transit-operator or other brand endorsement is implied.

## Run locally

Requirements: a modern WebGL2 browser; Python 3 for the simple local server; Node.js 20+ and npm for rebuilding/tests. Blender is **not** required to play.

```sh
git clone https://github.com/robinfrancis186/Car-game.git
cd Car-game/web
npm ci
npm run serve
```

Open **http://localhost:8080**. `npm run serve` binds only to your computer. The game has no server, login, paid currency, analytics integration or network API dependency. Workshop credits/preferences are stored in your browser; no real purchases exist.

### Build a self-contained playable HTML file

```sh
cd web  # from the repository root
npm ci
npm run build
```

Open the generated `dist/malabar-hot-coast.html` in a desktop browser, or serve it over HTTP/HTTPS. The file embeds code, both tracks, models and font. iOS file-preview apps may not execute HTML; use an HTTP/HTTPS server instead. Generated bundles and dependency caches are deliberately not committed.

### Test

```sh
cd web
npm test
```

See [TESTING.md](TESTING.md) for coverage and evidence boundaries. These deterministic tests do **not** establish real GPU rendering, human handling quality, mobile hardware performance or audible sound quality.

## Play

- Select **HOT COAST** (coastal villages, metro, canal garden, flyover, harbor) or **HIGHLAND RUN** (divided highway, tea bends, switchbacks, bird-rock ridge).
- **EXPLORE** starts in a selected district, without a clock, opponents, police or mandatory gates. Recovery is free. Races require gates in order and apply damage/recovery rules.
- **W/S** accelerate / brake into reverse; **A/D** steer; **Space** brake; **Shift** boost; **B** ultra burst; **F** fictional flight; **Q/E** lower / raise flight target; **X** controlled kickflip; **C** camera; **L** inspect an Explore landmark while parked; **R** recover; **Escape** pause. Drag to orbit the chase camera. Touch controls are provided; landscape is recommended.
- Workshop upgrades change speed, acceleration, grip and boost efficiency independently for each car. Credits are fictional and local to the browser.

## Repository layout

| Directory | Contents |
| --- | --- |
| `web/src/`, `web/index.html` | Game, UI, physics and synthesized audio source |
| `web/public/assets/` | Frozen runtime GLB geometry, route/collision data and font |
| `web/public/vendor/` | Pinned Three.js runtime modules and license |
| `web/tests/` | Portable automated model/controller/scene-contract tests |
| `blender/` | Original procedural generators, exporters and asset validators |
| `assets/` | **24 editable native `.blend` files**, source plans/manifests and authoring data |
| `references/route/` | Attributed OSM source/derived geographic database |
| `unreal/` | Optional earlier Unreal source scaffold; **not compiled or shipped as a game** |
| `tools/` | Authoring utilities; not required for the browser game |

See [AUTHORING.md](AUTHORING.md) for editable Blender files and regeneration notes; [PROVENANCE.md](PROVENANCE.md) and [LICENSES.md](LICENSES.md) for attribution and rights.

## Version and limitations

`SOURCE_MANIFEST.json` records the exact frozen runtime hashes. Native Blender files were losslessly saved with Blender's built-in compression and relative preview-output paths; reopening verified unchanged mesh geometry. `ASSET_SOURCE_MANIFEST.json` records their original/published hashes and geometry fingerprints. Source generators remain editable; small reference-filename metadata was removed before public publication.

V10 automated source, model and scene-contract checks pass. Full V10 WebGL/human-driving acceptance, a real iOS hardware pass and sound-listening review remain separate checks. Prior-version FPS observations are not V10 performance guarantees. Art/collision proxies remain simplified; most boats are static props; visual flight/water/foliage effects are arcade approximations.

No user reference photos/videos, private notes, hosting configuration, credentials, cached dependencies, Blender backup files or historical debug reports are included.
