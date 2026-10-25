> Historical R1/R2 record retained for provenance. It is not current R3 acceptance evidence. See the root `design-qa.md` and `STATUS.md` for R3 status; supported cloud CUA later became available, but WebGL remains disabled. Do not rerun the historically denied custom Chromium launch.

# V17 reference UI source/controller QA

## Evidence level

`web/tests/v17-reference-ui.test.mjs` bundles the actual current `main.js` with real gameplay/catalog/storage modules and a synthetic DOM/renderer. Its harness is copied from the existing controller test; the original was not modified. It verifies controller state and semantics, not layout, screenshots, WebGL, visual fidelity, audio listening or native FPS.

Run:

```sh
cd web
node tests/v17-reference-ui.test.mjs
```

## Passing checks

- A fixture with **580 coins** retains that actual balance. Crimson speed level 1 costs 600, so the button is disabled, says **20 MORE COINS**, and cannot debit or upgrade even if its handler is invoked directly.
- Home next/previous wraps only through owned cars, persists legitimate selection, and does not spend coins. A separately fully owned fixture cycles all seven cars.
- Settings and Home menu open Help without mutating profile or underlying screen. Closing Help restores it.
- Shop initially lists five locked cars. All/Coupe/Hypercar/Classic/Drift filters use explicit presentation taxonomy; displayed prices and speed values come from the real catalog/modifiers.
- Default, ascending-price and descending-speed sorts expose the expected visual order and matching DOM order for keyboard/screen-reader traversal. The harness implements real append/move semantics and checks that reordering never duplicates cards.
- Inspecting every locked car changes only the preview, never ownership, balance or selected race car.
- Empty filtered Owned collection recovers with All; fully owned Shop reports a complete collection.
- HTML and generated controller IDs are unique. Navigation keeps text labels with decorative SVG icons.
- Source contains portrait and compact-landscape reflow, scrolling panels and no URLs to the private reference originals.

Log: `tests/v17/reference-ui-controller.log`.

## Source cascade review

All identified source cascade issues are now resolved in source (not yet rendered):

1. **Fixed:** Compact portrait Home caption is at 54%; V17 explicitly resets inherited Home action padding to zero.
2. **Fixed:** Ineffective nested view selector replaced by direct `.garage-view` selector.
3. **Fixed:** Inherited Home `top`, garage orbit `height`, wallet `left` and landscape name hiding are explicitly overridden.
4. **Fixed:** Portrait Play wallet has an explicit `top:16px; right:calc(16px + 132px)` header override, clear of the event content beginning at 84px.
5. **Fixed:** Collection sorts now reorder the real DOM via `root.append(...)`, in addition to CSS order; synthetic move-semantics tests prove both sequences agree and no cards are duplicated.

These observations are source-derived and do not replace the required four-size rendered review. The four-size rendered acceptance gate remains blocked by the execution environment described in BROWSER_QA_STATUS.md.

## Protected scope

`tests/v17/preservation.test.mjs` passes all 138 byte-protected modules/assets. At the latest source test, 139 of 143 old V16.1 runtime files were unchanged; only index.html, main.js, scene.js and style.css changed. The four exact private reference-original hashes are absent from runtime. Archive exclusion and derivative/privacy review remain separate checks.
