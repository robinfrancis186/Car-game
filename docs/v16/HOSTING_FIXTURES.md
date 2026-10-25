# Exact isolated hosting gate

Use `tests/v16/hosting_fixtures.json` to copy the small non-public fixture set before `cd web && npm test`. The three staged course GLBs must equal their public copies; they are inputs to the independent art validator, not additional hosted URLs. Create the listed output directories. `npm test` generates the ignored car-projection report before building the UI preview, so a stale projection snapshot is unnecessary.

Do not copy `references`, user photos/video, hosting credentials/receipts, or private backup manifests into the public site. Runtime is the exact `web/index.html`, `web/src`, `web/public` tree captured in `tests/release/V16_RELEASE.json`. Standard split hosting is required because the standalone exceeds the static per-file limit. Preserve prior historical review routes. Build uses pinned existing dependencies; no external asset/CDN request is introduced.

New optional route: `?track=surface-test`. Default normal routes stay unchanged. The named static UI preview `v16-ui-preview.html` contains normal-route UI only, with a disabled explanatory solo-test button: it is not a rendered wall-driving demonstration.
