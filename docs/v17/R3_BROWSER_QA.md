# V17 R3 actual cloud-browser QA — changes required

**Home improvement verified at all four sizes:** no duplicate dock, no car-caption/action overlap, every visible Home control at least 44×44, no body overflow. Sixteen screenshots captured and inspected; all four main screens at 1440×722, 390×844, 844×390, 320×568.

**Concrete target-size defects:** Shop native sort select36px high at all sizes; short-landscape Workshop/Shop audio, settings, help, back buttons36×36; short-landscape Shop ALL filter37.56×44. The built-in77-case bounds audit passed all four sizes but did not cover these real elements. Independent measurements override that incomplete green result.

Filters, top-speed sort, owned-car cycling, Home/Workshop/Shop/results navigation, keyboard focus outline and internal scrolling worked in synthetic CSS review. No real saves/economy touched. Original frozen145-file runtime remains exact.

**Not final visual acceptance:** this CSS harness shows original-model stills, not actual3D. Actual R3 game root reaches Graphics unavailable, with GL_VENDOR/GL_RENDERER Disabled. No native FPS, garage360 or actual-pavilion approval. Shop imagery remains below photoreal scenic-reference target. Original offline Blender proof is separate partial evidence, not gameplay.

R3 remains separate review only. R3.1 target-size patch may be prepared separately; no frozen edits/promotion.

See R3_BROWSER_QA.json, per-screen DOM receipts,308-case bounds receipts, filter/sort/navigation receipts,20JPEG screenshots, and roundtrip-verified Library screenshot receipt.
