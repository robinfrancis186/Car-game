# Kerala Roadster — two-driver network alpha

**Experimental Canvas 2D diagnostic, not integrated multiplayer for the V10/V11 3D game.** This isolated `multiplayer-public-alpha` branch has a Node-authoritative, private two-driver room and manual browser/CLI clients. The `main` branch retains the original V10 game unchanged.

Cars use equal stock physics: no car-to-car contact, traffic, flight, upgrades, accounts, coins, purchases or payouts. Manual clients contain no bots/ghosts; test automation is explicitly separate. Rooms and results are in memory only.

## Run locally

Node **22+** is required (tested with 24.19.0). The only pinned runtime dependency is `ws` 8.22.0. No credentials are needed.

```sh
git clone --branch multiplayer-public-alpha --single-branch https://github.com/robinfrancis186/Car-game.git
cd Car-game
npm ci --ignore-scripts --omit=dev
npm test
npm run test:regression
npm start
```

Open **http://127.0.0.1:8787** in separate browser profiles. Create a room, share only the invite code, join, mark both players Ready, then Start as host. **WASD/arrows** drive; **Space** brakes; **Shift** boosts; **R** recovers with a five-second penalty. The diagnostic displays server snapshots without local prediction/interpolation. Separate profiles/devices keep reconnect credentials independent.

Default mode binds only to loopback. **Do not tunnel local mode.**

Manual CLI:

```sh
npm run client -- --name DriverA
npm run client -- --name DriverB --join PRIVATE_INVITE_FROM_A
# For an approved deployed server, append --url https://<actual-service>.onrender.com
```

CLI commands persist until changed; `brake` stops input. Keep room invitations private. Reconnect bearer tokens are not printed or placed in URLs; browser reconnect state stays in tab session storage.

## Optional public experiment

See [docs/HOSTING.md](docs/HOSTING.md). `render.yaml` is a passive **Free / Singapore / one-instance / manual-deploy** configuration, with no database. Committing it does not create a service or enable deployment. Verify workspace billing/overage conditions before provisioning; a free instance alone is not a guarantee of zero charges.

Public mode is opt-in and accepts only its exact Render HTTPS origin. It allows **one room, two seats, six open WebSockets and 40 TCP connections**, with bounded message/HTTP/control-frame quotas, 2 KiB messages, schema/version checks and reconnect-token rotation. Origin checks are not authentication; a non-browser client can forge them. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

The Free service can sleep, take time to wake, restart and lose all rooms/results. No uptime, persistence or production DDoS guarantee is made. No keep-awake traffic, paid service or automatic deployment is included.

## Verification and source

Local verification passed **15 security/network/world tests** and **128 unchanged V10 gameplay regressions**. These tests do not establish a live public deployment, internet latency, real human/device play, mobile/GPU performance or 3D integration. See [docs/TESTING.md](docs/TESTING.md).

- `server/`: authority, lifecycle and ingress guards.
- `client/`: manual Canvas browser and CLI clients.
- `shared/`, `data/`: frozen V10-derived headless physics/world data and authored water triangles.
- `test/`, `tools/`: automated checks, optional source-water parity tools and a labeled remote smoke harness.
- `SOURCE_FREEZE.json`: public-source hashes and upstream reviewed-freeze identity.

Runtime, clients, data, tests and deployment configuration are byte-identical to the reviewed public-alpha freeze. Public documentation is sanitized; internal reports/logs, reference media, credentials and dependency caches are omitted. Test-generated reports remain local and ignored.

## Attribution and rights

© OpenStreetMap contributors. Coastal map data is available under [ODbL](https://www.openstreetmap.org/copyright) in `data/coastal_map_data.json` and via `/map-data`; preserve this database offer. Original project code has no new blanket open-source license (`UNLICENSED`). `ws` is MIT-licensed; see [LICENSES.md](LICENSES.md) and [docs/WS-LICENSE.txt](docs/WS-LICENSE.txt).
