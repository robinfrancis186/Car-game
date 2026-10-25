# R3 rendered CSS review against supplied targets

Evidence: actual supported cloud-browser JPEGs under `tests/v17/r3-browser-evidence/`, exact R3 public review bytes anchored by `R3_BROWSER_QA.json`. Inputs: previously inspected private Home, Shop, Workshop and Run Ended reference images; originals and crops are excluded. This evaluates R3 only ; R3.1 has not yet been rendered.

## What is now demonstrably closer
- **Home:** white condensed italic MALABAR wordmark, orange primary Play, two secondary Garage/Map cards and three compact shortcuts. Desktop keeps actions left/car caption right. Portrait/compact use a single hierarchy; the old duplicated Home/Garage/Play/Shop bottom dock is absent. Actual 320×568 has 6px between caption and action grid, 390×844 has 8px. No overlap/body overflow in any requested size.
- **Workshop:** dark slate interface, outlined active Inspect tab, owned-car summary and five performance rows; desktop left controls/right original-car still. Mobile uses its own car area plus scrollable upgrade panel above the internal navigation dock.
- **Shop:** five paid original cars, three desktop columns/two short-landscape columns/one portrait column; lock badges, real catalog prices, performance bars, Inspect presentation, filter and sort states. Original car renders are legible; no uploaded reference crop is used.
- **Run ended:** centered narrow dark panel, orange/white title, large time, paired rewards, outlined total and orange Retry. All actions fit portrait; short landscape provides a working scroll area and visible keyboard focus.

## Why this is not an exact match
- Static preview uses a flat slate-gradient field and transparent original-car stills. It does not render the coastal pavilion, glass, timber, ocean, palms, warm reflected lighting, or any actual 360 view. Its blank stage is not the intended final 3D background and must not be passed off as finished scenery.
- Shop cards still lack the supplied reference's photographic coastal backgrounds. Replacing them with crops of private references is not an acceptable solution.
- Existing game cars are stylized; body/material/foliage/water fidelity differs materially from the photographed reference aesthetic. The separately labeled original Blender pavilion proof shows partial improvement, not exactness and not actual WebGL.
- Tiny secondary labels, spacing and car scale differ from the supplied desktop mocks; mobile is a responsive adaptation rather than a literal scaling of those landscape images.
- Concrete R3 hit-target defects remain in the deployed review. R3.1 addresses only these and needs its own actual browser evidence.

Verdict: **substantial navigation/layout correction is evidenced; exact reference/3D/native acceptance remains blocked.** No production promotion is justified by these CSS screenshots alone.
