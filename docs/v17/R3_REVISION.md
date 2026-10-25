# R3 revision: rejected V16.1 screenshot → coherent unpublished candidate

## Evidence and identity
The user screenshot is the expected V16.1 portrait UI, not a stale deployment. The exact V16.1 durable archive and fresh Vercel runtime hashes match its 143-file release tree `1c91402ff7fe7077df3718f0ebc78087c79c851835664c94fdecac98d2a8cc82`. The old Home exposes a Play/Garage/Map/Shop/Story/Workshop stack plus a duplicate Home/Garage/Play/Shop dock. Its original loft has pale daylight material response.

The latest Workshop/Shop and earlier Home/Run Ended reference pixels were inspected again on 2026-10-23. Their strongest shared visual signal is a dark charcoal, steel and cedar coastal interior against low warm sunset light, with glossy floor/car reflections, restrained orange accents and compact icon/text controls.

## Intentional reference adaptation
The landscape reference itself has duplicated Home navigation. The revised user feedback and parent task explicitly call for removing that duplication, so R3 uses one Home action hierarchy and reserves the dock for internal screens. Mobile uses intrinsic grid tracks rather than reducing the desktop screenshot to an unreadable scale.

## Functional boundaries
- Main navigation is semantically hidden on Home; IDs and existing internal navigation handlers remain intact.
- Caption, original interactive car fit region and Home actions occupy separate portrait grid rows.
- Real saved coins, ownership, prices and upgrade effects remain authoritative; reference mock values are never new defaults.
- No private reference image or crop becomes a runtime asset.
- All 138 byte-protected V16 files remain a required preservation gate.
- Menu scene/environment changes must restore the original racing state on leaving Home/garage.
- Offline original Blender proof is not an actual WebGL screenshot and must never be labeled as one.

## Publication and review
No publication is part of this revision. The denied R2 Sites37 publication has not been retried. The new source, tests, screenshots (if supported) and full backup must be reviewed before any subsequent release decision. Root `design-qa.md` is authoritative for the current gate and known gaps.
