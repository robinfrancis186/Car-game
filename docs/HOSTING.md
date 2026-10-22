# Optional Free Render Singapore deployment

This branch is prepared for a bounded experiment; this document is **not a deployment receipt**. Creating a service is a separate operation. Confirm that the selected workspace has no payment method, or an enforceable zero-charge guard for applicable overages, before provisioning. Stop if a card, paid plan, additional permissions or new terms are required. Do not create API keys for this app.

## Configuration

- Repository: `https://github.com/robinfrancis186/Car-game`
- Branch: `multiplayer-public-alpha`; server source is at the branch root. Pin and verify the reviewed commit.
- Runtime: Node; region: **Singapore**; instance plan: **Free**; one instance.
- Build: `npm ci --omit=dev --ignore-scripts`
- Start: `npm start`
- Environment: `NODE_ENV=production`, `NODE_VERSION=24.19.0`, `PUBLIC_ALPHA=true`.
- Let Render supply `PORT`, `RENDER`, and `RENDER_EXTERNAL_HOSTNAME`; do not override them.
- Automatic deployment: **off** (`autoDeployTrigger: 'off'`). No disk, database, cron, custom domain or external-game origin.
- Health route: `/health`. Verify its actual public HTTPS response after deployment.

Public mode fails closed unless Render's hostname/environment and a valid port are present. It binds `0.0.0.0:$PORT`; local mode stays loopback-only. Render terminates HTTPS/WSS at its edge; the Node listener internally uses HTTP. Only the exact generated Render origin is permitted. Origin filtering is not account authentication.

`render.yaml` supplies configuration only. Do not modify `main`, enable an auto-deploy hook or upgrade compute as a side effect of publishing this branch.

## Bounded acceptance

Verify actual returned plan, region, repository, branch and deployment commit. After it becomes live, verify HTTPS `/health` and `/manifest`, invalid-Origin rejection, then run:

```sh
node tools/remote-smoke.mjs https://<actual-service>.onrender.com
```

The approximately two-minute smoke test uses two independently connected **automated CLI processes**, checks shared movement/start/results and reconnect rotation, and writes a scope-labeled local receipt. It is not human/device/browser/3D acceptance. Do not publish token-bearing logs or imply that local tests prove internet behavior.

Free instances can sleep after inactivity, wake slowly, restart, and lose every in-memory room/result. No keep-alive traffic or uptime promise. Check current provider terms before provisioning: [Free limits](https://render.com/docs/free), [web services](https://render.com/docs/web-services), [regions](https://render.com/docs/regions), [environment values](https://render.com/docs/environment-variables), and [Blueprint configuration](https://render.com/docs/blueprint-spec).
