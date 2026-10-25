# V14 interface redesign: bounded brief

## User goal and protected behavior
A coherent, restrained racing interface across every screen—not a home-only cosmetic patch. Preserve the real 3D car/world, every driving control, owned cars, coins, upgrades, save migration, chapter progress, audio and camera behavior. Live V13 remains untouched. A small implementation/QA team is working; no claim of ten designers.

## Grounding and evidence
The user supplied an actual pause-screen photo (`current_user_screenshots/PRIVATE_REFERENCE_IMAGE`). Its oversized two-line slogan and long orange action compete with the actual pause task; decorative subtitle adds no useful state. This is direct user evidence. Fresh current-version cloud CSS captures will inventory all screens; native WebGL captures are a separate parent-owned window. Prior V13 bounds tests establish only fit/operation, not visual quality.

## Selected visual direction
- Keep MALABAR identity and existing car hero, but reserve display lettering for the brand. Use a readable system sans for controls, settings and explanatory text. Tabular numerals for timers/prices/stats.
- Scale hierarchy: restrained section headings, compact context, one primary action. No slogan headings, artificial urgency, wall-to-wall orange, giant arrows or decorative slash copy.
- Neutral charcoal/near-white palette; orange marks primary/selected actions, violet only retains Ultra meaning, red only danger/error. Selected and disabled states must also have text/border semantics, not color alone.
- Thin dividers and solid readable panel backings rather than nested translucent cards. Consistent radius, spacing, alignment, button height and focus treatment across menus/modals/garage.
- Pause: PAUSED, event/track context, Resume, Restart, Home. Results: actual outcome, position/time, finish/collected/total coins, Retry/Home and chapter continuation only when valid.
- Garage/shop: emphasize car and ownership/price; compact comparable stats and clearly linked purchase action, no fabricated catalogue. Preserve inspect orbit and upgrade meanings.
- HUD: prioritize road visibility and driving information; position/time/route/speed distinct from secondary car meters and special controls. Keep touch controls reachable without covering the central driving corridor.
- Help/settings: concise grouped sections; controls, graphics/motion/audio, save controls, credits. Destructive reset remains segregated and confirmed. Loading/error must plainly describe readiness or actionable failure.

## Acceptance
Every requested state has a fresh accepted screenshot or explicit blocker. Test desktop1180×757, portrait390×844 and320×568, landscape568×320; inspect actual rendering, overflow, focus, targets, practical copy and hierarchy. Preserve all protected source/assets by hash; review any main.js change for behavior. Run actual-main/controller/story/store/economy tests and complete gate before freeze. No screenshots of static previews are labeled gameplay; no blanket accessibility or realism claim.

## Brief primary comparison research (original design only)
- EA official NFS Unbound accessibility resource: https://www.ea.com/able/resources/need-for-speed-unbound — separates visual/audio/control/gameplay settings and describes HUD contrast and motion options. This supports clear grouping and readable controls, not copying its artwork or adding unsupported settings.
- Gran Turismo7 official manual: https://www.gran-turismo.com/gb/gt7/manual/drivingoption/02 — makes pre-race car settings a direct named action. Used only as a functional clarity comparison.
- Forza official accessibility-support page was attempted but redirected to an inaccessible URL; no design finding is attributed to unread page content.

Private user photos and third-party reference art stay outside public assets. Required OSM/Three/font notices remain intact.
