> Historical R1/R2 record retained for provenance. It is not current R3 acceptance evidence. See the root `design-qa.md` and `STATUS.md` for R3 status; supported cloud CUA later became available, but WebGL remains disabled. Do not rerun the historically denied custom Chromium launch.

# V17 cloud rendered QA

The flow under test is: Home → Workshop/Shop → actual car/upgrade interactions → real-model failed-run result → Home, at 1440×722, 390×844, 844×390, 320×568.

## Current environment blocker

2026-10-23: Browser plugin skill is listed but required associated Browser-app `js` tool is absent. Available CUA controls the user's computer and is out of this cloud-only task. The explicit task permits cloud Playwright; installed Chromium is `/usr/bin/chromium`.

Default cloud launch failed before game navigation:

`chrome/browser/process_singleton_posix.cc:297 socket() failed: Operation not permitted (1)`

A supported `require_escalated` retry failed in the execution wrapper:

`bwrap: Can't create file at /home/agent/.codex/sessions: Read-only file system`

No reads/access requests to that policy-denied path were made. No workaround or bypass was attempted. This is an execution-environment blocker, not evidence of a game error. **No rendered screenshot, WebGL acceptance or native FPS claim is currently valid.**

## Ready-to-run harness

`tests/v17/browser-qa.mjs` uses actual `web/index.html`, JavaScript controller, scene and WebGL2 runtime; it does not use static UI-preview HTML, a stub renderer or a screenshot overlay.

Start the local-only HTTP server:

```sh
cd web
python3 -m http.server 8170 --bind 127.0.0.1
```

Then run from the project root in a cloud executor that permits Chromium:

```sh
node tests/v17/browser-qa.mjs --url=http://127.0.0.1:8170/ --output=/tmp/malabar-v17-browser-qa
# Optional single viewport:
node tests/v17/browser-qa.mjs --size=1440x722
```

Each viewport gets a fresh isolated browser context with a synthetic 580-coin Crimson profile. No user browser, Mac save or live website is touched. Functional checks spend 300 fixture coins on braking, verify 280 remain and persist after reload, orbit the actual car, inspect all five locked cars, and verify failure pays zero. Result capture deterministically calls the real model's `_end('failed', ...)` with 48.33s; that is explicit state-fixture testing, **not** human driving completion. All current upgrade prices/stat values come from real code rather than screenshot mock numbers.

Screenshots/JSON go outside the repository into `/tmp`. A successful harness pass still requires actual screenshot/reference inspection and a recorded mismatch ledger; software SwiftShader timing is not native performance acceptance.


## R2 hosted CSS review update — 2026-10-23
Supported existing cloud-browser `cua cdp` reviewed the isolated Sites 36 static artifact at all four required CSS viewport sizes. No denied custom Chromium launch was retried. 16 primary-screen screenshots were inspected; all four original77-case bounds audits passed, but visual review caught the320×568 Home caption overlapping Play. R2 corrects only that compact placement and adds explicit overlap regression checks. See docs/v17/RENDERED_CSS_REVIEW_R2.md. Real WebGL/pavilion/native-device/FPS acceptance remains open; full game publication remains held.
