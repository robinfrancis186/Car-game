# V17 R3.5 — one showroom Home

Candidate based on Git main `f8bd64714682a658a86d80119a8050c52b250818` (R3.4).
Publication and native acceptance are separate from implementation.

## Requested flow correction

The separate outdoor Events/setup page is retired, not merely restyled. The golden showroom Home retains its existing visual theme, car carousel and main action composition. A compact, expandable course/mode drawer lives above the existing orange **Play**. This is the only quick-race launch button; it launches the selected mode directly.

- Hot Coast/Highland Run and Sprint/Pursuit/Time Attack/Explore remain available.
- Map selects Explore and opens its district choices without starting a session.
- Setup navigation returns to the same showroom and opens the drawer, not another full-screen menu.
- Garage, Shop, Workshop, Story, Help and the device-local leaderboard remain available.
- Per-course known Explore starts and validated mode selections survive course reloads through URL parameters. No race starts automatically on reload, and no new save-data store is introduced.
- Repeated Play clicks cannot restart a live run; held Enter cannot launch again after returning Home. Native summary/select controls retain normal keyboard behavior.
- Drawer changes refresh the portrait showroom fitting bounds. The drawer scrolls within its own bounded area; Play remains outside that scroller.
- Old Events panel, tabs, vehicle picker and second Start Race control are removed from runtime markup. Existing preview `view=events` is only an alias to the expanded Home drawer.

## Preservation and validation scope

No physics, route geometry, models, textures, Blender sources, coin rules, profile/Story/leaderboard storage modules or licenses are changed. Existing R3.4 HUD containment, dock insets and graphics-interruption protections are retained.

`npm test` now includes the unified-Home controller regression stage. Automated controller/scene tests use DOM/renderer/audio stand-ins where documented; they are not native browser or GPU proof. The final candidate receipt records exact full-suite/build results and native-review status independently. Historical R3.4 publication manifests identify the baseline and do not claim this candidate is published.
